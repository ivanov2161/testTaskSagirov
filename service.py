import datetime
import asyncio
import os
import re

from telebot import types
import telebot

from model import write_to_db

# Переменные для запуска бота
TOKEN = os.environ.get('TOKEN')
URL = 'https://b24-iu5stq.bitrix24.site/backend_test/'

bot = telebot.TeleBot(TOKEN)


class User:
    '''
    Класс для временного хранения данных пользователя
    '''

    def __init__(self):
        self.name = ''
        self.surname = ''
        self.email = ''
        self.phone_number = ''
        self.birth_date = ''
        self.last_message_by_bot = ''


users = dict()


def is_valid_email(email):
    '''
    Функция для проверки правильного ввода адреса электронной почты
    :param email: Адрес электронной почты
    :return: bool
    '''
    pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    match = pattern.search(email)
    return match is not None


def is_valid_phone_number(phone_number):
    '''
    Функция для проверки правильного ввода номера телефона
    :param phone_number: Номер телефона
    :return: bool
    '''
    pattern = re.compile(r'^\+7[0-9]{10}$')
    match = pattern.search(phone_number)
    return match is not None


def is_valid_birth_date(birth_date):
    '''
    Функция для проверки правильного ввода даты рождения
    :param birth_date: Дата рождения
    :return: bool
    '''
    try:
        datetime.datetime.strptime(birth_date, '%d.%m.%Y')
        return True
    except ValueError:
        return False


# Обработка чата с пользователем
@bot.message_handler(content_types=['text'])
def start(message):
    '''
    Приветствие пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    # Создаем эксземпляр класса в словаре с ключем в виде ID пользователя для возможности
    # параллельного заполнения данных
    users[id] = User()
    if message.text == '/start':
        bot.send_message(id, "Как тебя зовут?")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(id, f"Привет, я помогу тебе заполнить форму на сайте {URL}")
        bot.send_message(id, "Чтобы начать, введите /start")


def get_name(message):
    '''
    Функция для получения имени пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    users[id].name = message.text
    bot.send_message(id, 'Какая у тебя фамилия?')
    bot.register_next_step_handler(message, get_surname)


def get_surname(message):
    '''
    Функция для получения фамилии пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    users[id].surname = message.text
    bot.send_message(id, 'Введите электронную почту в формате example@example.com')
    bot.register_next_step_handler(message, get_email)


def get_email(message):
    '''
    Функция для получения адреса почты пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    users[id].email = message.text
    # Проверяем формат электронной почты
    if is_valid_email(users[id].email):
        bot.register_next_step_handler(message, get_phone_number)
        bot.send_message(id, 'Введите номер телефона в следующем формате +7ХХХХХХХХХХ')
    else:
        bot.send_message(id, 'Неправильный формат электронной почты, введите в формате example@gmail.com')
        bot.register_next_step_handler(message, get_email)


def get_phone_number(message):
    '''
    Функция для получения номера телефона пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    users[id].phone_number = message.text
    # Проверяем формат номера телефона
    if is_valid_phone_number(users[id].phone_number):
        bot.send_message(id, 'Введите дату рождения в формате ДД.ММ.ГГГГ')
        bot.register_next_step_handler(message, get_birth_date)
    else:
        bot.send_message(id, 'Неправильный формат номера телефона, введите в формате +7ХХХХХХХХХХ')
        bot.register_next_step_handler(message, get_phone_number)


def get_birth_date(message):
    '''
    Функция для получения даты рождения пользователя
    :param message: Сообщение пользователя
    :return: none
    '''
    global users
    id = message.from_user.id
    users[id].birth_date = message.text
    # Проверяем формат даты рождения
    if is_valid_birth_date(users[id].birth_date):

        # Настраиваем клавиатуру для подтверждения введеных данных пользователем
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)

        # Формируем вопрос с введеными данными пользователя
        question = f'Тебя зовут *{users[id].name}* *{users[id].surname}* ваша почта *{users[id].email}* ' \
                   f'ваш номер телефона *{users[id].phone_number}* ваша дата рождения *{users[id].birth_date}*'

        bot.send_message(id, question, parse_mode='Markdown')
        users[id].last_message_by_bot = bot.send_message(id, text='Верно?', reply_markup=keyboard, ).message_id
    else:
        bot.send_message(id, "Неправильный формат даты, введите в следующем формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(message, get_birth_date)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    '''
    Функция для обработки нажатия клавиш Да или Нет - подтвержление введеных данных пользователем
    :param call: Входящий запрос обратного вызова
    :return: none
    '''
    global users
    id = call.message.chat.id
    if call.data == "yes":  # Обработка нажатия кнопки "Да" клавиатуры

        # Записываем данные пользователя в базу данных
        write_to_db(users[id], id)

        # Удаляем сообщение с клавиатурой, чтобы избежать двойного нажатия пользователем
        bot.delete_message(id, users[id].last_message_by_bot)

        bot.send_message(id, 'В течении десяти минут отправлю Вам скриншот с подтверждением заполнения формы 🙂')
        bot.send_message(id, 'Чтобы отправить новые данные введите /start')

        # Удаляем пользователя из словаря
        users.__delitem__(id)
    elif call.data == "no":  # Обработка нажатия кнопки "Нет" клавиатуры

        # Удаляем сообщение с клавиатурой, чтобы избежать двойного нажатия пользователем
        bot.delete_message(id, users[id].last_message_by_bot)
        bot.send_message(id, 'Покрутим еще, напишите /start')

        # Удаляем пользователя из словаря
        users.__delitem__(id)


async def run_polling():
    '''
    Функция для асинхронной работы
    :return: none
    '''
    await asyncio.get_event_loop().run_in_executor(None, bot.polling)
