import telebot
import os
from dotenv import load_dotenv
load_dotenv()

import sqlite3

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN_HERE')
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x) for x in ADMIN_IDS.split(',') if x.strip().isdigit()]

from telebot import types

# Состояния для ожидания фото
WAITING_MENU_PHOTO = {}
WAITING_LUNCH_PHOTO = {}

ORDER_STATE = {}

ORDER_STEPS = [
    'type',
    'address',
    'name',
    'phone',
    'comment',
    'confirm'
]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Посмотреть меню', 'Посмотреть бизнес-ланч')
    markup.add('Сделать заказ')
    return markup

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_type TEXT,
        address TEXT,
        name TEXT,
        phone TEXT,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_order(user_id, data):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, order_type, address, name, phone, comment)
                 VALUES (?, ?, ?, ?, ?, ?)''', (
        user_id,
        data.get('type'),
        data.get('address', ''),
        data.get('name'),
        data.get('phone'),
        data.get('comment', '')
    ))
    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, 'Йо, я на связи! Чем могу помочь?', reply_markup=main_menu_markup())

@bot.message_handler(func=lambda m: m.text == 'Главное меню')
def back_to_main_menu(message):
    bot.send_message(message.chat.id, 'Главное меню:', reply_markup=main_menu_markup())

@bot.message_handler(func=lambda m: m.text == 'Посмотреть меню')
def send_menu(message):
    try:
        with open('data/menu.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption='Актуальное меню', reply_markup=main_menu_markup())
    except FileNotFoundError:
        bot.reply_to(message, 'Меню пока не загружено!', reply_markup=main_menu_markup())

@bot.message_handler(func=lambda m: m.text == 'Посмотреть бизнес-ланч')
def send_lunch(message):
    try:
        with open('data/business-lunch.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption='Бизнес-ланч на сегодня', reply_markup=main_menu_markup())
    except FileNotFoundError:
        bot.reply_to(message, 'Бизнес-ланч пока не загружен!', reply_markup=main_menu_markup())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, 'Ты не админ, братишка!')
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Загрузить меню', 'Загрузить бизнес-ланч')
    bot.send_message(message.chat.id, 'Админ-панель. Выбери действие:', reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Загрузить меню')
def ask_menu_photo(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, 'Только для админов!')
        return
    WAITING_MENU_PHOTO[message.from_user.id] = True
    bot.send_message(message.chat.id, 'Пришли фото меню (menu.jpg)')

@bot.message_handler(func=lambda m: m.text == 'Загрузить бизнес-ланч')
def ask_lunch_photo(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, 'Только для админов!')
        return
    WAITING_LUNCH_PHOTO[message.from_user.id] = True
    bot.send_message(message.chat.id, 'Пришли фото бизнес-ланча (business-lunch.jpg)')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if WAITING_MENU_PHOTO.get(user_id):
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('data/menu.jpg', 'wb') as f:
            f.write(downloaded_file)
        bot.reply_to(message, 'Меню обновлено!')
        WAITING_MENU_PHOTO.pop(user_id)
    elif WAITING_LUNCH_PHOTO.get(user_id):
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('data/business-lunch.jpg', 'wb') as f:
            f.write(downloaded_file)
        bot.reply_to(message, 'Бизнес-ланч обновлён!')
        WAITING_LUNCH_PHOTO.pop(user_id)
    else:
        bot.reply_to(message, 'Фото не требуется сейчас. Если хочешь обновить меню — используй /admin.')

@bot.message_handler(func=lambda m: m.text == 'Сделать заказ')
def start_order(message):
    user_id = message.from_user.id
    ORDER_STATE[user_id] = {'step': 'type', 'data': {}}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Самовывоз', 'Доставка')
    markup.add('Главное меню')
    bot.send_message(message.chat.id, 'Выберите тип заказа:', reply_markup=markup)

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'type' and m.text in ['Самовывоз', 'Доставка'])
def order_type(message):
    user_id = message.from_user.id
    ORDER_STATE[user_id]['data']['type'] = message.text
    if message.text == 'Доставка':
        ORDER_STATE[user_id]['step'] = 'address'
        bot.send_message(message.chat.id, 'Введите адрес доставки:', reply_markup=types.ReplyKeyboardRemove())
    else:
        ORDER_STATE[user_id]['step'] = 'name'
        bot.send_message(message.chat.id, 'Введите ваше имя:', reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'address')
def order_address(message):
    user_id = message.from_user.id
    ORDER_STATE[user_id]['data']['address'] = message.text
    ORDER_STATE[user_id]['step'] = 'name'
    bot.send_message(message.chat.id, 'Введите ваше имя:')

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'name')
def order_name(message):
    user_id = message.from_user.id
    ORDER_STATE[user_id]['data']['name'] = message.text
    ORDER_STATE[user_id]['step'] = 'phone'
    bot.send_message(message.chat.id, 'Введите ваш телефон:')

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'phone')
def order_phone(message):
    user_id = message.from_user.id
    ORDER_STATE[user_id]['data']['phone'] = message.text
    ORDER_STATE[user_id]['step'] = 'comment'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Пропустить')
    bot.send_message(message.chat.id, 'Комментарий к заказу (или нажмите "Пропустить"):', reply_markup=markup)

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'comment')
def order_comment(message):
    user_id = message.from_user.id
    comment = message.text if message.text != 'Пропустить' else ''
    ORDER_STATE[user_id]['data']['comment'] = comment
    ORDER_STATE[user_id]['step'] = 'confirm'
    data = ORDER_STATE[user_id]['data']
    order_text = f"Ваш заказ:\nТип: {data['type']}"
    if data['type'] == 'Доставка':
        order_text += f"\nАдрес: {data['address']}"
    order_text += f"\nИмя: {data['name']}\nТелефон: {data['phone']}"
    if comment:
        order_text += f"\nКомментарий: {comment}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Подтвердить заказ', 'Главное меню')
    bot.send_message(message.chat.id, order_text + '\n\nВсё верно?', reply_markup=markup)

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') == 'confirm' and m.text == 'Подтвердить заказ')
def order_confirm(message):
    user_id = message.from_user.id
    data = ORDER_STATE[user_id]['data']
    order_text = f"Новый заказ!\nТип: {data['type']}"
    if data['type'] == 'Доставка':
        order_text += f"\nАдрес: {data['address']}"
    order_text += f"\nИмя: {data['name']}\nТелефон: {data['phone']}"
    if data['comment']:
        order_text += f"\nКомментарий: {data['comment']}"
    # Сохраняем заказ в базу
    save_order(user_id, data)
    # Отправляем заказ всем админам
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, order_text)
        except Exception:
            pass
    bot.send_message(message.chat.id, 'Спасибо за заказ! Мы свяжемся с вами.', reply_markup=main_menu_markup())
    ORDER_STATE.pop(user_id)

@bot.message_handler(func=lambda m: ORDER_STATE.get(m.from_user.id, {}).get('step') in ['type','address','name','phone','comment','confirm'] and m.text == 'Главное меню')
def order_cancel(message):
    user_id = message.from_user.id
    ORDER_STATE.pop(user_id, None)
    bot.send_message(message.chat.id, 'Вы вернулись в главное меню.', reply_markup=main_menu_markup())

if __name__ == '__main__':
    print('Бот стартует...')
    bot.polling(none_stop=True)
