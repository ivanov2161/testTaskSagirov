import datetime
import asyncio
import time
import os

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from PIL import Image
import requests
import telebot

from model import get_data_from_db, write_is_send

TOKEN = os.environ.get('TOKEN')
CHECK_AVAILABLE_FORM_TIME = 600  # Период проверки доступности формы


class FormClient:
    def __init__(self):
        self.url_image_selenium = 'http://172.17.0.2:4444/wd/hub'  # Вставить адрес selenium/standalone-firefox
        self.url = 'https://b24-iu5stq.bitrix24.site/backend_test/'  # Адрес формы
        self.folder_path = './images'  # Путь до папки, куда будут сохраняться скриншоты
        # Координаты для обрезания скриншота
        self.left = 460
        self.top = 140
        self.right = 900
        self.bottom = 450

    def fill_form(self, user):
        '''
        Метод для заполнения формы
        :param user: Словарь с данными пользователя
        :return: none
        '''

        driver = webdriver.Remote(
            command_executor=self.url_image_selenium,
            desired_capabilities={'browserName': 'firefox'})

        driver.get(self.url)

        self.fill_name(driver, user)
        self.fill_contacts(driver, user)
        self.fill_birth_date(driver, user)

        # Снимаем скриншот
        time.sleep(2)
        self.take_screenshot_and_send(driver, user['chat_id'])
        driver.close()

    def fill_name(self, driver, user):
        '''
        Метод для заполнения первой страницы формы с именем и фамилией
        :param driver: WebDriver браузера Mozilla Firefox
        :param user: Словарь с данными пользователя
        :return: none
        '''
        # Найдем элементы формы для имени и фамилии
        name_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "name")))
        surname_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "lastname")))

        # Заполним форму
        name_field.send_keys(user['name'])
        surname_field.send_keys(user['surname'])

        # Найдем кнопку отправки формы и нажмем на нее
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button')
        submit_button.click()

    def fill_contacts(self, driver, user):
        '''
        Метод для заполнения второй страницы формы с электронной почтой и номером телефона
        :param driver: WebDriver браузера Mozilla Firefox
        :param user: Словарь с данными пользователя
        :return: none
        '''
        # Найдем элементы формы для электронной почты и номера телефона
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email")))
        phone_number_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "phone")))

        # Заполним форму
        email_field.send_keys(user['email'])
        phone_number_field.send_keys(user['phone_number'])

        # Найдем кнопки отправки формы и нажмем на нужную
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, 'button')
        submit_buttons[1].click()
        time.sleep(1)

    def fill_birth_date(self, driver, user):
        '''
        Метод для заполнения третьей страницы формы с датой рождения
        :param driver: WebDriver браузера Mozilla Firefox
        :param user: Словарь с данными пользователя
        :return: none
        '''
        # Найдем элемент форм для даты рождения
        birth_date_field = driver.find_element(By.CSS_SELECTOR, 'input')

        # Удаляем атрибут readonly
        driver.execute_script("arguments[0].removeAttribute('readonly')", birth_date_field)
        birth_date_field.send_keys(user['birth_date'])

        # Найдем кнопку отправки формы и нажмем на нее
        submit_buttons = driver.find_elements(By.CSS_SELECTOR, 'button')
        submit_buttons[1].click()

    def check_available(self):
        """
        Метод для проверки доступности формы
        :return: bool
        """
        response = requests.get(self.url)

        if response.status_code == 200:
            return True
        else:
            return False

    def take_screenshot_and_send(self, driver, chat_id):
        '''
        Метод для захвата скриншота и отправки его пользователю
        :param driver: WebDriver браузера Mozilla Firefox
        :param chat_id: ID пользователя
        :return: none
        '''

        # Получить текущую дату и время
        now = datetime.datetime.now()

        # Формат даты и времени для имени файла
        date_time = now.strftime("%Y-%m-%d_%H-%M")

        # Полный путь до файла
        file_path = f'{self.folder_path}/{date_time}_{chat_id}.png'

        # Сохраняем скриншот
        driver.save_screenshot(file_path)

        # Открываем скриншот
        screenshot = Image.open(file_path)

        # Обрезаем скриншот
        screenshot = screenshot.crop((self.left, self.top, self.right, self.bottom))

        # Отправляем скриншот пользователю
        bot = telebot.TeleBot(TOKEN)
        bot.send_photo(chat_id, screenshot)
        screenshot.close()


def send_data_to_form():
    '''
    Функция для организации проверки доступности формы и отправки данных один раз в check_available_form_time секунд
    :return: none
    '''
    client_form = FormClient()
    # С промежутком в check_available_form_time проверка на добавление новых данных для заполнения формы
    while True:
        if client_form.check_available():
            print('Form is available')
            users = get_data_from_db(False)
            if users:
                for user in users:
                    client_form.fill_form(user)
                    write_is_send(user['chat_id'])
            else:
                print('No new data to send')
        else:
            print('Form is not available')
        time.sleep(CHECK_AVAILABLE_FORM_TIME)


async def check_available():
    '''
    Функция для асинхронной работы
    :return: none
    '''
    await asyncio.get_event_loop().run_in_executor(None, send_data_to_form)
