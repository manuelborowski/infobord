from email.policy import default
from app import db
from sqlalchemy_serializer import SerializerMixin
from app import data as dl

#logging on file level
import logging, sys
from app import MyLogFilter, top_log_handle, app
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


class Incident(db.Model, SerializerMixin):
    __tablename__ = 'incidents'

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M'

    id = db.Column(db.Integer, primary_key=True)
    lis_badge_id = db.Column(db.Integer, default=-1)
    priority = db.Column(db.Integer, default=1)
    laptop_owner_name = db.Column(db.String(256), default=None)
    laptop_owner_id = db.Column(db.String(256), default=None)
    laptop_owner_password = db.Column(db.String(256), default=None)
    laptop_owner_password_default = db.Column(db.Boolean, default=False)
    laptop_type = db.Column(db.String(256), default=None)
    laptop_name = db.Column(db.String(256), default=None)
    laptop_serial = db.Column(db.String(256), default=None)
    spare_laptop_name = db.Column(db.String(256), default=None)
    spare_laptop_serial = db.Column(db.String(256), default=None)
    charger = db.Column(db.Boolean, default=False)
    info = db.Column(db.String(256), default=None)
    incident_type = db.Column(db.String(256), default=None)
    drop_damage = db.Column(db.Boolean, default=False)
    water_damage = db.Column(db.Boolean, default=False)
    incident_state = db.Column(db.String(256), default=None)
    location = db.Column(db.String(256), default=None)
    incident_owner = db.Column(db.String(256), default=None)
    time = db.Column(db.DateTime, default=None)

def add(data = {}):
    return dl.models.add_single(Incident, data)


def update(incident, data={}):
    return dl.models.update_single(Incident, incident, data)


def get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return dl.models.get_multiple(Incident, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def get(filters=[]):
    return dl.models.get_first_single(Incident, filters)


def delete(ids=None):
    return dl.models.delete_multiple(Incident, ids=ids)


def commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

############ incident overview list #########
def filter(query_in):
    return query_in

def pre_sql_query():
    return db.session.query(Incident)


def pre_sql_filter(query, filters):
    for f in filters:
        if f['id'] == 'incident-type':
            if f['value'] != 'all':
                query = query.filter(Incident.incident_type == f['value'])
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Incident.id.like(search_string))
    search_constraints.append(Incident.incident_owner.like(search_string))
    search_constraints.append(Incident.lis_badge_id.like(search_string))
    search_constraints.append(Incident.laptop_owner_name.like(search_string))
    search_constraints.append(Incident.laptop_name.like(search_string))
    return search_constraints




