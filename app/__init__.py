import logging.handlers, os, sys
from flask import Flask, abort
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_jsglue import JSGlue
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from werkzeug.routing import IntegerConverter
from functools import wraps

#Warning: update flask_jsglue.py: from markupsafe import Markup

# 0.1 clone from laptop incident systeem 0.70
# 0.2 able to add vervaningen
# 0.3: gebruikers can only view
# 0.4: added viewer
# 0.5: multiple days
# 0.6: added preview button.  Small bugfixes.  Remove date and logo from view
# 0.7: added favicon
# 0.8: view depends on lesuur (passed are not visible)
# 0.9: small bugfix
# 0.10: implemented vervangers
# 0.11: small updates
# 0.12: esthetic updates
# 0.13: added more dates to select from
# 0.14: updated preview so that future rosters can be displayed

version = "0.14"

app = Flask(__name__, instance_relative_config=True, template_folder='presentation/template/')

#  enable logging
top_log_handle = "IB"
log = logging.getLogger(f"{top_log_handle}.{__name__}")
# support custom filtering while logging
class MyLogFilter(logging.Filter):
    def filter(self, record):
        record.username = current_user.username if current_user and current_user.is_active else 'NONE'
        return True
LOG_FILENAME = os.path.join(sys.path[0], f'log/ib.txt')
log_level = getattr(logging, 'INFO')
log.setLevel(log_level)
log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info("START Infobord")

from app.config import app_config
config_name = os.getenv('FLASK_CONFIG')
config_name = config_name if config_name else 'production'
app.config.from_object(app_config[config_name])
app.config.from_pyfile('config.py')

jsglue = JSGlue(app)
db = SQLAlchemy()
login_manager = LoginManager()
db.app = app  #  hack:-(
db.init_app(app)
migrate = Migrate(app, db)

app.url_map.converters['int'] = IntegerConverter
login_manager.init_app(app)
login_manager.login_message = 'Je moet aangemeld zijn om deze pagina te zien!'
login_manager.login_view = 'auth.login'

socketio = SocketIO(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'], cors_allowed_origins="*")


def create_admin():
    with app.app_context():
        try:
            from app.data.user import User
            find_admin = User.query.filter(User.username == 'admin').first()
            if not find_admin:
                admin = User(username='admin', password='admin', level=5, user_type=User.USER_TYPE.LOCAL)
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error(f'{sys._getframe().f_code.co_name}: {e}')

create_admin()

SCHEDULER_API_ENABLED = True
ap_scheduler = APScheduler()
ap_scheduler.init_app(app)
ap_scheduler.start()

# decorator to grant access to admins only
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_at_least_admin:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


# decorator to grant access to at least supervisors
def supervisor_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_at_least_supervisor:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


# Should be last to avoid circular import
from app.presentation.view import auth, user, settings, infobord
app.register_blueprint(auth.bp_auth)
app.register_blueprint(user.bp_user)
app.register_blueprint(settings.bp_settings)
app.register_blueprint(infobord.bp_infobord)
