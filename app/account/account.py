from flask import Blueprint, request, jsonify
import uuid
import hashlib

from app.exceptions import (
    ClientException,
    DatabaseEntryExists,
    DatabaseEntryNotFound)
from app.models import Account, db
from app.static.struct_json import (
    USER_ID,
    ACCOUNT_ID,
    ACCOUNT_NAME,
    AMOUNT, KEY_SUCCESS)
from app.utils import *

account = Blueprint('account', __name__)


@account.route('/create')
def create():
    data = request.json
    try:
        verify_field_json(data, USER_ID, ACCOUNT_NAME, AMOUNT)
        account = Account.query.filter_by(user_id=data[USER_ID], account_name=data[ACCOUNT_NAME]).first()
        if account:
            raise DatabaseEntryExists(account, data[ACCOUNT_NAME])
        new_account = Account(user_id=data[USER_ID], account_name=data[ACCOUNT_NAME], amount=data[AMOUNT])
        db.session.add(new_account)
        db.session.commit()
        return {KEY_SUCCESS: 'Счет успешно создан.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@account.route('/update')
def update():
    data = request.json
    try:
        verify_field_json(data, USER_ID, ACCOUNT_ID, ACCOUNT_NAME, AMOUNT)
        account = Account.query.filter_by(id=data[ACCOUNT_ID], user_id=data[USER_ID]).first()
        if not account:
            raise DatabaseEntryNotFound(db_table=Account)
        account.account_name = data[ACCOUNT_NAME]
        account.amount = data[AMOUNT]
        db.session.add(account)
        db.session.commit()
        return {KEY_SUCCESS: 'Счет успешно изменен.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@account.route('/delete')
def delete():
    data = request.json
    try:
        verify_field_json(data, USER_ID, ACCOUNT_ID)
        account = Account.query.filter_by(id=data[ACCOUNT_ID], user_id=data[USER_ID]).first()
        if not account:
            raise DatabaseEntryNotFound(db_table=Account)
        db.session.delete(account)
        db.session.commit()
        return {KEY_SUCCESS: 'Счет успешно удален.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@account.route('/get')
def get():
    data = request.json
    try:
        verify_field_json(data, USER_ID)
        return read_accounts(data[USER_ID])
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


def read_accounts(user_id):
    try:
        query_accounts = Account.query.filter_by(user_id=user_id).order_by(Account.account_name)
        accounts = []
        for account in query_accounts:
            accounts.append({
                ACCOUNT_ID: account.id,
                ACCOUNT_NAME: account.account_name,
                AMOUNT: account.amount
            })
        return jsonify(accounts)
    except Exception:
        raise


def hash_password(password):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt


def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()
