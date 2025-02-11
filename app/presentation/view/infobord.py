from flask import Blueprint, render_template, request, redirect, url_for
from app import data as dl
import json

# logging on file level
import logging
from app import MyLogFilter, top_log_handle, app
from flask_login import login_required, current_user

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

bp_infobord = Blueprint('infobord', __name__)

@bp_infobord.route('/infobordedit', methods=['GET', "POST", "DELETE"])
@login_required
def edit():
    if request.method == "GET":
        school = request.args.get("school")
        infos = dl.inforbord.get_m(("school", "=", school))
        infos = [i.to_dict() for i in infos]
    if request.method == "POST":
        school = request.args.get("school")
        data = json.loads(request.data)
        # remove old entries
        infos = dl.inforbord.get_m(("school", "=", school))
        dl.inforbord.delete_m(objs=infos)
        data = dl.inforbord.add_m(data)
        data = [d.to_dict() for d in data]
        return {"data": data}
    if request.method == "DELETE":
        school = request.args.get("school")
        infos = dl.inforbord.get_m(("school", "=", school))
        dl.inforbord.delete_m(objs=infos)
        return {}
    return render_template("infobord.html", global_data={"school": school, "info": infos})

@bp_infobord.route('/infobordview', methods=['GET'])
def view():
    school = request.args.get("school")
    font_size = request.args.get("fontsize")
    infos = dl.inforbord.get_m(("school", "=", school))
    infos = [i.to_dict() for i in infos]
    return render_template("infobord_view.html", global_data={"school": school, "info": infos, "lestijden": app.config["LESTIJDEN"], "font_size": font_size})
