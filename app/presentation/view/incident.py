from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.data.datatables import DatatableConfig
from app import data as dl, application as al
from app.presentation.view import datatable_get_data, fetch_return_error
import json, sys, pathlib

# logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

bp_incident = Blueprint('incident', __name__)

@bp_incident.route('/incidentshow', methods=['GET'])
@login_required
def show():
    id_to_show = request.args.get("id")
    generate = request.args.get("generate")
    if generate:
        al.incident.generate(int(generate))
    event = request.args.get("event")
    if event:
        al.incident.event(int(event))
    locations = dl.settings.get_configuration_setting("lis-locations")
    location_options = [{"label": v["label"], "value": k} for (k, v) in locations.items()]
    found, default_location = dl.settings.get_setting("default-location", current_user.username)
    if not found:
        default_location = location_options[0]["value"]
        dl.settings.add_setting("default-location", default_location, user=current_user.username)
    data = {"filters": [{"id": "incident-id", "value": id_to_show}]}
    return render_template("incident.html", table_config=config.create_table_config(), view_data=data)

# invoked when the client requests data from the database
al.socketio.subscribe_on_type("incident-datatable-data", lambda type, data: datatable_get_data(config, data))

@bp_incident.route('/incident', methods=['POST', "UPDATE", "GET"])
@login_required
def incident():
    try:
        ret = {}
        if request.method == "POST":
            data = json.loads(request.data)
            ret = al.incident.add(data)
        if request.method == "UPDATE":
            data = json.loads(request.data)
            ret = al.incident.update(data)
        if request.method == "GET":
            ret = al.models.get(dl.incident.Incident, request.args)
        return json.dumps(ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return fetch_return_error()

@bp_incident.route('/incident/message', methods=['POST', "GET"])
@login_required
def message():
    try:
        ret = {}
        if request.method == "POST":
            data = json.loads(request.data)
            ret = al.incident.message_send(data)
        if request.method == "GET":
            id = request.args.get("id")
            ret = al.incident.message_default(id)
        return json.dumps(ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return fetch_return_error()

@bp_incident.route('/incident/meta', methods=['GET'])
@login_required
def meta():
    categories = dl.settings.get_configuration_setting("lis-categories")
    category_labels = {k: v["label"] for k, v in categories.items()}
    locations = dl.settings.get_configuration_setting("lis-locations")
    location_options = [{"value": k, "label": v["label"]} for k, v in locations.items()]
    location_labels = {k: v["label"] for k, v in locations.items()}
    types = dl.settings.get_configuration_setting("lis-incident-types")
    type_options = [{"value": k, "label": v["label"]} for k, v in types.items()]
    type_labels = {k: v["label"] for k, v in types.items()}
    states = dl.settings.get_configuration_setting("lis-state")
    state_options = [{"value": k, "label": v["label"]} for k, v in states.items()]
    state_labels = {k: v["label"] for k, v in states.items()}
    _, default_location = dl.settings.get_setting("default-location", current_user.username)
    default_password = app.config["AD_DEFAULT_PASSWORD"]
    return json.dumps({"option": {"location": location_options, "incident_state": state_options, "incident_type": type_options},
                       "label": {"location": location_labels, "incident_state": state_labels, "category": category_labels, "incident_type": type_labels},
                       "default": {"location": default_location},
                       "default_password": default_password,
                       "category": categories,
                       })

@bp_incident.route('/incident/location', methods=['POST',])
@login_required
def location():
    try:
        if request.method == "POST":
            data = json.loads(request.data)
            dl.settings.set_setting("default-location", data["default"], user=current_user.username)
            ret = {"data": "ok"}
            return json.dumps(ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: Exception, {e}')
        return fetch_return_error(f'Exception, {e}')

@bp_incident.route('/incident/form', methods=['GET'])
@login_required
def form():
    try:
        if request.method == "GET":
            form = request.args.get('form')
            optional = []
            template = ""
            if form == "sw-hw-new":
                optional = {"url": app.config["ENTRA_API_URL"], "key": app.config["ENTRA_API_KEY"]}
                template = open(pathlib.Path("app/presentation/template/lib/sw_hw_new_form.html")).read()
            if form == "sw-hw-update":
                template = open(pathlib.Path("app/presentation/template/lib/sw_hw_update.html")).read()
            if form == "history":
                template = open(pathlib.Path("app/presentation/template/lib/history_form.html")).read()
            if form == "message":
                template = open(pathlib.Path("app/presentation/template/lib/ss_message.html")).read()
            if form == "loan":
                template = open(pathlib.Path("app/presentation/template/lib/loan_form_new.html")).read()
            if form == "setting":
                template = open(pathlib.Path("app/presentation/template/lib/setting_form.html")).read()
            return {"template": template, "defaults": [], "data": optional}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: Exception, {e}')
        return fetch_return_error(f'Exception, {e}')


class Config(DatatableConfig):
    def pre_sql_query(self):
        return dl.incident.pre_sql_query()

    def pre_sql_filter(self, q, filters):
        return dl.incident.pre_sql_filter(q, filters)

    def pre_sql_search(self, search):
        return dl.incident.pre_sql_search(search)

    def post_process_template(self, template):
        locations = dl.settings.get_configuration_setting("lis-locations")
        location_labels = {k: v["label"] for (k, v) in locations.items()}
        states = dl.settings.get_configuration_setting("lis-state")
        state_labels = {k: v["label"] for (k, v) in states.items()}
        state_colors = {k: v["color"] for (k, v) in states.items()}
        standard_button_template = f'<a type="button" class="btn-incident-update btn btn-success"><i class="fa-solid fa-pen-to-square" title="Incident aanpassen"></i></a></div>'
        standard_button_template += f'<a type="button" class="btn-show-history btn btn-success"><i class="fa-solid fa-clock-rotate-left" title="Historiek bekijken"></i></a></div>'
        message_button_template = f'<a type="button" class="btn-send-message btn btn-success"><i class="fa-regular fa-envelope" title="Bericht sturen"></i></a></div>'
        close_button_template = f'<a type="button" class="btn-incident-close btn btn-success"><i class="fa-solid fa-xmark" title="Incident sluiten"></i></a></div>'
        categories = dl.settings.get_configuration_setting("lis-categories")
        category_labels = {k: v["label"] for k, v in categories.items()}

        action_labels = {
            "started": standard_button_template + message_button_template,
            "transition": standard_button_template + message_button_template,
            "repaired": standard_button_template + message_button_template + close_button_template,
            "shortloan": standard_button_template + message_button_template + close_button_template,
            "longloan": standard_button_template + message_button_template + close_button_template,
            "closed": "NVT"
        }

        for column in template:
            if "data" in column:
                if column["data"] == "incident_state" and column["name"] == "Status":
                    column["label"] = {"labels": state_labels}
                    column["color"] = {"colors": state_colors}
                if column["data"] == "location":
                    column["label"] = {"labels": location_labels}
                if column["data"] == "category":
                    column["label"] = {"labels": category_labels}
                if column["data"] == "info":
                    column["ellipsis"] = {"cutoff": 30, "wordbreak": True}
                if column["data"] == "incident_state" and column["name"] == "Actie":
                    column["label"] = {"labels": action_labels}
        return template

    def format_data(self, db_list, total_count=None, filtered_count=None):
        return al.incident.format_data(db_list, total_count, filtered_count)

config = Config("incident", "Incidenten")
