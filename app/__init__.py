from flask import Flask, g, current_app
from flask_sqlalchemy import SQLAlchemy

from .account.account import account
from .category.category import category, subcategory
from .cheque.auto_cheque import auto_cheque
from .cheque.cheque import cheque
from .extensions import db
from .user.user import user


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    db.init_app(app)

    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(account, url_prefix='/account')
    app.register_blueprint(category, url_prefix='/category')
    app.register_blueprint(subcategory, url_prefix='/subcategory')
    # продукт
    app.register_blueprint(cheque, url_prefix='/cheque')
    app.register_blueprint(auto_cheque, url_prefix='/auto-cheque')

    return app



