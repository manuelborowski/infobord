from app import data as dl
import sys, requests

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def staff_load_from_sdh(opaque=None, **kwargs):
    try:
        log.info(f"{sys._getframe().f_code.co_name}, START")
        updated_staff = []
        new_staff = []
        deleted_staff = []
        sdh_url = app.config["SDH_GET_STAFF_URL"]
        sdh_key = app.config["SDH_GET_API_KEY"]
        res = requests.get(sdh_url, headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_staffs = res.json()
            if sdh_staffs['status']:
                db_staffs = dl.staff.get_m()
                db_code2staff = {s.code: s for s in db_staffs} if db_staffs else {}
                for staff in sdh_staffs["data"]:
                    update = {}
                    if staff["code"] in db_code2staff:
                        # update existing staff
                        db_staff = db_code2staff[staff["code"]]
                        if db_staff.voornaam != staff["voornaam"]:
                            update["voornaam"] = staff["voornaam"]
                        if db_staff.naam != staff["naam"]:
                            update["naam"] = staff["naam"]
                        if db_staff.rfid != staff["rfid"]:
                            update["rfid"] = staff["rfid"]
                        if db_staff.ss_internal_nbr != staff["ss_internal_nbr"] if staff["ss_internal_nbr"] is not None else "":
                            update["ss_internal_nbr"] = staff["ss_internal_nbr"]
                        if update:
                            update.update({"item": db_staff})
                            updated_staff.append(update)
                        del db_code2staff[staff["code"]]
                    else:
                        # new staff
                        new_staff.append({"code": staff["code"], "voornaam": staff["voornaam"], "naam": staff["naam"],
                                          "ss_internal_nbr": staff["ss_internal_nbr"], "rfid": staff["rfid"],})
                # removed staff
                for staff in db_code2staff.values():
                    deleted_staff.append(staff)
                log.info(f'{sys._getframe().f_code.co_name}, new/updated/deleted {len(new_staff)}/{len(updated_staff)}/{len(deleted_staff)} staff')
                dl.staff.update_m(updated_staff)
                dl.staff.add_m(new_staff)
                dl.staff.delete_m(staffs=deleted_staff)
            else:
                log.info(f'{sys._getframe().f_code.co_name}, error retrieving staff from SDH, {sdh_staffs["data"]}')
        else:
            log.error(f'{sys._getframe().f_code.co_name}: api call to {sdh_url} returned {res.status_code}')
        log.info(f"{sys._getframe().f_code.co_name}, STOP")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

