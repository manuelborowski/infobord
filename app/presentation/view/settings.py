from flask import render_template, Blueprint
from flask_login import login_required

from app import admin_required, data as dl, application as al
from app.presentation.view import send_alert_to_client
from app.application import cron_table
import json

bp_settings = Blueprint('settings', __name__)

@bp_settings.route('/settingsshow', methods=['GET', 'POST'])
@admin_required
@login_required
def show():
  cron_module_enable_settings = dl.settings.get_configuration_setting('cron-enable-modules')
  cron_component = al.formio.search_component(settings_formio, 'cron-enable-modules')
  cron_component["components"] = []
  for nbr, module in enumerate(cron_table):
    enabled = cron_module_enable_settings[module[0]] if module[0] in cron_module_enable_settings else False
    cron_component["components"].append({"label": f'({nbr+1}) {module[2]}', "tooltip": module[3], "tableView": False, "defaultValue": enabled, "key": module[0], "type": "checkbox", "input": True})
  default_settings = dl.settings.get_configuration_settings(convert_to_string=True)
  data = {'default': default_settings, 'template': settings_formio}
  return render_template('settings.html', data=data)


def update_settings_cb(type, data):
  try:
    settings = json.loads(data['value'])
    ret = al.settings.set_setting_topic(settings)
    al.socketio.broadcast_message({'type': 'settings', 'data': None})
    if not ret["status"]:
      send_alert_to_client("error", ret["data"])
  except Exception as e:
    al.socketio.broadcast_message({'type': 'settings', 'data': None})
    send_alert_to_client("error", str(e))

al.socketio.subscribe_on_type('settings', update_settings_cb)

false = False
true = True
null = None

# https://formio.github.io/formio.js/app/builder
settings_formio = {"display": "form", "components": [
  {"title": "Templates", "theme": "warning", "collapsible": true, "key": "templates", "type": "panel", "label": "Panel", "collapsed": true, "input": false, "tableView": false, "components": [
    {"label": "Users", "tableView": false, "key": "users", "type": "container", "input": true, "components": [
      {"title": "Gebruikers", "theme": "primary", "collapsible": true, "key": "gebruikers", "type": "panel", "label": "Algemeen", "collapsed": true, "input": false, "tableView": false, "components": [
        {"label": "Opslaan", "theme": "warning", "tableView": false, "key": "submit", "type": "button", "input": true, "saveOnEnter": false},
        {"label": "Lijst template (YAML)", "autoExpand": false, "tableView": true, "key": "user-datatables-template", "type": "textarea", "input": true}]}]}]},
  {"title": "Modules", "theme": "warning", "collapsible": true, "key": "modules", "type": "panel", "label": "Panel", "input": false, "tableView": false, "components": [
    {"label": "generic", "tableView": false, "key": "generic", "type": "container", "input": true, "components": [
      {"title": "Algemeen", "theme": "primary", "collapsible": true, "key": "algemeen", "type": "panel", "label": "Smartschool", "collapsed": true, "input": false, "tableView": false, "components": [
        {"label": "Opslaan ", "showValidations": false, "theme": "warning", "tableView": false, "key": "submit", "type": "button", "input": true},
        {"label": "Nieuwe gebruikers via smartschool login?", "tooltip": "Mogen nieuwe gebruikers inloggen via de Smartschool OAuth2?", "tableView": false, "key": "generic-new-via-smartschool", "type": "checkbox", "input": true, "defaultValue": false},
        {"label": "Nieuwe gebruikers via Smartschool: standaard niveau", "labelPosition": "left-left", "widget": "choicesjs", "tooltip": "Standaard niveau wanneer een gebruiker voor de eerste maal aanmeldt via Smartschool OAuth2", "tableView": true, "defaultValue": 1, "data": {"values": [
          {"label": "Gebruiker", "value": "1"}, {"label": "Gebruiker+", "value": "2"}, {"label": "Toezichthouder", "value": "3"}, {"label": "Toezichthouder+", "value": "4"},
          {"label": "Administrator", "value": "5"}]}, "key": "generic-new-via-smartschool-default-level", "type": "select", "input": true, "labelWidth": 60},
        {"label": "Scholen configuratie (YAML)", "applyMaskOn": "change", "autoExpand": false, "tableView": true, "validateWhenHidden": false, "key": "school-configuration", "type": "textarea", "input": true},
        {"label": "Velden configuratie (YAML)", "applyMaskOn": "change", "tableView": true, "validateWhenHidden": false, "key": "field-configuration", "type": "textarea", "input": true, "inputFormat": "plain", "keyModified": true}]}]},
    {"label": "Cron-generic", "tableView": false, "key": "cron-generic", "type": "container", "input": true, "components": [
      {"title": "Cron: generiek", "theme": "primary", "collapsible": true, "key": "cron-generic", "type": "panel", "label": "Smartschool", "collapsed": true, "input": false, "tableView": false, "components": [
        {"label": "Opslaan ", "showValidations": false, "theme": "warning", "tableView": false, "key": "submit", "type": "button", "input": true},
        {"label": "Cron template", "labelPosition": "left-left", "tooltip": "Check https://crontab.guru/ voor de layout van de cron template", "tableView": true, "persistent": false, "key": "cron-scheduler-template", "type": "textfield", "labelWidth": 20, "input": true},
        {"label": "Columns", "columns": [{"components": [
          {"label": "Start cron cyclus", "tableView": false, "defaultValue": false, "key": "check-start-cron-cycle", "type": "checkbox", "input": true}], "width": 3, "offset": 0, "push": 0, "pull": 0, "size": "md", "currentWidth": 3},
          {"components": [
            {"label": "Start cron cyclus", "showValidations": false, "theme": "danger", "tableView": false, "key": "button-start-cron-cycle", "conditional": {"show": true, "when": "cron-generic.check-start-cron-cycle", "eq": "true"}, "type": "button", "saveOnEnter": false, "input": true}], "width": 6, "offset": 0, "push": 0, "pull": 0, "size": "md", "currentWidth": 6}], "key": "columns", "type": "columns", "input": false, "tableView": false},
        {"label": "Container", "tableView": false, "key": "cron-enable-modules", "type": "container", "input": true, "components": []}]}]}], "collapsed": true}]}

