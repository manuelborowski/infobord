__all__ = ["user", "datatables", "common", "settings", "cron", "socketio", "formio", "staff", "schoolschedule", "models", "infobord", "student", "smartschool"]

import app.application.user
import app.application.datatables
import app.application.common
import app.application.settings
import app.application.socketio
import app.application.formio
import app.application.staff
import app.application.schoolschedule
import app.application.models
import app.application.infobord
import app.application.student
import app.application.smartschool

from app.application.staff import staff_load_from_sdh
from app.application.schoolschedule import schedule_load_from_sdh
from app.application.student import student_load_from_sdh

# tag, cront-task, label, help
cron_table = [
    ('SDH-STAFF-UPDATE', staff_load_from_sdh, 'VAN SDH, upload personeel', ''),
    ('SDH-SCHEDULE-UPDATE', schedule_load_from_sdh, 'VAN SDH, upload lesrooster', ''),
    ('SDH-STUDENT-UPDATE', student_load_from_sdh, 'VAN SDH, upload leerlingen', ''),
]

import app.application.cron
