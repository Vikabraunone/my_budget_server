import re

from flask import Blueprint, request

from app.exceptions import (
    InvalidEmail,
    RegistrationEmailExists,
    ClientException,
    InvalidLogin,
    UserNotFound)
from app.models import User, db
from app.static.struct_json import *
from app.utils import *

user = Blueprint('user', __name__)

REGEX_EMAIL = re.compile(r'^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$')


@user.route('/register')
def register():
    data = request.json
    try:
        verify_field_json(data, USERNAME, EMAIL, PASSWORD)
        if not re.fullmatch(REGEX_EMAIL, data[EMAIL]):
            raise InvalidEmail(data[EMAIL])
        user = User.query.filter_by(email=data[EMAIL]).first()
        if user:
            raise RegistrationEmailExists(data[EMAIL])
        new_user = User(username=data[USERNAME], email=data[EMAIL], password=data[PASSWORD])
        db.session.add(new_user)
        db.session.commit()
        return {
            USER_ID: new_user.id,
            USERNAME: new_user.username,
            EMAIL: new_user.email,
            PASSWORD: new_user.password
        }
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@user.route('/login')
def login():
    data = request.json
    try:
        verify_field_json(data, EMAIL, PASSWORD)
        user = User.query.filter_by(email=data[EMAIL], password=data[PASSWORD]).first()
        if not user:
            raise InvalidLogin()
        return {
            USER_ID: user.id,
            USERNAME: user.username,
            EMAIL: user.email,
            PASSWORD: user.password
        }
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@user.route('/update')
def update_user():
    data = request.json
    try:
        verify_field_json(data, USER_ID, USERNAME, EMAIL, PASSWORD)
        if not re.fullmatch(REGEX_EMAIL, data[EMAIL]):
            raise InvalidEmail(data[EMAIL])
        user = User.query.filter_by(id=data[USER_ID]).first()
        if not user:
            raise UserNotFound()
        user.username = data[USERNAME]
        user.email = data[EMAIL]
        user.password = data[PASSWORD]
        db.session.add(user)
        db.session.commit()
        return {
            USER_ID: user.id,
            USERNAME: user.username,
            EMAIL: user.email,
            PASSWORD: user.password
        }
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()
