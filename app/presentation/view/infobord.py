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
    return render_template("infobord.html", global_data={"school": school})

@bp_infobord.route('/infobordview', methods=['GET'])
def view():
    school = request.args.get("school")
    font_size = request.args.get("fontsize")
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    infos = dl.infobord.get_m([("school", "=", school), ("datum", "=", now)])
    infos = [i.to_dict() for i in infos]
    return render_template("infobord_view.html", global_data={"school": school, "info": infos, "lestijden": app.config["LESTIJDEN"], "font_size": font_size})

@bp_infobord.route('/infobord', methods=['GET', "POST", "DELETE"])
@login_required
def infobord():
    school = request.args.get("school")
    datum = request.args.get("datum")
    infos = dl.infobord.get_m([("school", "=", school), ("datum", "=", datum)])
    week_old_infos = []
    if request.method in ["GET", "POST"]:
        date = datetime.datetime.strptime(datum, "%Y-%m-%d") - datetime.timedelta(days=7)
        week_old_infos = dl.infobord.get_m([("school", "=", school), ("datum", "=", date.strftime("%Y-%m-%d"))])
        week_old_infos = [i.to_dict() for i in week_old_infos]
    if request.method == "GET":
        infos = [i.to_dict() for i in infos]
        return {"data": infos, "vervangers": week_old_infos}
    if request.method == "POST":
        data = json.loads(request.data)
        # remove old entries
        dl.infobord.delete_m(objs=infos)
        data = dl.infobord.add_m(data)
        data = [d.to_dict() for d in data]
        return {"data": data, "vervangers": week_old_infos}
    if request.method == "DELETE":
        dl.infobord.delete_m(objs=infos)
    return {}

