from flask import Blueprint, request

from app.exceptions import DatabaseEntryExists, DatabaseEntryNotFound, ClientException
from app.models import db, Product, Subcategory
from app.static.struct_json import *
from app.utils import *

product = Blueprint('product', __name__)


@product.route('/create')
def create():
    data = request.json
    try:
        if create_product(data):
            return {KEY_SUCCESS: 'Товар успешно создан.'}
        raise {KEY_ERROR: 'Товар не удалось создать.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


def create_product(data):
    try:
        verify_field_json(data, SUBCATEGORY_ID, PRODUCT_NAME, PRODUCT_COMMENT)
        subcategory = Subcategory.query.filter_by(id=data[SUBCATEGORY_ID]).first()
        if not subcategory:
            raise DatabaseEntryNotFound(db_table=Subcategory)

        product = Product.query.filter_by(subcategory_id=data[SUBCATEGORY_ID], product_name=data[PRODUCT_NAME]).first()
        if product:
            raise DatabaseEntryExists(product, data[ACCOUNT_NAME])

        new_product = Product(product_name=data[PRODUCT_NAME], comment=data[PRODUCT_COMMENT])
        db.session.add(new_product)
        db.session.flush()

        subcategory.products.append(new_product)
        db.session.add(subcategory)
        db.session.commit()
        return new_product
    except Exception:
        raise


@product.route('/update')
def update():
    data = request.json
    try:
        verify_field_json(data, PRODUCT_ID, SUBCATEGORY_ID, PRODUCT_NAME, PRODUCT_COMMENT)
        new_subcategory = Subcategory.query.filter_by(id=data[SUBCATEGORY_ID]).first()
        if not new_subcategory:  # если категория не найдена
            raise DatabaseEntryNotFound(db_table=Subcategory)

        product = Product.query.filter_by(id=data[PRODUCT_ID]).first()
        if not product:
            raise DatabaseEntryNotFound(db_table=Product)

        if product.product_name != data[PRODUCT_NAME]:  # если изменилось название, проверяем, есть ли такой же товар
            same_product = Product.query.filter_by(product_name=data[PRODUCT_NAME],
                                                   subcategory_id=data[SUBCATEGORY_ID]).first()
            if same_product:
                raise DatabaseEntryExists(db_table=Product, name=data[PRODUCT_NAME])

        # изменяем подкатегорию
        if product.subcategory_id != new_subcategory.id:  # если изменилась категория товара
            old_subcategory = product.subcategory
            old_subcategory.products.remove(product)  # удаляем из старой подкатегории товар
            new_subcategory.product.append(product)  # добавляем в новую подкатегорию товар
            db.session.add_all([old_subcategory, new_subcategory])
            db.session.flush()
        product.product_name = data[PRODUCT_NAME]
        product.comment = data[PRODUCT_COMMENT]

        db.session.add(product)
        db.session.commit()
        return {KEY_SUCCESS: 'Товар успешно изменен.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


@product.route('/delete')
def delete():
    data = request.json
    try:
        verify_field_json(data, PRODUCT_ID)
        product = Product.query.filter_by(id=data[PRODUCT_ID]).first()
        if not product:
            raise DatabaseEntryNotFound(db_table=Product)
        db.session.delete(product)
        db.session.commit()
        return {KEY_SUCCESS: 'Товар успешно удален.'}
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()


@product.route('/get')
def get():
    data = request.json
    try:
        verify_field_json(data, SUBCATEGORY_ID)
        query_products = Product.query.filter_by(subcategory_id=data[SUBCATEGORY_ID])
        response = []
        for qp in query_products:
            product = {
                PRODUCT_ID: qp.id,
                SUBCATEGORY_ID: qp.id,
                PRODUCT_NAME: qp.product_name,
                PRODUCT_COMMENT: qp.comment
            }
            response.append(product)
        return response
    except ClientException as e:
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()
