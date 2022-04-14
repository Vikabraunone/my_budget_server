from flask import Blueprint, request, jsonify

from app.exceptions import DatabaseEntryExists, ClientException, DatabaseEntryNotFound, UserNotFound
from app.models import db, User, Category, Subcategory
from app.static.struct_json import (
    USER_ID,
    CATEGORY_ID,
    CATEGORY_NAME, KEY_SUCCESS, SUBCATEGORY_NAME, SUBCATEGORY_ID, SUBCATEGORIES)
from app.utils import *

category = Blueprint('category', __name__)
subcategory = Blueprint('subcategory', __name__)


@category.route('/create')
def create():
    data = request.json
    try:
        create_category(data)
        return {KEY_SUCCESS: 'Категория успешно добавлена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


def create_category(data):
    try:
        verify_field_json(data, USER_ID, CATEGORY_NAME)
        user = User.query.filter_by(id=data[USER_ID]).first()
        if not user:
            raise UserNotFound()
        category = Category.query.filter_by(user_id=data[USER_ID], category_name=data[CATEGORY_NAME]).first()
        if category:
            raise DatabaseEntryExists(db_table=Category, name=data[CATEGORY_NAME])

        new_subcategory = Subcategory(subcategory_name='Другое')
        db.session.add(new_subcategory)
        db.session.flush()

        new_category = Category(category_name=data[CATEGORY_NAME])
        new_category.subcategories.append(new_subcategory)
        db.session.add(new_category)
        db.session.flush()

        user.categories.append(new_category)
        db.session.add(user)
        db.session.commit()
        return new_category
    except Exception:
        raise


@category.route('/update')
def update():
    data = request.json
    try:
        verify_field_json(data, USER_ID, CATEGORY_ID, CATEGORY_NAME)
        user = User.query.filter_by(id=data[USER_ID]).first()
        if not user:
            raise UserNotFound()
        upd_category = Category.query.filter_by(id=data[CATEGORY_ID], user_id=data[USER_ID]).first()
        if not upd_category:
            raise DatabaseEntryNotFound(db_table=Category)
        same_category = Category.query.filter_by(user_id=data[USER_ID], category_name=data[CATEGORY_NAME]).first()
        if same_category:
            raise DatabaseEntryExists(db_table=Category, name=data[CATEGORY_NAME])
        upd_category.category_name = data[CATEGORY_NAME]
        db.session.add(upd_category)
        db.session.commit()
        return {KEY_SUCCESS: 'Категория успешно изменена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@category.route('/delete')
def delete():
    data = request.json
    try:
        verify_field_json(data, USER_ID, CATEGORY_ID)
        user = User.query.filter_by(id=data[USER_ID]).first()
        if not user:
            raise UserNotFound()
        category = Category.query.filter_by(id=data[CATEGORY_ID], user_id=data[USER_ID]).first()
        if not category:
            raise DatabaseEntryNotFound(db_table=Category)
        db.session.delete(category)
        db.session.commit()
        return {KEY_SUCCESS: 'Категория успешно удалена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@category.route('/get')
def get():
    data = request.json
    try:
        verify_field_json(data, USER_ID)
        return read(data[USER_ID]), 404
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


def read(user_id):
    try:
        query_categories = Category.query.filter_by(user_id=user_id).order_by(Category.category_name)
        response = []
        for qc in query_categories:
            subcategories = Subcategory.query.filter(Subcategory.category_id == qc.id) \
                .order_by(Subcategory.subcategory_name)
            category = {
                CATEGORY_ID: qc.id,
                CATEGORY_NAME: qc.category_name,
                SUBCATEGORIES: [
                    {
                        SUBCATEGORY_ID: s.id,
                        SUBCATEGORY_NAME: s.subcategory_name
                    }
                    for s in subcategories]
            }
            response.append(category)
        return jsonify(response)
    except Exception:
        raise


@subcategory.route('/create')
def create_subcategory():
    data = request.json
    try:
        create_subcategory_data(data)
        return {KEY_SUCCESS: 'Подкатегория успешно добавлена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


def create_subcategory_data(data):
    try:
        verify_field_json(data, CATEGORY_ID, SUBCATEGORY_NAME)
        category = Category.query.filter_by(id=data[CATEGORY_ID]).first()
        if not category:
            raise DatabaseEntryNotFound(db_table=Category)
        subcategory = Subcategory.query.filter_by(subcategory_name=data[SUBCATEGORY_NAME],
                                                  category_id=data[CATEGORY_ID]).first()
        if subcategory:
            raise DatabaseEntryExists(db_table=Subcategory, name=data[SUBCATEGORY_NAME])
        new_subcategory = Subcategory(subcategory_name=data[SUBCATEGORY_NAME])
        db.session.add(new_subcategory)
        db.session.flush()
        category.subcategories.append(new_subcategory)
        db.session.add(category)
        db.session.commit()
        return new_subcategory
    except Exception:
        raise



@subcategory.route('/update')
def update_subcategory():
    data = request.json
    try:
        verify_field_json(data, CATEGORY_ID, SUBCATEGORY_ID, SUBCATEGORY_NAME)
        new_category = Category.query.filter_by(id=data[CATEGORY_ID]).first()
        if not new_category:
            raise DatabaseEntryNotFound(db_table=Category)
        subcategory = Subcategory.query.filter_by(id=data[SUBCATEGORY_ID]).first()
        if not subcategory:
            raise DatabaseEntryNotFound(db_table=Subcategory)
        if subcategory.subcategory_name != data[SUBCATEGORY_NAME]:  # если разные названия
            upd_subcategory = Subcategory.query.filter_by(subcategory_name=data[SUBCATEGORY_NAME],
                                                          category_id=data[CATEGORY_ID]).first()
            if upd_subcategory:
                raise DatabaseEntryExists(db_table=Subcategory, name=data[SUBCATEGORY_NAME])

        if subcategory.category_id != new_category.id:
            old_category = subcategory.category
            old_category.subcategories.remove(subcategory)
            new_category.subcategories.append(subcategory)
            db.session.add_all([new_category, new_category])
            db.session.flush()
        subcategory.subcategory_name = data[SUBCATEGORY_NAME]
        db.session.add(subcategory)
        db.session.commit()
        return {KEY_SUCCESS: 'Подкатегория успешно изменена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


@subcategory.route('/delete')
def delete_subcategory():
    data = request.json
    try:
        verify_field_json(data, SUBCATEGORY_ID)
        subcategory = Subcategory.query.filter_by(id=data[SUBCATEGORY_ID]).first()
        if not subcategory:
            raise DatabaseEntryNotFound(db_table=Subcategory)
        db.session.delete(subcategory)
        db.session.commit()
        return {KEY_SUCCESS: 'Подкатегория успешно удалена.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()
