import sys
import app.data.models
from app import db
from sqlalchemy_serializer import SerializerMixin


class ExtraInfo(db.Model, SerializerMixin):
    __tablename__ = 'extra_infos'

    date_format = '%Y/%m/%d'
    datetime_format = '%Y/%m/%d %H:%M'

    id = db.Column(db.Integer(), primary_key=True)
    lesuur = db.Column(db.Integer(), default=0)
    location = db.Column(db.String(256), default='')
    school = db.Column(db.String(256), default='')
    info = db.Column(db.String(4096), default='')
    staff = db.Column(db.String(256), default='')

    @property
    def person_id(self):
        return self.leerlingnummer

def commit():
    return app.data.models.commit()


def add(data={}, commit=True):
    return app.data.models.add_single(ExtraInfo, data, commit)


def add_m(data=[]):
    return app.data.models.add_multiple(ExtraInfo, data)


def update(data={}, commit=True):
    return app.data.models.update_single(ExtraInfo, data, commit)


def update_m(data=[]):
    return app.data.models.update_multiple(ExtraInfo, data)


def delete_m(ids=[], objs=[]):
    return app.data.models.delete_multiple(ExtraInfo, ids, objs)


def get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(ExtraInfo, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def get(filters=[]):
    return app.data.models.get_first_single(ExtraInfo, filters)