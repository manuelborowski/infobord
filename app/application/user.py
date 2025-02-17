from werkzeug.security import generate_password_hash, check_password_hash
import sys, qrcode, secrets, base64, io
from app import data as dl
from flask import request

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def add(data):
    try:
        user = dl.user.get(('username', "=", data['username']))
        if user:
            log.error(f'Error, user {user.username} already exists')
            return {"status": "warning", "msg": f'Fout, gebruiker "{user.username}" bestaat al'}
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data['password'])
        user = dl.user.add(data)
        data = {k: v for k, v in data.items() if k not in ('username', 'password', 'password_hash')}
        log.info(f"Add user: {data}")
        return {"status": "ok", "msg": f"Gebruiker, {user.username} toegevoegd."}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": str(e)}


def update(data):
    try:
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data['password'])
        user = dl.user.update(data)
        if user:
            data = {k: v for k, v in data.items() if k not in ('username', 'password', 'password_hash')}
            log.info(f"Update user: {data}")
            return {"status": "ok", "msg": f"Gebruiker, {user.username} aangepast."}
        return {"status": "warning", "msg": f"Gebruiker met id {data['id']} bestaat niet"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": str(e)}


def delete(ids):
    try:
        dl.user.delete(ids)
        return {"status": "ok", "msg": "Gebruikers zijn verwijderd"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": str(e)}


def get(data):
    try:
        filter = None
        if "id" in data:
            filter = ("id", "=", data['id'])
        if "rfid" in data:
            filter = ("rfid", "=", data['rfid'])
        if filter:
            user = dl.user.get(filter)
            if user:
                return {"data": user.to_dict()}
            else:
                return {"status": "error", "msg": f"User not found, filter {filter}"}
        else:
            return {"status": "error", "msg": f"No valid data {data}"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {data}, {e}')
        return {"status": "error", "msg": {str(e)}}

def login_url_generate(user):
    try:
        url_token = secrets.token_urlsafe(32)
        user.url_token = url_token
        dl.user.commit()
        return url_token
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return None

def qr_get(user, new_qr=False):
    try:
        if new_qr: user.url_token = None
        url_token = user.url_token if user.url_token else login_url_generate(user)
        url = f"{request.root_url}m/{url_token}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4, )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        return {"qr": img_base64}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": {str(e)}}

############ user overview list #########
def format_data(db_list, total_count=None, filtered_count=None):
    out = []
    for i in db_list:
        em = i.to_dict()
        em.update({"row_action": i.id, "DT_RowId": i.id})
        out.append(em)
    return  total_count, filtered_count, out

