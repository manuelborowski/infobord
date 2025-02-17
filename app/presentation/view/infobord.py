from flask import Blueprint, render_template, request, redirect, url_for
from app import data as dl
import json, datetime

# logging on file level
import logging
from app import MyLogFilter, top_log_handle, app
from flask_login import login_required, current_user

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

bp_infobord = Blueprint('infobord', __name__)

@bp_infobord.route('/infobordedit', methods=['GET'])
@login_required
def edit():
    school = request.args.get("school")
    school_info = dl.settings.get_configuration_setting("school-configuration")[school]
    field_info = dl.settings.get_configuration_setting("field-configuration")
    return render_template("infobord.html", global_data={"school": school, "school_info": school_info, "field_info": field_info})

@bp_infobord.route('/infobordview', methods=['GET'])
def view():
    school = request.args.get("school")
    datum = request.args.get("datum")
    font_size = request.args.get("fontsize")
    width = request.args.get("width")
    preview = request.args.get("preview") == "true"
    view_date = datum if datum else datetime.datetime.now().strftime("%Y-%m-%d")
    infos = dl.infobord.get_m([("school", "=", school), ("datum", "=", view_date)])
    infos = [i.to_dict() for i in infos]
    extra_info = dl.extra_info.get([("school", "=", school)])
    school_info = dl.settings.get_configuration_setting("school-configuration")[school]
    field_info = dl.settings.get_configuration_setting("field-configuration")
    global_data={"school": school, "info": infos, "lestijden": app.config["LESTIJDEN"], "font_size": font_size, "width": width, "preview": preview,
                 "date": view_date, "extra_info": extra_info.to_dict() if extra_info else None, "school_info": school_info, "field_info": field_info}
    return render_template("infobord_view.html", global_data=global_data)

@bp_infobord.route('/infobord', methods=['GET', "POST", "DELETE", "UPDATE"])
@login_required
def infobord():
    school = request.args.get("school")
    datum = request.args.get("datum")
    infos = dl.infobord.get_m([("school", "=", school), ("datum", "=", datum)])
    if request.method == "GET":
        week_old_infos = []
        for i in range(1, 4):
            date = datetime.datetime.strptime(datum, "%Y-%m-%d") - datetime.timedelta(days= 7 * i)
            week_old_infos += dl.infobord.get_m([("school", "=", school), ("datum", "=", date.strftime("%Y-%m-%d"))])
        week_old_infos = [i.to_dict() for i in week_old_infos]
        infos = [i.to_dict() for i in infos]
        return {"data": infos, "vervangers": week_old_infos}
    if request.method == "POST":
        data = json.loads(request.data)
        dl.infobord.add_m(data)
    if request.method == "UPDATE":
        data = json.loads(request.data)
        dl.infobord.update_m(data)
    if request.method == "DELETE":
        dl.infobord.delete_m(objs=infos)
    return {}


@bp_infobord.route('/extrainfo', methods=['GET', "POST", "UPDATE"])
@login_required
def extrainfo():
    school = request.args.get("school")
    if request.method in ["GET"]:
        extra_info = dl.extra_info.get([("school", "=", school)])
        return {"data": extra_info.to_dict() if extra_info else None}
    if request.method == "POST":
        data = json.loads(request.data)
        dl.extra_info.add(data)
    if request.method == "UPDATE":
        data = json.loads(request.data)
        dl.extra_info.update(data)
    return {}

@bp_infobord.route('/extrainfoview', methods=['GET'])
def extrainfoview():
    school = request.args.get("school")
    extra_info = dl.extra_info.get([("school", "=", school)])
    return render_template("infobord_view_extra.html", extra_info=extra_info.to_dict() if extra_info else None)

