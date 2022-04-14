from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    accounts = db.relationship('Account', backref='user')
    shopping_lists = db.relationship('ShoppingList', backref='user')
    categories = db.relationship('Category', backref='user')

    def __repr__(self):
        return f'Пользователь: {self.username}'


class Account(db.Model):
    """Счет"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    account_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(9, 2), nullable=False, default=0.00)

    cheques = db.relationship('Cheque', cascade="all, delete", backref='account')

    def __repr__(self):
        return f'Счет: {self.account_name}'


class Cheque(db.Model):
    """Чек"""
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"))
    cheque_name = db.Column(db.String(100), nullable=True)
    sum = db.Column(db.Numeric(9, 2), nullable=False)
    positive_cheque = db.Column(db.Boolean(), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    comment = db.Column(db.String(255), nullable=True)

    cheque_products = db.relationship('ProductCheque', cascade="all,delete", backref='cheque')

    def __repr__(self):
        return f'Чек {self.cheque_name} от {self.date}'


class ProductCheque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.Numeric(9, 2), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    cheque_id = db.Column(db.Integer, db.ForeignKey("cheque.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))


class Product(db.Model):
    """Продукт"""
    id = db.Column(db.Integer, primary_key=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey("subcategory.id"))
    shopping_list_id = db.Column(db.Integer, db.ForeignKey("shopping_list.id"))
    product_name = db.Column(db.String(255), nullable=False)
    comment = db.Column(db.String(255), nullable=True)

    cheque_products = db.relationship('ProductCheque', cascade="all,delete", backref='product')

    def __repr__(self):
        return f'Продукт {self.product_name}'


class Subcategory(db.Model):
    """Подкатегория"""
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    subcategory_name = db.Column(db.String(255), nullable=False)

    products = db.relationship('Product', cascade="all,delete", backref='subcategory')

    def __repr__(self):
        return f'Подкатегория {self.subcategory_name}'


class Category(db.Model):
    """Категория"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_name = db.Column(db.String(255), nullable=False)

    subcategories = db.relationship('Subcategory', cascade="all,delete", backref='category')

    def __repr__(self):
        return f'Категория {self.category_name}'


class ShoppingList(db.Model):
    """Список покупок"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    list_name = db.Column(db.String(255), nullable=True)
    date_create = db.Column(db.Date(), nullable=False)

    products = db.relationship('Product', cascade="all,delete", backref='shopping_list')

    def __repr__(self):
        return f'Категория {self.category_name}'
