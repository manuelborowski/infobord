import inspect
import requests
from app import MyLogFilter, top_log_handle, app
from app import data as dl

# logging on file level
import logging

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

def _student_payload(sdh_student):
    klascode = sdh_student.get("klascode", "")
    return {
        "leerlingnummer": sdh_student.get("leerlingnummer", ""),
        "klas": sdh_student.get("klas", klascode),
        "klascode": klascode,
        "klasgroep": sdh_student.get("klasgroep", ""),
        "naam": sdh_student.get("naam", ""),
        "voornaam": sdh_student.get("voornaam", ""),
        "roepnaam": sdh_student.get("roepnaam", ""),
        "rfid": sdh_student.get("rfid", ""),
        "instellingsnummer": sdh_student.get("instellingsnummer", ""),
        "username": sdh_student.get("username", ""),
    }

def student_load_from_sdh(opaque=None, **kwargs):
    try:
        log.info(f'{inspect.currentframe().f_code.co_name}, START')
        updated_students = []
        new_students = []
        deleted_students = []
        sdh_url = app.config["SDH_GET_STUDENT_URL"]
        sdh_key = app.config["SDH_GET_API_KEY"]
        res = requests.get(sdh_url, headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_students = res.json()
            if sdh_students['status']:
                db_students = dl.student.get_m()
                db_leerlingnummer_to_student = {s.leerlingnummer: s for s in db_students}
                for sdh_student in sdh_students["data"]:
                    student = _student_payload(sdh_student)
                    leerlingnummer = student["leerlingnummer"]
                    if leerlingnummer in db_leerlingnummer_to_student:
                        db_student = db_leerlingnummer_to_student[leerlingnummer]
                        update = {}
                        for field, value in student.items():
                            if getattr(db_student, field) != value:
                                update[field] = value
                        if update:
                            update.update({"obj": db_student})
                            updated_students.append(update)
                        del db_leerlingnummer_to_student[leerlingnummer]
                    else:
                        new_students.append(student)
                deleted_students = list(db_leerlingnummer_to_student.values())
                dl.student.update_m(updated_students)
                dl.student.add_m(new_students)
                dl.student.delete_m(objs=deleted_students)
                log.info(f'{inspect.currentframe().f_code.co_name}, students add/update/delete {len(new_students)}/{len(updated_students)}/{len(deleted_students)}')
            else:
                log.info(f'{inspect.currentframe().f_code.co_name}, error retrieving students from SDH, {sdh_students["data"]}')
        else:
            log.error(f'{inspect.currentframe().f_code.co_name}: api call to {sdh_url} returned {res.status_code}')
        log.info(f'{inspect.currentframe().f_code.co_name}, STOP')
    except Exception as e:
        log.error(f'{inspect.currentframe().f_code.co_name}: {e}')
