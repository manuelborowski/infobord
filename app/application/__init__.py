__all__ = ["user", "datatables", "common", "settings", "cron", "socketio", "formio", "staff"]

import app.application.user
import app.application.datatables
import app.application.common
import app.application.settings
import app.application.socketio
import app.application.formio
import app.application.staff

from app.application.staff import staff_load_from_sdh

# tag, cront-task, label, help
cron_table = [
    ('SDH-STAFF-UPDATE', staff_load_from_sdh, 'VAN SDH, upload personeel', ''),
]

import app.application.cron