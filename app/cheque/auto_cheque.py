import os
import re
import time

from PIL import Image
from flask import Blueprint, request
from pyzbar.pyzbar import decode
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from app.category.category import create_category, create_subcategory_data
from app.exceptions import ClientException
from app.models import Category, Subcategory, Product
from app.product.product import create_product
from app.static.struct_json import *
from app.utils import verify_field_json, log_server_error, create_response_error_server, create_response_client_error

auto_cheque = Blueprint('auto-cheque', __name__)

MAX_WAITING_TIME = 30  # макс. время ожидания ответа от веб-страницы (секунды)
WAITING_STEP = 3  # частота проверки наличия элемента на странице (секунды)
WAITING_LOADING_PAGE = 1
NUMBER_WAITING_CYCLES = round(MAX_WAITING_TIME / WAITING_STEP)  # количество проверок наличия элемента на странице

SERVICE_VERIFICATION_CHECK = 'https://proverkacheka.com/'
# SERVICE_OFD = 'https://check.ofd.ru/'
CHROME_DRIVER_PATH = 'app/cheque/chromedriver.exe'

REGEX_FISCAL_SATA = re.compile(r't=\d+\w+&s=\d+.\d+&fn=\d+&i=\d+&fp=\d+&n=1')
REGEX_FN = re.compile(r'fn=\d+')
REGEX_FP = re.compile(r'fp=\d+')
REGEX_FD = re.compile(r'i=\d+')
REGEX_DATE = re.compile(r'\d+\.\d+\.\d+')


@auto_cheque.route('/qr')
def create_from_qr():
    try:
        user_id = request.form[USER_ID]
        image = request.files['image']
        if not image:
            raise ClientException('Изображение отсутствует')
        path = os.path.join('app', image.filename)
        image.save(path)
        decoded_byte_data = decode(Image.open(path))
        os.remove(path)
        if not decoded_byte_data:
            raise ClientException('QR-код не распознан')
        qr_text = decoded_byte_data[0].data.decode()
        if not re.fullmatch(REGEX_FISCAL_SATA, qr_text):
            raise ClientException('QR-код не соответствует стандарту')
        cheque_text = run_service_qr_text(qr_text=qr_text)
        return create_cheque_from_text(user_id=user_id, text=cheque_text)
    except ClientException as e:
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, None)
        return create_response_error_server()


@auto_cheque.route('/qr-text')
def create_from_qr_text():
    data = request.json
    key = 'qr-text'
    try:
        verify_field_json(data, key)
        cheque_text = run_service_qr_text(qr_text=data[key])
        return create_cheque_from_text(user_id=data[USER_ID], text=cheque_text)
    except ClientException as e:
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, None)
        return create_response_error_server()


@auto_cheque.route('/fiscal-data')
def create_from_fiscal_data():
    data = request.json
    fn, fd, fp, s, t, T, n = 'fn', 'fd', 'fp', 's', 't', 'T', 'n'
    try:
        verify_field_json(data, USER_ID, fn, fd, fp, s, t, T, n)
        n = int(data[n])
        cheque_text = run_service_fiscal_data(fn, fd, fp, s, t, T, n)
        return create_cheque_from_text(user_id=data[USER_ID], text=cheque_text)
    except ClientException as e:
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, None)
        return create_response_error_server()


def run_service_qr_text(qr_text):
    """
    :param qr_text: текст qr-кода
    :return: текстовое представление чека
    """
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--start-maximized")
    web_driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    web_driver.get(SERVICE_VERIFICATION_CHECK)
    web_driver.implicitly_wait(WAITING_LOADING_PAGE)  # ждем загрузки страницы

    id_form_qr_code = 'b-checkform_qrraw'
    css_button_check = '#b-checkform_tab-qrraw button'
    css_table = 'table.b-check_table'

    try:
        # region # находим нужную вкладку с формой
        li_elements = web_driver.find_elements(By.TAG_NAME, "li")
        li = None
        for elem in li_elements:
            if elem.text == 'Строка':
                li = elem
                break
        if not li:
            return 'Элемент li не найден'
        li.click()
        # endregion
        elem_qr_code_text = web_driver.find_element(By.ID, id_form_qr_code)
        elem_qr_code_text.send_keys(qr_text)  # вводим в поле textarea данные
        button_check = web_driver.find_element(By.CSS_SELECTOR, css_button_check)  # находим кнопку отправки
        button_check.click()

        for iteration in range(0, NUMBER_WAITING_CYCLES):
            time.sleep(WAITING_STEP)
            if element_exists_on_page_css(web_driver=web_driver, css=css_table):
                rows = web_driver.find_elements(By.TAG_NAME, 'tr')
                cheque_text = ''
                for row in rows:
                    cheque_text += row.text + '\n'
                return cheque_text
        raise ClientException('Чек не найден')
    except ClientException as e:
        return create_response_client_error(e)
    except Exception as e:
        log_server_error(e, None)
        return create_response_error_server()
    finally:
        web_driver.quit()


def run_service_fiscal_data(fn, fd, fp, s, t, T, n):
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--start-maximized")
    web_driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=chromeOptions)
    web_driver.get(SERVICE_VERIFICATION_CHECK)
    web_driver.implicitly_wait(WAITING_LOADING_PAGE)  # ждем загрузки страницы

    elem_id_fn = 'b-checkform_fn'
    elem_id_fd = 'b-checkform_fd'
    elem_id_fp = 'b-checkform_fp'
    elem_id_s = 'b-checkform_s'
    elem_id_date = 'b-checkform_date'
    elem_id_time = 'b-checkform_time'
    elem_id_n = 'b-checkform_n'
    css_button_check = '#b-checkform_tab-props button'
    css_table = 'table.b-check_table'

    try:
        form_send_keys(web_driver=web_driver, id=elem_id_fn, key=fn)
        form_send_keys(web_driver=web_driver, id=elem_id_fd, key=fd)
        form_send_keys(web_driver=web_driver, id=elem_id_fp, key=fp)
        form_send_keys(web_driver=web_driver, id=elem_id_s, key=s)
        form_send_keys(web_driver=web_driver, id=elem_id_date, key=t)
        form_send_keys(web_driver=web_driver, id=elem_id_time, key=T)

        select_element = web_driver.find_element(By.ID, elem_id_n)
        select_object = Select(select_element)
        select_object.select_by_index(n)
        button_check = web_driver.find_element(By.CSS_SELECTOR, css_button_check)  # находим кнопку отправки
        button_check.click()

        for iteration in range(0, NUMBER_WAITING_CYCLES):
            time.sleep(WAITING_STEP)
            if element_exists_on_page_css(web_driver=web_driver, css=css_table):
                rows = web_driver.find_elements(By.TAG_NAME, 'tr')
                cheque_text = ''
                for row in rows:
                    cheque_text += row.text + '\n'
                return cheque_text
        raise ClientException('Чек не найден')
    except Exception:
        raise
    finally:
        web_driver.quit()


def create_cheque_from_text(user_id, text):
    try:
        category = Category.query.filter_by(user_id=user_id, category_name='Другое').first()
        if not category:
            category = create_category({USER_ID: user_id})
        subcategory = Subcategory.query.filter_by(subcategory_name='Другое', category_id=category.id).first()
        if not subcategory:
            subcategory = create_subcategory_data({CATEGORY_ID: category.id, SUBCATEGORY_NAME: 'Другое' })

        cheque_date = re.findall(REGEX_DATE, text)[0]
        sum = re.search(r'ИТОГО:\s\d+\.\d+', text).group(0)
        sum = re.search(r'\d+\.\d+', sum).group(0)
        products_text = re.findall(r'\n\d+\s.+', text)
        products = []
        for pt in products_text:
            line = pt.strip()
            sep_iter = list(re.finditer(r'(\s\d+(\.\d+)*)+$', line))[-1]
            product_name = re.split(r'^\d+\s', line[0: sep_iter.start()])[
                1]  # убираем из названия товара номер в начале
            numbers = re.split(r'\s', line)  # находим 3 числа в строке
            numbers = [value for value in numbers if value]  # убираем пустые значения
            if len(numbers) < 3:
                continue
            count = numbers[-2]
            if re.fullmatch(r'\d+', count):
                count = int(count)
            else:
                count = 1
            cost = numbers[-3]

            product = Product.query.filter_by(subcategory_id=subcategory.id,
                                              product_name=product_name).first()
            if not product:
                product = create_product({
                    SUBCATEGORY_ID: subcategory.id,
                    PRODUCT_NAME: product_name,
                    PRODUCT_COMMENT: ""
                })
            products.append({
                CATEGORY_ID: category.id,
                CATEGORY_NAME: category.category_name,
                SUBCATEGORY_ID: subcategory.id,
                SUBCATEGORY_NAME: subcategory.subcategory_name,
                PRODUCT_ID: product.id,
                PRODUCT_NAME: product.product_name,
                PRODUCT_COMMENT: product.comment,
                PRODUCT_COST: cost,
                PRODUCT_COUNT: count
            })
        if not products:
            raise ClientException('Не удалось сформировать чек из полученных данных')
        cheque = {
            CHEQUE_NAME: 'Мой чек',
            CHEQUE_DATE: cheque_date,
            CHEQUE_SUM: sum,
            PRODUCTS: products
        }
        return cheque
    except Exception:
        raise


def form_send_keys(web_driver, id, key):
    act = web_driver.find_element(by=By.ID, value=id)
    act.click()
    act.send_keys(key)


def element_exists_on_page_id(web_driver, id):
    try:
        web_driver.find_element(by=By.ID, value=id)
    except NoSuchElementException:
        return False
    return True


def element_exists_on_page_css(web_driver, css):
    try:
        web_driver.find_element(by=By.CSS_SELECTOR, value=css)
    except NoSuchElementException:
        return False
    return True
