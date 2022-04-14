import datetime
import decimal

from flask import Blueprint, request, jsonify

from app.exceptions import DatabaseEntryNotFound, ClientException
from app.models import db, Product, Cheque, Account, ProductCheque
from app.product.product import create_product
from app.static.struct_json import *
from app.utils import *

cheque = Blueprint('cheque', __name__)


@cheque.route('/create')
def create():
    data = request.json
    try:
        verify_field_json(data, ACCOUNT_ID, CHEQUE_NAME, CHEQUE_SUM, POSITIVE_CHEQUE, CHEQUE_DATE,
                          CHEQUE_COMMENT, PRODUCTS)
        cheque = Cheque(cheque_name=data[CHEQUE_NAME], sum=data[CHEQUE_SUM], positive_cheque=data[POSITIVE_CHEQUE],
                        date=data[CHEQUE_DATE], comment=data[CHEQUE_COMMENT])
        db.session.add(cheque)
        db.session.flush()

        account = Account.query.filter_by(id=data[ACCOUNT_ID]).first()
        if not account:
            raise DatabaseEntryNotFound(db_table=Account)
        if data[POSITIVE_CHEQUE]:
            account.amount += decimal.Decimal(cheque.sum)
        else:
            account.amount -= decimal.Decimal(cheque.sum)
        account.cheques.append(cheque)
        db.session.add(account)
        db.session.flush()

        products = data[PRODUCTS]
        for product_data in products:
            product = Product.query.filter_by(id=product_data[PRODUCT_ID]).first()
            if not product:
                raise DatabaseEntryNotFound(db_table=Product)
            product_cheque = ProductCheque(cost=product_data[PRODUCT_COST], count=product_data[PRODUCT_COUNT])
            cheque.cheque_products.append(product_cheque)
            product.cheque_products.append(product_cheque)
            db.session.add_all([cheque, product])
            db.session.flush()
        db.session.commit()
        return {KEY_SUCCESS: 'Чек успешно создан.'}
    except ClientException as e:
        db.session.rollback()
        log_client_error(e, data)
        return create_response_client_error(e)
    except Exception as e:
        db.session.rollback()
        log_server_error(e, data)
        return create_response_error_server()


@cheque.route('/get')
def get():
    data = request.json
    try:
        verify_field_json(data, POSITIVE_CHEQUE, DATE_FROM, DATE_TO)
        date_from = datetime.datetime.strptime(data[DATE_FROM], '%d.%m.%Y').date()
        date_to = datetime.datetime.strptime(data[DATE_TO], '%d.%m.%Y').date()
        cheques = Cheque.query.filter(Cheque.positive_cheque == data[POSITIVE_CHEQUE],
                                      Cheque.date >= date_from, Cheque.date <= date_to).order_by(Cheque.date)
        result = []
        for cheque in cheques:
            products = []
            for cp in cheque.cheque_products:
                products.append(
                    {
                        PRODUCT_ID: cp.product.id,
                        PRODUCT_NAME: cp.product.product_name,
                        PRODUCT_COMMENT: cp.product.comment,
                        PRODUCT_COST: cp.cost,
                        PRODUCT_COUNT: cp.count,
                        SUBCATEGORY_NAME: cp.product.subcategory.subcategory_name,
                        CATEGORY_NAME: cp.product.subcategory.category.category_name
                    })
            result.append({
                CHEQUE_ID: cheque.id,
                CHEQUE_NAME: cheque.cheque_name,
                CHEQUE_DATE: str(cheque.date),
                CHEQUE_COMMENT: cheque.comment,
                ACCOUNT_NAME: cheque.account.account_name,
                PRODUCTS: products
            })
        return jsonify(result)
    except Exception as e:
        log_server_error(e, data)
        return create_response_error_server()
