import sqlite3


def write_to_db(user, chat_id):
    '''
    Функция для запись данных пользователя в базу данных
    :param user: Словарь с информацией о пользователе
    :param chat_id: ID пользователя
    :return: none
    '''
    conn = sqlite3.connect('./DB/DB.db')
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT,
         surname TEXT, email TEXT, phone_number TEXT, birth_date, chat_id TEXT, is_send TEXT)''')
    cursor.execute(
        f"INSERT INTO users (name, surname, email, phone_number, birth_date, chat_id, is_send) VALUES ('{user.name}', "
        f"'{user.surname}', '{user.email}', '{user.phone_number}', '{user.birth_date}', '{chat_id}', '0')")
    conn.commit()
    conn.close()


def get_data_from_db(is_send):
    '''
    Функция для получение пользователей из базы данных
    :param is_send: False - пользователи чьи данные не отправлены в форму, True - пользователи с отправленными данными
    :return: Словарь с пользователями
    '''
    conn = sqlite3.connect('./DB/DB.db')
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT,
         surname TEXT, email TEXT, phone_number TEXT, birth_date, chat_id TEXT, is_send TEXT)''')
    keys = ('id', 'name', 'surname', 'email', 'phone_number', 'birth_date', 'chat_id', 'is_send')
    dict_from_db = list()

    cursor.execute(f"SELECT * FROM users WHERE is_send={is_send}")
    values = cursor.fetchall()
    cursor.close()
    conn.close()

    for value in values:
        dict_from_db.append(dict(zip(keys, value)))
    return dict_from_db


def write_is_send(chat_id):
    '''
    Функция для отметки пользователей чьи данные отправлены
    :param chat_id: ID пользователя
    :return: none
    '''
    conn = sqlite3.connect('./DB/DB.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET is_send = 1 WHERE chat_id = {chat_id}')
    conn.commit()
    conn.close()
