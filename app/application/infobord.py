from app import data as dl, socketio
from app.application.smartschool import send_message as ss_send_message
import sys, datetime, re, yaml

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app

log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

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
        # send-ss-message specific, when "bericht" is set for the first time, send a message to
        # the students and additional receivers (staff)
        message_jobs = []
        for item in data:
            if "id" not in item or "bericht" not in item or item["bericht"] is not True:
                continue
            current = dl.infobord.get([("id", "=", item["id"])])
            if current and not current.bericht:
                message_jobs.append(current.id)
        ret = dl.infobord.update_m(data)
        for infobord_id in message_jobs:
            socketio.start_background_task(send_smartschool_message, infobord_id)
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def _additional_receiver_codes(value):
    try:
        if isinstance(value, list):
            codes = value
        else:
            parsed = yaml.safe_load(value or "")
            if isinstance(parsed, list):
                codes = parsed
            elif parsed:
                codes = re.split(r"[\n,;]+", str(parsed))
            else:
                codes = []
        return [str(item).strip().upper() for item in codes if str(item).strip()]
    except yaml.YAMLError as e:
        log.error(f'{sys._getframe().f_code.co_name}: invalid YAML, {e}')
        return []

def _get_klas_tokens(klas):
    tokens = set()
    for part in re.split(r";+", klas or ""):
        part = part.strip()
        if not part:
            continue
        pieces = part.split(" ", 1)
        if len(pieces) == 1:
            tokens.add(pieces[0].strip())
            continue
        klasgroep, klassen = pieces
        for klascode in re.split(r",+", klassen):
            klascode = klascode.strip()
            if klascode:
                tokens.add(klascode)
    return tokens

def _students_for_klas(klas):
    tokens = _get_klas_tokens(klas)
    students = []
    seen = set()
    for token in tokens:
        token_students = dl.student.get_m([("klascode", "=", token)])
        if not token_students:
            token_students = [student for student in dl.student.get_m() if student.klascode.startswith(token)]
        for student in token_students:
            if student.leerlingnummer not in seen:
                students.append(student)
                seen.add(student.leerlingnummer)
    return students

def _replace_message_tags(template, student, info):
    tags = {
        "%%NAAM%%": student.naam if student else "",
        "%%VOORNAAM%%": student.voornaam if student else "",
        "%%ROEPNAAM%%": student.roepnaam if student else "",
        "%%KLAS%%": student.klascode if student else info.klas,
        "%%LEERLINGNUMMER%%": student.leerlingnummer if student else "",
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

def send_smartschool_message(infobord_id):
    with app.app_context():
        try:
            info = dl.infobord.get([("id", "=", infobord_id)])
            if not info:
                log.error(f'{sys._getframe().f_code.co_name}: could not find infobord row {infobord_id}')
                return
            subject_template = dl.settings.get_configuration_setting("smartschool-message-title")
            body_template = dl.settings.get_configuration_setting("smartschool-message-body")
            additional_receivers = _staff_receivers(_additional_receiver_codes(dl.settings.get_configuration_setting("smartschool-message-additional-receivers")))
            enable_sending = dl.settings.get_configuration_setting("smartschool-message-enable-sending")
            students = _students_for_klas(info.klas)
            sender = "csu"
            sent = 0
            for student in students:
                subject = _replace_message_tags(subject_template, student, info)
                body = _replace_message_tags(body_template, student, info)
                ss_send_message(student.leerlingnummer, sender, subject, body, 0, enable_sending, f", {student.klascode}")
                sent += 1
            subject = _replace_message_tags(subject_template, None, info)
            body = _replace_message_tags(body_template, None, info)
            for receiver in additional_receivers:
                receiver_enable_sending = True if receiver["code"].lower() == "boro" else enable_sending
                ss_send_message(receiver["ss_internal_nbr"], sender, subject, body, 0, receiver_enable_sending)
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
