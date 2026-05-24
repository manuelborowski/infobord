from app import data as dl
import sys, datetime

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

def add_update(data, add=True):
    try:
        if data:
            school = data[0]["school"]
            school_info = dl.settings.get_configuration_setting("school-configuration")[school]
            if "mark_recent_update" in school_info:
                now = datetime.datetime.now()
                now_string = str(now)
                date = now_string[:10]
                time =  now_string[11:19]
                now_lestijd = 10
                lestijden = app.config["LESTIJDEN"]
                for lestijd in range(9, 0, -1):
                    start_time_string = lestijden[lestijd]
                    start_time = datetime.datetime.strptime(f"{date} {start_time_string}:00", "%Y-%m-%d %H.%M:%S")
                    if now >= start_time:
                        now_lestijd = lestijd
                        break
                for d in data:
                    d["recent_update"] = d["lesuur"] > now_lestijd and d["datum"] == date
            if add:
                dl.infobord.add_m(data)
            else:
                dl.infobord.update_m(data)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def add(data):
    return add_update(data)

def update(data):
    return add_update(data, False)

def get_klasgroepen(school):
    try:
        klasgroepen = {}
        schedules = dl.schoolschedule.get_m([("school", "=", school)], order_by=["klascode"])
        for schedule in schedules:
            klascode_parts = schedule.klascode.split(" ", 1)
            if len(klascode_parts) != 2:
                continue
            klasgroep, klas = klascode_parts
            if klasgroep not in klasgroepen:
                klasgroepen[klasgroep] = []
            if klas not in klasgroepen[klasgroep]:
                klasgroepen[klasgroep].append(klas)
        return klasgroepen
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {}
