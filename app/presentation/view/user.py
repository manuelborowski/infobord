from flask import Blueprint, render_template, request
from flask_login import login_required
from app import admin_required
from app.data.datatables import DatatableConfig
from app import data as dl, application as al
from app.presentation.view import datatable_get_data, fetch_return_error
import json, sys

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())
bp_user = Blueprint('user', __name__)

@bp_user.route('/usershow', methods=['GET', 'POST'])
@admin_required
@login_required
def show():
    return render_template("user.html", table_config=config.create_table_config())

# invoked when the client requests data from the database
al.socketio.subscribe_on_type("user-datatable-data", lambda type, data: datatable_get_data(config, data))

@bp_user.route('/user', methods=["POST", "UPDATE", "DELETE", "GET"])
@login_required
def user():
    if request.method == "UPDATE":
        data = json.loads(request.data)
        ret = al.user.update(data)
    elif request.method == "POST":
        data = json.loads(request.data)
        ret = al.user.add(data)
    elif request.method == "DELETE":
        ret = al.user.delete(request.args["ids"].split(","))
    else: # GET
        ret = al.user.get(request.args)
    return json.dumps(ret)

@bp_user.route('/form', methods=["GET"])
@login_required
def form():
    try:
        params = request.args
        defaults = {}
        if "user_id" in params:
            user = dl.user.get(("id", "=", params["user_id"]))
            defaults = user.to_dict()
            defaults["level"] = {"default": defaults["level"]}
            defaults["user_type"] = {"default": defaults["user_type"]}
        return {"template": user_popup, "defaults": defaults}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: Exception, {e}')
        return fetch_return_error(f'Exception, {e}')


def value_update(type, data):
    user = dl.user.get(("id", "=", data["id"]))
    dl.user.update(user, {data["column"]: data["value"]})

# invoked when a single cell in the table is updated
al.socketio.subscribe_on_type("cell-update", value_update)


class Config(DatatableConfig):
    def pre_sql_query(self):
        return dl.user.pre_sql_query()

    def pre_sql_filter(self, q, filters):
        return dl.user.pre_sql_filter(q, filters)

    def pre_sql_search(self, search):
        return dl.user.pre_sql_search(search)

    def format_data(self, l, total_count, filtered_count):
        return al.user.format_data(l, total_count, filtered_count)

config = Config("user", "Gebruikers")

false = False
true = True
null = None

user_popup = {
  "display": "form",
  "components": [
    {
      "title": "Gebruiker",
      "collapsible": false,
      "key": "gebruiker",
      "type": "panel",
      "label": "Panel",
      "input": false,
      "tableView": false,
      "components": [
        {
          "label": "Gebruikersnaam",
          "labelPosition": "left-left",
          "tableView": true,
          "key": "username",
          "type": "textfield",
          "input": true
        },
        {
          "label": "Achternaam",
          "labelPosition": "left-left",
          "tableView": true,
          "key": "last_name",
          "type": "textfield",
          "input": true
        },
        {
          "label": "Voornaam",
          "labelPosition": "left-left",
          "tableView": true,
          "key": "first_name",
          "type": "textfield",
          "input": true
        },
        {
          "label": "E-mail",
          "labelPosition": "left-left",
          "tableView": true,
          "key": "email",
          "type": "email",
          "input": true
        },
        {
          "label": "Niveau",
          "labelPosition": "left-left",
          "widget": "choicesjs",
          "tableView": true,
          "defaultValue": 1,
          "data": {
            "values": [
              {
                "label": "Gebruiker",
                "value": "1"
              },
              {
                "label": "Secretariaat",
                "value": "3"
              },
              {
                "label": "Administrator",
                "value": "5"
              }
            ]
          },
          "key": "level",
          "type": "select",
          "input": true
        },
        {
          "label": "Type",
          "labelPosition": "left-left",
          "widget": "choicesjs",
          "tableView": true,
          "defaultValue": "local",
          "data": {
            "values": [
              {
                "label": "Local",
                "value": "local"
              },
              {
                "label": "Oauth",
                "value": "oauth"
              }
            ]
          },
          "key": "user_type",
          "type": "select",
          "input": true
        },
        {
          "label": "Nieuw wachtwoord?",
          "tableView": false,
          "key": "new_password",
          "type": "checkbox",
          "input": true,
          "defaultValue": false
        },
        {
          "label": "Paswoord",
          "labelPosition": "left-left",
          "tableView": false,
          "key": "password",
          "conditional": {
            "show": true,
            "when": "new_password",
            "eq": "true"
          },
          "type": "password",
          "input": true,
          "protected": true
        },
        {
          "label": "Bevestig paswoord",
          "labelPosition": "left-left",
          "tableView": false,
          "validate": {
            "custom": "valid = (input === data.password) ? true : \"Paswoorden zijn niet gelijk\";"
          },
          "key": "confirm_password",
          "conditional": {
            "show": true,
            "when": "new_password",
            "eq": "true"
          },
          "type": "password",
          "input": true,
          "protected": true
        }
      ]
    },
    {
      "label": "Columns",
      "columns": [
        {
          "components": [
            {
              "label": "Opslaan",
              "showValidations": false,
              "theme": "success",
              "disableOnInvalid": true,
              "tableView": false,
              "key": "submit",
              "type": "button",
              "saveOnEnter": false,
              "input": true
            }
          ],
          "width": 3,
          "offset": 0,
          "push": 0,
          "pull": 0,
          "size": "md",
          "currentWidth": 3
        },
        {
          "components": [
            {
              "label": "Annuleer",
              "action": "event",
              "showValidations": false,
              "theme": "warning",
              "tableView": false,
              "key": "annuleer",
              "type": "button",
              "input": true,
              "event": "cancel"
            }
          ],
          "width": 3,
          "offset": 0,
          "push": 0,
          "pull": 0,
          "size": "md",
          "currentWidth": 3
        }
      ],
      "key": "columns",
      "type": "columns",
      "input": false,
      "tableView": false
    },
    {
      "label": "id",
      "key": "id",
      "type": "hidden",
      "input": true,
      "tableView": false
    }
  ]
}
