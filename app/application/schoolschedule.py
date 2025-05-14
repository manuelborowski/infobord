from app import data as dl
import sys, requests

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def schedule_load_from_sdh(opaque=None, **kwargs):
    try:
        log.info(f"{sys._getframe().f_code.co_name}, START")
        sdh_url = app.config["SDH_GET_SCHEDULE_URL"]
        sdh_key = app.config["SDH_GET_API_KEY"]
        res = requests.get(sdh_url, headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_schedules = res.json()
            if sdh_schedules['status']:
                # delete the current schedule
                dl.schoolschedule.truncate()
                dl.schoolschedule.add_m(sdh_schedules["data"])
                log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_schedules["data"])} items')
            else:
                log.info(f'{sys._getframe().f_code.co_name}, error retrieving schedule from SDH, {sdh_schedules["data"]}')
        else:
            log.error(f'{sys._getframe().f_code.co_name}: api call to {sdh_url} returned {res.status_code}')
        log.info(f"{sys._getframe().f_code.co_name}, STOP")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

