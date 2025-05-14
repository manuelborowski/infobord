from app import db
import app.data.models
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import desc

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


class Schedule(db.Model, SerializerMixin):
    __tablename__ = 'schoolschedule'

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M'

    id = db.Column(db.Integer(), primary_key=True)
    klascode = db.Column(db.String(256), default='')
    vak = db.Column(db.String(256), default='')
    leerkracht = db.Column(db.String(256), default='')
    lokaal = db.Column(db.String(256), default='')
    coteaching = db.Column(db.Boolean(), default=False)
    dag = db.Column(db.Integer(), default=0)
    lestijd = db.Column(db.Integer(), default=0)
    school = db.Column(db.String(256), default='')

def commit():
    return app.data.models.commit()

def add_obj(obj):
    return db.session.add(obj)

def add(data = {}, commit=True):
    obj = app.data.models.add_single(Schedule, data, commit)
    return obj


def add_m(data = []):
    return app.data.models.add_multiple(Schedule, data)


def update(obj, data={}, commit=True):
    return app.data.models.update_single(Schedule, obj, data, commit)


def delete_m(ids=[], objs=[]):
    return app.data.models.delete_multiple(Schedule, ids, objs)

def truncate():
    return app.data.models.truncate(Schedule)

def get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Schedule, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def get(filters=[]):
    return app.data.models.get_first_single(Schedule, filters)


def get_periods(school=None):
    if school:
        return db.session.query(Schedule.start, Schedule.end).filter(Schedule.school == school).distinct().order_by(desc(Schedule.start)).all()
    return db.session.query(Schedule.school, Schedule.start, Schedule.end).distinct().order_by(Schedule.start).all()



############ schedule overview list #########
def pre_sql_query():
    return db.session.query(Schedule).filter(Schedule.active == True)


def pre_sql_filter(query, filter):
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Schedule.naam.like(search_string))
    search_constraints.append(Schedule.voornaam.like(search_string))
    search_constraints.append(Schedule.code.like(search_string))
    return search_constraints


