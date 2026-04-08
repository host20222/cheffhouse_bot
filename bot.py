import logging
import sqlite3
from datetime import datetime
from telebot import TeleBot, types

BOT_TOKEN = "8659993864:AAEBH4hJXwDhP67SfT5XMYyWTdZn15MKLlA"
ADMIN_ID = 8237810301

bot = TeleBot(BOT_TOKEN)

# База данных
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  balance REAL DEFAULT 0,
                  orders INTEGER DEFAULT 0,
                  total_spent REAL DEFAULT 0,
                  reg_date TEXT,
                  referrer_id INTEGER DEFAULT NULL,
                  ref_earnings REAL DEFAULT 0,
                  language TEXT DEFAULT 'ru')''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(user_id, username, first_name, referrer_id=None):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, reg_date, referrer_id) VALUES (?, ?, ?, ?, ?)',
              (user_id, username, first_name, reg_date, referrer_id))
    conn.commit()
    conn.close()

# Главное меню
def main_menu(lang='ru'):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == 'ru':
        markup.row('🛍 Магазин', '💵 Пополнить баланс')
        markup.row('🛒 Профиль', '📟 Поддержка')
        markup.row('📜 Новости', '🏆 Отзывы')
        markup.row('📦 Оптом', '💡 Ваши идеи', '❗ ЧАВО')
        markup.row('💎 Реферальная система')
        markup.row('🇺🇸 Change the language')
    else:
        markup.row('🛍 Shop', '💵 Add funds')
        markup.row('🛒 Profile', '📟 Support')
        markup.row('📜 News', '🏆 Reviews')
        markup.row('📦 Wholesale', '💡 Your ideas', '❓ FAQ')
        markup.row('💎 Referral system')
        markup.row('🇷🇺 Сменить язык')
    return markup

def back_menu(lang='ru'):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('◀️ В меню' if lang == 'ru' else '◀️ Back to menu')
    return markup

# /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    first_name = message.from_user.first_name or ''
    
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id == user_id:
                referrer_id = None
        except:
            pass
    
    add_user(user_id, username, first_name, referrer_id)
    user = get_user(user_id)
    lang = user[9] if user else 'ru'
    
    text = f"Привет, {first_name}! 👋\n\nДобро пожаловать в Cheff House 🌿\nТолько премиальные ингредиенты\nОткройте нужный раздел ниже 👇"
    bot.send_message(user_id, text, reply_markup=main_menu(lang))

# Профиль
@bot.message_handler(func=lambda m: m.text in ['🛒 Профиль', '🛒 Profile'])
def profile(message):
    user = get_user(message.from_user.id)
    if not user:
        return start(message)
    lang = user[9]
    text = f"""📁 Профиль

🔗 Ваш ID: {user[0]}
👛 Ваш баланс: {user[3]:.2f} €
📦 Заказов: {user[4]} шт.
💰 На сумму: {user[5]:.2f} €
🗓 Дата регистрации: {user[6]}

📊 Ваша группа покупателя: Новичёк
👑 Ваша скидка: 0 %
⭐ Рейтинг: 0/10
🛒 Корзина пуста..."""
    bot.send_message(message.chat.id, text, reply_markup=back_menu(lang))

# Поддержка - капча
@bot.message_handler(func=lambda m: m.text in ['📟 Поддержка', '📟 Support'])
def support(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('😊', '🙃', '😎')
    markup.row('🤔', '😴', '🥳')
    bot.send_message(message.chat.id, 
        '🤖 Подтвердите что вы не робот\n\nВыберите смайлик: 😊', 
        reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['😊', '🙃', '😎', '🤔', '😴', '🥳'])
def captcha_answer(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    if message.text == '😊':
        bot.send_message(message.chat.id,
            '✅ Проверка пройдена!\n\n📟 Поддержка Cheff House\n\nНапишите ваш вопрос и мы ответим в ближайшее время.\n\n📩 @cheffhouse_support',
            reply_markup=back_menu(lang))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('😊', '🙃', '😎')
        markup.row('🤔', '😴', '🥳')
        bot.send_message(message.chat.id, '❌ Неверно! Попробуйте ещё раз\n\nВыберите смайлик: 😊', reply_markup=markup)

# Новости
@bot.message_handler(func=lambda m: m.text in ['📜 Новости', '📜 News'])
def news(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id,
        '📜 Новости Cheff House\n\nКанал с новостями временно недоступен.\nСледите за обновлениями!',
        reply_markup=back_menu(lang))

# Отзывы
@bot.message_handler(func=lambda m: m.text in ['🏆 Отзывы', '🏆 Reviews'])
def reviews(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id,
        '🏆 Отзывы\n\nКанал с отзывами временно недоступен.\nСкоро вернёмся!',
        reply_markup=back_menu(lang))

# Оптом
@bot.message_handler(func=lambda m: m.text in ['📦 Оптом', '📦 Wholesale'])
def wholesale(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id,
        '📦 Оптовые заказы\n\nДля оптовых заказов свяжитесь с менеджером:\n📩 @cheffhouse_support',
        reply_markup=back_menu(lang))

# Ваши идеи
user_states = {}

@bot.message_handler(func=lambda m: m.text in ['💡 Ваши идеи', '💡 Your ideas'])
def ideas(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    user_states[message.from_user.id] = 'waiting_idea'
    bot.send_message(message.chat.id,
        '🔥 ИДЕИ и ПОЖЕЛАНИЯ 🔥\n\nЗдесь вы можете оставить свои идеи по развитию шопа.\nВаши идеи анонимные!\n\n✍️ Напишите вашу идею:',
        reply_markup=back_menu(lang))

# ЧАВО
@bot.message_handler(func=lambda m: m.text in ['❗ ЧАВО', '❓ FAQ'])
def faq(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id,
        '''❗ ЧАВО — Часто задаваемые вопросы

❓ Как сделать заказ?
Нажмите 🛍 Магазин и выберите нужный товар.

❓ Как пополнить баланс?
Нажмите 💵 Пополнить баланс и выберите способ оплаты.

❓ Как получить скидку?
Скидки начисляются автоматически при накоплении заказов.

❓ Как связаться с поддержкой?
Нажмите 📟 Поддержка и пройдите проверку.

❓ Как работает реферальная система?
Поделитесь своей ссылкой — получите 5% с пополнения друга.''',
        reply_markup=back_menu(lang))

# Пополнить баланс
@bot.message_handler(func=lambda m: m.text in ['💵 Пополнить баланс', '💵 Add funds'])
def add_funds(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('💳 Card Payment / 🍎 Apple Pay')
    markup.row('🟡 BTC (Bitcoin)')
    markup.row('🔵 LTC (LiteCoin)')
    markup.row('🟢 USDT (TRON)')
    markup.row('🔴 TRX (TRON)')
    markup.row('♻️ PROMOCODE')
    markup.row('◀️ В меню' if lang == 'ru' else '◀️ Back to menu')
    bot.send_message(message.chat.id,
        '💵 Пополнение баланса\n\nВыберите способ оплаты:',
        reply_markup=markup)

# Магазин
@bot.message_handler(func=lambda m: m.text in ['🛍 Магазин', '🛍 Shop'])
def shop(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id,
        '🛍 Магазин Cheff House\n\n🌿 Премиальные ингредиенты\n\nРаздел в разработке. Скоро здесь появятся товары!',
        reply_markup=back_menu(lang))

# Реферальная система
@bot.message_handler(func=lambda m: m.text in ['💎 Реферальная система', '💎 Referral system'])
def referral(message):
    user = get_user(message.from_user.id)
    if not user:
        return start(message)
    lang = user[9]
    ref_link = f"https://t.me/cheffhouse_shop_bot?start={user[0]}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🔺 Назад в меню' if lang == 'ru' else '🔺 Back to menu')
    bot.send_message(message.chat.id,
        f'''📊 Реферальная система:

❓ Если человек, присоединившийся к боту по вашей ссылке, пополнит баланс, то вы получите: 5%

💲 Ваш доход с реферальной системы составляет: {user[8]:.2f} €

🔗 Ваша реферальная ссылка:
{ref_link}''',
        reply_markup=markup)

# Смена языка
@bot.message_handler(func=lambda m: m.text in ['🇺🇸 Change the language', '🇷🇺 Сменить язык'])
def change_language(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    new_lang = 'en' if lang == 'ru' else 'ru'
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET language = ? WHERE user_id = ?', (new_lang, message.from_user.id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id,
        '🇺🇸 Language changed to English!' if new_lang == 'en' else '🇷🇺 Язык изменён на русский!',
        reply_markup=main_menu(new_lang))

# В меню
@bot.message_handler(func=lambda m: m.text in ['◀️ В меню', '◀️ Back to menu', '🔺 Назад в меню', '🔺 Back to menu'])
def back_to_menu(message):
    user = get_user(message.from_user.id)
    lang = user[9] if user else 'ru'
    bot.send_message(message.chat.id, '↩️ Вы вернулись в главное меню', reply_markup=main_menu(lang))

# Обработка идей и текста
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    lang = user[9] if user else 'ru'
    
    if user_states.get(user_id) == 'waiting_idea':
        user_states.pop(user_id)
        bot.send_message(ADMIN_ID, f'💡 Новая идея от пользователя {user_id}:\n\n{message.text}')
        bot.send_message(message.chat.id, '✅ Спасибо! Ваша идея отправлена анонимно.', reply_markup=main_menu(lang))
    else:
        bot.send_message(message.chat.id, 'Используйте кнопки меню 👇', reply_markup=main_menu(lang))

if __name__ == '__main__':
    init_db()
    print('Бот запущен!')
    bot.polling(none_stop=True)