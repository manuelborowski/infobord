from app import db
from sqlalchemy import text, desc, func
import sys, datetime

#logging on file level
import logging
from app import MyLogFilter, top_log_handle, app
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

def commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def add_single(model, data={}, commit=True, timestamp=False):
    try:
        obj = model()
        for k, v in data.items():
            if hasattr(obj, k):
                if getattr(model, k).expression.type.python_type == type(v):
                    setattr(obj, k, v.strip() if isinstance(v, str) else v)
        if timestamp:
            obj.timestamp = datetime.datetime.now()
        db.session.add(obj)
        if commit:
            db.session.commit()
        return obj
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def add_multiple(model, data=[], timestamp=False):
    try:
        objs = []
        for d in data:
            objs.append(add_single(model, d, commit=False, timestamp=timestamp))
        db.session.commit()
        return objs
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return []


def update_single(model, data={}, commit=True, timestamp=False):
    try:
        if "obj" in data:
            obj = data["obj"]
            del (data["obj"])
        elif "id" in data:
            obj = model.query.filter(model.id == data["id"]).first()
            del (data["id"])
        else:
            return None
        for k, v in data.items():
            if hasattr(obj, k):
                if type(getattr(obj, k)) == type(v):
                        setattr(obj, k, v.strip() if isinstance(v, str) else v)
        if timestamp:
            obj.timestamp = datetime.datetime.now()
        if commit:
            db.session.commit()
        return obj
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def update_multiple(model, data = [], timestamp=False):
    try:
        for d in data:
            update_single(model, d, commit=False, timestamp=timestamp)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def delete_multiple(model, ids=[], objs=[]):
    try:
        if objs:
            for obj in objs:
                db.session.delete(obj)
        if ids:
            objs = model.query.filter(model.id.in_(ids)).all()
            for obj in objs:
                db.session.delete(obj)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


# filters is list of tupples: [(key, operator, value), ...]
def get_multiple(model, filters=[], fields=[], order_by=None, first=False, count=False, active=True, start=None, stop=None):
    try:
        tablename = model.__tablename__
        entities = [text(f'{tablename}.{f}') for f in fields]
        if entities:
            q = model.query.with_entities(*entities)
            if not filters: # hack.  If no filter is defined, the query errors with 'unknown table'
                q = q.filter(getattr(model, "id") > 0)
        else:
            q = model.query
        if type(filters) is not list: filters = [filters]
        for k, o, v in filters:
            if hasattr(model, k):
                if o == '!':
                    q = q.filter(getattr(model, k) != v)
                elif o == '>':
                    q = q.filter(getattr(model, k) > v)
                elif o == '<':
                    q = q.filter(getattr(model, k) < v)
                elif o == '>=':
                    q = q.filter(getattr(model, k) >= v)
                elif o == '<=':
                    q = q.filter(getattr(model, k) <= v)
                elif o == 'l':
                    q = q.filter(getattr(model, k).like(f"%{v}%"))
                elif o == 'c=':
                    q = q.filter(func.binary(getattr(model, k)) == v)
                else:
                    q = q.filter(getattr(model, k) == v)
        if order_by:
            if order_by[0] == '-':
                q = q.order_by(desc(getattr(model, order_by[1::])))
            else:
                q = q.order_by(getattr(model, order_by))
        else:
            q = q.order_by(getattr(model, "id"))
        if active is not None and hasattr(model, "active"):
            q = q.filter(model.active == active)
        if start is not None and stop is not None:
            q = q.slice(start, stop)
        if first:
            obj = q.first()
            return obj
        if count:
            return q.count()
        objs = q.all()
        return objs
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise e


def get_first_single(model, filters=[], order_by=None):
    try:
        obj = get_multiple(model, filters, order_by=order_by, first=True)
        return obj
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None
