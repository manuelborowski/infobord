from flask import render_template, Blueprint, request
from flask_login import login_required, current_user

from app import admin_required, supervisor_required, data as dl, application as al
from app.presentation.view import fetch_return_error
from app.application import cron_table
import html
import json, sys

# logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

bp_settings = Blueprint('settings', __name__)

# Settings page access policy.  This drives both the generated template and the update guard.
setting_levels = {
    'generic-new-via-smartschool-default-level': 5,
    'generic-new-via-smartschool': 5,
    'cron-scheduler-template': 5,
    'cron-enable-modules': 5,
    'smartschool-message-title-at-home': 3,
    'smartschool-message-body-at-home': 3,
    'smartschool-message-title-to-home': 3,
    'smartschool-message-body-to-home': 3,
    'smartschool-message-additional-receivers': 3,
    'smartschool-message-sender': 3,
    'smartschool-message-enable-sending': 3,
    'user-datatables-template': 5,
    'school-configuration': 5,
    'field-configuration': 5,
}

def _current_user_level():
    return current_user.level or 0

def _can_access_setting(setting):
    return _current_user_level() >= setting_levels.get(setting, 5)

def _filter_settings_for_current_user(settings):
    return {setting: value for setting, value in settings.items() if _can_access_setting(setting)}

# name corresponds to a setting that can be manipulated in the front-end
# setting is used to display/hide the item, depending on the level
def _template_item_setting(item):
    if "setting" in item:
        return item["setting"]
    if "name" in item:
        return item["name"]
    return None

def _filter_template_for_current_user(template):
    filtered = []
    for item in template:
        if isinstance(item, list):
            row = _filter_template_for_current_user(item)
            if row:
                filtered.append(row)
            continue

        setting = _template_item_setting(item)
        if setting and not _can_access_setting(setting):
            continue

        item = {**item}
        item.pop("setting", None)
        if "rows" in item:
            rows = _filter_template_for_current_user(item["rows"])
            if rows:
                item["rows"] = rows
            else:
                continue
        filtered.append(item)
    return filtered

def _settings_template():
    smartschool_message_variables = ", ".join(al.infobord.MESSAGE_VARIABLES)
    smartschool_message_tags = html.escape(", ".join(al.infobord.message_template_tags()))
    smartschool_school_codes = al.infobord.school_codes()
    smartschool_additional_receivers_example = "<br>".join(
        f"{html.escape(school)}:<br>&nbsp;&nbsp;- boro" for school in smartschool_school_codes
    ) or "schoolcode:<br>&nbsp;&nbsp;- boro"
    cron_enable_modules = dl.settings.get_configuration_setting('cron-enable-modules') if _can_access_setting('cron-enable-modules') else {}
    cron_modules_template = [
        {
            "label": module[2],
            "setting": "cron-enable-modules",
            "name": module[0],
            "type": "check",
            "class": "cron-modules",
            "attribute": {"checked": cron_enable_modules.get(module[0], False)}
        }
        for module in cron_table
    ]
    template = [
        {
            "type": "container", "label": "Templates", "save": True, "default_collapsed": True, "rows": [
                {"label": "Gebruikers", "name": "user-datatables-template", "type": "textarea"},
            ]
        },
        {
            "type": "container", "label": "Modules", "default_collapsed": True, "rows": [
                {
                    "type": "container", "label": "Algemeen", "save": True, "default_collapsed": True, "rows": [
                        [{"label": "Nieuwe gebruikers mogen via Smartschool aanmelden?", "name": "generic-new-via-smartschool", "type": "check"}],
                        [{"label": "Nieuwe gebruikers, standaard niveau", "name": "generic-new-via-smartschool-default-level", "type": "select"}],
                    ]
                },
                {
                    "type": "container", "label": "Cron", "save": True, "default_collapsed": True, "rows": [
                        [{"label": "Cron template", "name": "cron-scheduler-template", "type": "input"}],
                        [
                            {"label": "Start cron cyclus?", "setting": "cron-enable-modules", "id": "display-button-start-cron-cycle", "type": "check", "save": False},
                            {"label": "Start", "setting": "cron-enable-modules", "id": "button-start-cron-cycle", "type": "button", "class": "btn btn-success"},
                        ],
                        *cron_modules_template,
                    ]
                },
                {
                    "type": "container", "label": "Smartschool", "save": True, "default_collapsed": True, "rows": [
                        {
                            "type": "container", "label": "Bericht voor: Thuis", "default_collapsed": True, "rows": [
                                [{"label": "Bericht onderwerp", "name": "smartschool-message-title-at-home", "type": "input", "class": "smartschool-message-title-setting"}],
                                {"label": "Bericht inhoud", "name": "smartschool-message-body-at-home", "type": "quill", "editor_height": "220px", "class": "smartschool-message-body-setting"},
                            ]
                        },
                        {
                            "type": "container", "label": "Bericht voor: Naar Huis", "default_collapsed": True, "rows": [
                                [{"label": "Bericht onderwerp", "name": "smartschool-message-title-to-home", "type": "input", "class": "smartschool-message-title-setting"}],
                                {"label": "Bericht inhoud", "name": "smartschool-message-body-to-home", "type": "quill", "editor_height": "220px", "class": "smartschool-message-body-setting"},
                            ]
                        },
                        {"label": "Extra ontvangers (YAML per school)", "name": "smartschool-message-additional-receivers", "type": "textarea"},
                        [{"label": "Afzender (personeelscode, laat leeg voor generieke afzender Campus Sint-Ursula)", "name": "smartschool-message-sender", "type": "input"}],
                        [{"label": "Smartschool berichten effectief verzenden?", "name": "smartschool-message-enable-sending", "type": "check"}],
                        {"type": "div", "setting": "smartschool-message-additional-receivers", "innerHTML": f"Extra ontvangers voorbeeld:<br>{smartschool_additional_receivers_example}<br># commentaar<br><br>Beschikbare variabelen: {smartschool_message_variables}<br><br>Schooltags: {smartschool_message_tags}"},
                    ]
                },
                {
                    "type": "container", "label": "Scholen configuratie", "save": True, "default_collapsed": True, "rows": [
                        {"label": "YAML", "name": "school-configuration", "type": "textarea"},
                    ]
                },
                {
                    "type": "container", "label": "Velden configuratie", "save": True, "default_collapsed": True, "rows": [
                        {"label": "YAML", "name": "field-configuration", "type": "textarea"},
                    ]
                },
            ]
        }
    ]
    return _filter_template_for_current_user(template)

@bp_settings.route('/settingsshow', methods=['GET'])
@login_required
@supervisor_required
def show():
    return render_template('settings.html', data=[])


@bp_settings.route('/setting', methods=['GET', 'UPDATE'])
@login_required
@supervisor_required
def setting():
    try:
        ret = {}
        if request.method == "UPDATE":
            data = json.loads(request.data)
            if not all(_can_access_setting(setting) for setting in data):
                return fetch_return_error("Niet voldoende rechten om deze instellingen te bewaren")
            ret = al.settings.update(data)
        if request.method == "GET":
            ret = al.settings.get()
            if "data" in ret:
                ret["data"] = _filter_settings_for_current_user(ret["data"])
        return json.dumps(ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return fetch_return_error()

@bp_settings.route('/button', methods=['POST'])
@login_required
@admin_required
def button():
    try:
        ret = {}
        if request.method == "POST":
            data = json.loads(request.data)
            al.settings.button(data["id"])
        return json.dumps(ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return fetch_return_error()

@bp_settings.route('/setting/meta', methods=['GET'])
@login_required
def meta():
    user_level_label = dl.user.User.level_label
    user_level_option =[{"value": k, "label": v} for k, v in user_level_label.items()]
    return json.dumps({
        "template": _settings_template(),
        "option": {"generic-new-via-smartschool-default-level": user_level_option},
    })
