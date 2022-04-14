from loguru import logger

from app.exceptions import JsonNotFound, JsonIncorrectStructure, KeyJsonNotFound
from app.static.struct_json import KEY_ERROR, SERVER_ERROR


def verify_field_json(data, *required_keys):
    try:
        if not data:
            raise JsonNotFound()
        # if len(data) != len(required_keys):
        #     raise JsonIncorrectStructure()
        for key in required_keys:
            if key not in data.keys():
                raise KeyJsonNotFound(key)
        return data
    except Exception:
        raise


def log_client_error(e: Exception, data):
    logger.info(e.__class__.__name__ + ' ' + str(e) + '\n--Request--\n' + str(data))
    return


def log_server_error(e: Exception, data):
    logger.error(e.__class__.__name__ + ' ' + str(e) + '\n--Request--\n' + str(data))
    return


def create_response_client_error(error: Exception):
    return {KEY_ERROR: str(error)}


def create_response_error_server():
    return {KEY_ERROR: SERVER_ERROR}


logger.add('info.txt', format='{time} {level} {message}', level='INFO', rotation='10 KB')
logger.add('error.txt', format='{time} {level} {message}', level='ERROR', rotation='10 KB')