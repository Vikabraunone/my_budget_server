class ClientException(Exception):
    pass


class RequestException(ClientException):
    pass


class LoginException(ClientException):
    pass


verbose_names_database = {
    'User': 'Пользователь',
    'Account': 'Счет',
    'Category': 'Категория',
    'Subcategory': 'Подкатегория',
    'Product': 'Товар'
}


class JsonNotFound(RequestException):
    def __init__(self):
        super().__init__(
            'Данные json отсутствуют.'
        )


class JsonIncorrectStructure(RequestException):
    def __init__(self):
        super().__init__(
            'Неверная структура json.'
        )


class KeyJsonNotFound(RequestException):
    def __init__(self, key):
        super().__init__(
            f'Ключ не найден {key}.'
        )


class InvalidEmail(LoginException):
    def __init__(self, email):
        super().__init__(
            f'Неверный формат электронной почты: {email}.'
        )


class RegistrationEmailExists(LoginException):
    def __init__(self, email):
        super().__init__(
            f'Пользователь с таким email {email} уже зарегистрирован.'
        )


class InvalidLogin(LoginException):
    def __init__(self):
        super().__init__(
            'Неверный логин и/или пароль.'
        )


class UserNotFound(LoginException):
    def __init__(self):
        super().__init__(
            'Пользователь не найден'
        )


class DatabaseEntryNotFound(ClientException):
    """Запись в базе данных не найдена"""
    def __init__(self, db_table):
        self.name = db_table.__class__.__name__
        super().__init__(
            f'{verbose_names_database[self.name]} не найден(a).'
        )


class DatabaseEntryExists(ClientException):
    """Такая запись в базе данных уже существует (при создании или изменении объектов)"""
    def __init__(self, db_table, name):
        self.name = db_table.__class__.__name__
        super().__init__(
            f'{verbose_names_database[self.name]} \"{name}\" уже существует.'
        )