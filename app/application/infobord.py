from app import data as dl, socketio
from app.application.smartschool import send_message as ss_send_message
import sys, datetime, re

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

MESSAGE_TYPE_NONE = "geen"
MESSAGE_TYPE_AT_HOME = "at-home"
MESSAGE_TYPE_TO_HOME = "to-home"

MESSAGE_SETTINGS = {
    MESSAGE_TYPE_AT_HOME: {
        "title": "smartschool-message-title-at-home",
        "body": "smartschool-message-body-at-home",
    },
    MESSAGE_TYPE_TO_HOME: {
        "title": "smartschool-message-title-to-home",
        "body": "smartschool-message-body-to-home",
    },
}

MESSAGE_VARIABLES = [
    "%%NAAM%%", "%%VOORNAAM%%", "%%ROEPNAAM%%", "%%KLAS%%", "%%KLASLIJST%%", "%%LEERLINGNUMMER%%", "%%DATUM%%",
    "%%LESUUR%%", "%%LEERKRACHT%%", "%%VERVANGER%%", "%%LOCATIE%%", "%%STAMLOKAAL%%", "%%INFO%%", "%%EXTRA%%",
]
MESSAGE_TEMPLATE_TAGS = [
    "<< tekst alleen voor leerlingen >>",
    "{{ tekst alleen voor extra ontvangers }}",
]

def _mark_recent_updates(data, school, datum):
    try:
        if data:
            school_info = dl.settings.get_configuration_setting("school-configuration")[school] if school else {}
            if "mark_recent_update" in school_info:
                now = datetime.datetime.now()
                now_string = str(now)
                date = now_string[:10]
                now_lestijd = 10
                lestijden = app.config["LESTIJDEN"]
                for lestijd in range(9, 0, -1):
                    start_time_string = lestijden[lestijd]
                    start_time = datetime.datetime.strptime(f"{date} {start_time_string}:00", "%Y-%m-%d %H.%M:%S")
                    if now >= start_time:
                        now_lestijd = lestijd
                        break
                for d in data:
                    if "lesuur" in d:
                        d["recent_update"] = d["lesuur"] > now_lestijd and datum == date
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def add(data, school, datum):
    for item in data:
        item["school"] = school
        item["datum"] = datum
    _mark_recent_updates(data, school, datum)
    return dl.infobord.add_m(data)

def update(data):
    try:
        # send-ss-message specific, when "bericht" is set, send a message to
        # the students and additional receivers (staff)
        message_jobs = []
        for item in data:
            if "id" not in item or "bericht" not in item or item["bericht"] not in MESSAGE_SETTINGS:
                continue
            current = dl.infobord.get([("id", "=", item["id"])])
            if current and current.bericht != item["bericht"]:
                klas = item["klas"] if "klas" in item else current.klas
                school = item["school"] if "school" in item else current.school
                students, error_msg = _students_for_klas(klas, school)
                if error_msg:
                    return {"status": "error", "msg": f"{error_msg}. <br>Pas de klassen aan en probeer opnieuw."}
                message_jobs.append({
                    "infobord_id": current.id,
                    "message_type": item["bericht"],
                    "subject_template": item.get("message_title"),
                    "body_template": item.get("message_body"),
                    "students": students,
                })
            item.pop("message_title", None)
            item.pop("message_body", None)
        ret = dl.infobord.update_m(data)
        for job in message_jobs:
            socketio.start_background_task(send_smartschool_message, **job)
        return ret or {}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": str(e)}

# klas is a string with one or more klassen, seperated by a comma.  Return as list of tokens
# in case of sul, a token can be a klas (5B MtWesport) or a complete klasgroep (5D)
def _get_klas_tokens(klas):
    tokens = set()
    for klascode in re.split(r",+", klas or ""):
        klascode = klascode.strip()
        if not klascode or klascode == "-":
            continue
        tokens.add(klascode)
    return tokens

def _student_school(student):
    first = student.klascode[:1].upper()
    instellingsnummer = student.instellingsnummer
    if instellingsnummer in ["30569", "30593"] and first in ["1", "2"]:
        return "sum"
    if instellingsnummer == "30593" and first in ["3", "4", "5", "6", "O"]:
        return "sul"
    if instellingsnummer == "30569" and first in ["3", "4", "5", "6"]:
        return "sui"
    return None

def _student_matches_school(student, school):
    return _student_school(student) == school

def _students_for_klas(klas, school):
    tokens = _get_klas_tokens(klas)
    students = []
    seen = set()
    missing_tokens = []
    school_students = [student for student in dl.student.get_m() if _student_matches_school(student, school)]
    for token in tokens:
        token_students = [student for student in school_students if student.klascode == token]
        if not token_students:
            # probably a sul klasgroep (e.g. 4A)
            token_students = [student for student in school_students if student.klascode.startswith(token)]
        if not token_students:
            missing_tokens.append(token)
            continue
        for student in token_students:
            if student.leerlingnummer not in seen:
                students.append(student.to_dict())
                seen.add(student.leerlingnummer)
    if missing_tokens:
        log.error(f"{sys._getframe().f_code.co_name}: Non existing class(es): {(missing_classes := ', '.join(sorted(missing_tokens)))}")
        return [], f"Smartschool bericht niet verzonden: klas(sen) niet gevonden: {missing_classes}"
    return students, None

def _replace_message_tags(template, student, info):
    template = template or ""

    def student_value(name, default=""):
        if not student:
            return default
        if isinstance(student, dict):
            return student.get(name, default)
        return getattr(student, name, default)

    template = re.sub(r"(?:<<|&lt;&lt;)\s*(.*?)\s*(?:>>|&gt;&gt;)", r"\1" if student else "", template, flags=re.DOTALL)
    template = re.sub(r"{{\s*(.*?)\s*}}", "" if student else r"\1", template, flags=re.DOTALL)
    tags = {
        "%%NAAM%%": student_value("naam"),
        "%%VOORNAAM%%": student_value("voornaam"),
        "%%ROEPNAAM%%": student_value("roepnaam"),
        "%%KLAS%%": student_value("klascode", info.klas),
        "%%KLASLIJST%%": info.klas,
        "%%LEERLINGNUMMER%%": student_value("leerlingnummer"),
        "%%DATUM%%": info.datum,
        "%%LESUUR%%": str(info.lesuur),
        "%%LEERKRACHT%%": info.leerkracht,
        "%%VERVANGER%%": info.vervanger,
        "%%LOCATIE%%": info.locatie,
        "%%STAMLOKAAL%%": info.stamlokaal,
        "%%INFO%%": info.info,
        "%%EXTRA%%": info.extra,
    }
    for tag, value in tags.items():
        template = template.replace(tag, value or "")
    return template

def _staff_receivers(codes):
    receivers = []
    for code in codes:
        staff = dl.staff.get(("code", "=", code))
        if staff and staff.ss_internal_nbr:
            receivers.append({"code": code, "ss_internal_nbr": staff.ss_internal_nbr})
        else:
            log.error(f'{sys._getframe().f_code.co_name}: could not find Smartschool internal number for staff code {code}')
    return receivers

def _message_templates(message_type):
    settings = MESSAGE_SETTINGS.get(message_type, MESSAGE_SETTINGS[MESSAGE_TYPE_AT_HOME])
    return (
        dl.settings.get_configuration_setting(settings["title"]),
        dl.settings.get_configuration_setting(settings["body"]),
    )

def smartschool_message_meta(school=None):
    additional_receivers = dl.settings.get_configuration_setting("smartschool-message-additional-receivers") or {}
    return {
        "additional_receivers": additional_receivers.get(school, []) if school else additional_receivers,
        "additional_receivers_by_school": additional_receivers,
        "variables": MESSAGE_VARIABLES,
        "template_tags": MESSAGE_TEMPLATE_TAGS,
        "templates": {
            MESSAGE_TYPE_AT_HOME: {
                "title": dl.settings.get_configuration_setting("smartschool-message-title-at-home"),
                "body": dl.settings.get_configuration_setting("smartschool-message-body-at-home"),
            },
            MESSAGE_TYPE_TO_HOME: {
                "title": dl.settings.get_configuration_setting("smartschool-message-title-to-home"),
                "body": dl.settings.get_configuration_setting("smartschool-message-body-to-home"),
            },
        }
    }

def send_smartschool_message(infobord_id, message_type=None, subject_template=None, body_template=None, students=None):
    with app.app_context():
        try:
            info = dl.infobord.get([("id", "=", infobord_id)])
            if not info:
                log.error(f'{sys._getframe().f_code.co_name}: could not find infobord row {infobord_id}')
                return
            if not message_type:
                message_type = info.bericht if info.bericht in MESSAGE_SETTINGS else MESSAGE_TYPE_AT_HOME
            if subject_template is None or body_template is None:
                default_subject_template, default_body_template = _message_templates(message_type)
                subject_template = default_subject_template if subject_template is None else subject_template
                body_template = default_body_template if body_template is None else body_template
            additional_receivers_setting = dl.settings.get_configuration_setting("smartschool-message-additional-receivers") or {}
            additional_receiver_codes = [code.strip().upper() for code in additional_receivers_setting.get(info.school, []) if code.strip()]
            additional_receivers = _staff_receivers(additional_receiver_codes)
            enable_sending = dl.settings.get_configuration_setting("smartschool-message-enable-sending")
            if students is None:
                students, error_msg = _students_for_klas(info.klas, info.school)
                if error_msg:
                    log.error(f'{sys._getframe().f_code.co_name}: {error_msg}, infobord {infobord_id}, klas {info.klas}')
                    return
            sender = "csu"
            sent = 0
            first_student_body = ""
            for student in students:
                subject = _replace_message_tags(subject_template, student, info)
                body = _replace_message_tags(body_template, student, info)
                leerlingnummer = student["leerlingnummer"] if isinstance(student, dict) else student.leerlingnummer
                klascode = student["klascode"] if isinstance(student, dict) else student.klascode
                ss_send_message(leerlingnummer, sender, subject, body, 0, enable_sending, f", {klascode}")
                if sent == 0:
                    first_student_body = body
                sent += 1
            subject = _replace_message_tags(subject_template, None, info)
            body = _replace_message_tags(body_template, None, info)
            if not enable_sending:
                body += "<br><br>--------------------------------<br><br>" + first_student_body
            for receiver in additional_receivers:
                ss_send_message(receiver["ss_internal_nbr"], sender, subject, body, 0, True)
                sent += 1
            log.info(f'{sys._getframe().f_code.co_name}: Smartschool message for infobord {infobord_id}, klas {info.klas}, sent {sent}, enable_sending {enable_sending}')
        except Exception as e:
            log.error(f'{sys._getframe().f_code.co_name}: {e}')

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
