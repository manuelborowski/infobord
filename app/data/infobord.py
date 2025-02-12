import sys
import app.data.models
from app import db
from sqlalchemy_serializer import SerializerMixin


class Infobord(db.Model, SerializerMixin):
    __tablename__ = 'inforbords'

    date_format = '%Y/%m/%d'
    datetime_format = '%Y/%m/%d %H:%M'

    id = db.Column(db.Integer(), primary_key=True)
    school = db.Column(db.String(256), default='')
    volgnummer = db.Column(db.Integer(), default=0)
    lesuur = db.Column(db.Integer(), default=0)
    leerkracht = db.Column(db.String(256), default='')
    vervanger = db.Column(db.String(256), default='')
    klas = db.Column(db.String(256), default='')
    locatie = db.Column(db.String(256), default='')
    info = db.Column(db.String(256), default='')
    extra = db.Column(db.String(256), default='')
    datum = db.Column(db.String(256), default='')

    active = db.Column(db.Boolean, default=True)    # long term

    @property
    def person_id(self):
        return self.leerlingnummer

def commit():
    return app.data.models.commit()


def add(data={}, commit=True):
    return app.data.models.add_single(Infobord, data, commit)


def add_m(data=[]):
    return app.data.models.add_multiple(Infobord, data)


def update(Infobord, data={}, commit=True):
    return app.data.models.update_single(Infobord, Infobord, data, commit)


def update_m(data=[]):
    return app.data.models.update_multiple(Infobord, data)


def delete_m(ids=[], objs=[]):
    return app.data.models.delete_multiple(Infobord, ids, objs)


def get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Infobord, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def get(filters=[]):
    return app.data.models.get_first_single(Infobord, filters)