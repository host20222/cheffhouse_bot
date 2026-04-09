import logging
import sqlite3
from datetime import datetime
from telebot import TeleBot, types

BOT_TOKEN = "8659993864:AAEBH4hJXwDhP67SfT5XMYyWTdZn15MKLlA"
ADMIN_ID = 8237810301
MAIN_PHOTO = "https://i.ibb.co/Hp76WyHV/IMG-5547.jpg"

bot = TeleBot(BOT_TOKEN)

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

def get_lang(user_id):
    user = get_user(user_id)
    return user[9] if user else 'ru'

TEXTS = {
    'ru': {
        'welcome': '👋 Привет, {name}!\n\nДобро пожаловать в Cheff House 🌿\nТолько премиальные ингредиенты\nОткройте нужный раздел ниже 👇',
        'back': '◀️ В меню',
        'back_menu': '↩️ Вы вернулись в главное меню',
        'support_captcha': '🤖 Подтвердите что вы не робот\n\nВыберите смайлик: 😊',
        'support_wrong': '❌ Неверно! Попробуйте ещё раз\n\nВыберите смайлик: 😊',
        'support_ok': '✅ Проверка пройдена!\n\n📟 Поддержка Cheff House\n\nНапишите ваш вопрос и мы ответим в ближайшее время.\n📩 @cheffhouse_support',
        'news': '📜 Новости Cheff House\n\nКанал с новостями временно недоступен.\nСледите за обновлениями!',
        'reviews': '🏆 Отзывы\n\nКанал с отзывами временно недоступен.\nСкоро вернёмся!',
        'wholesale': '📦 Оптовые заказы\n\nДля оптовых заказов свяжитесь с менеджером:\n📩 @cheffhouse_support',
        'ideas_prompt': '🔥 ИДЕИ и ПОЖЕЛАНИЯ 🔥\n\nОставьте свои идеи по развитию шопа.\nВаши идеи анонимные!\n\n✍️ Напишите вашу идею:',
        'ideas_sent': '✅ Спасибо! Ваша идея отправлена анонимно.',
        'faq': '❗ ЧАВО\n\n❓ Как сделать заказ?\nНажмите 🛍 Магазин и выберите товар.\n\n❓ Как пополнить баланс?\nНажмите 💵 Пополнить баланс.\n\n❓ Как работает рефералка?\nПоделитесь ссылкой — получите 5% с пополнения друга.',
        'add_funds': '💵 Пополнение баланса\n\nВыберите способ оплаты:',
        'shop_city': '🛍 Магазин Cheff House\n\n🌿 Выберите ваш город:',
        'shop_products': '🛍 Магазин — Прага\n\nВыберите товар:',
        'ref_text': '📊 Реферальная система:\n\n❓ Если человек по вашей ссылке пополнит баланс — вы получите: 5%\n\n💲 Ваш доход: {earnings:.2f} €\n\n🔗 Ваша реферальная ссылка:\n{link}',
        'order_confirm': '✅ Заказ оформлен!\n\n{product}\nКол-во: {qty}\nСумма: {price}\n\nДля оплаты пополните баланс 💵',
        'use_buttons': 'Используйте кнопки меню 👇',
        'choose_qty': 'Выберите количество:\n\n',
    },
    'en': {
        'welcome': '👋 Hello, {name}!\n\nWelcome to Cheff House 🌿\nOnly premium ingredients\nChoose a section below 👇',
        'back': '◀️ Back to menu',
        'back_menu': '↩️ You returned to the main menu',
        'support_captcha': '🤖 Confirm you are not a robot\n\nChoose the emoji: 😊',
        'support_wrong': '❌ Wrong! Try again\n\nChoose the emoji: 😊',
        'support_ok': '✅ Verified!\n\n📟 Cheff House Support\n\nWrite your question and we will answer soon.\n📩 @cheffhouse_support',
        'news': '📜 Cheff House News\n\nNews channel temporarily unavailable.\nStay tuned!',
        'reviews': '🏆 Reviews\n\nReviews channel temporarily unavailable.\nComing back soon!',
        'wholesale': '📦 Wholesale Orders\n\nContact our manager:\n📩 @cheffhouse_support',
        'ideas_prompt': '🔥 IDEAS & SUGGESTIONS 🔥\n\nLeave your ideas here.\nYour ideas are anonymous!\n\n✍️ Write your idea:',
        'ideas_sent': '✅ Thank you! Your idea was sent anonymously.',
        'faq': '❓ FAQ\n\n❓ How to order?\nPress 🛍 Shop and choose a product.\n\n❓ How to add funds?\nPress 💵 Add funds.\n\n❓ How does referral work?\nShare your link — get 5% from friend deposit.',
        'add_funds': '💵 Add Funds\n\nChoose payment method:',
        'shop_city': '🛍 Cheff House Shop\n\n🌿 Choose your city:',
        'shop_products': '🛍 Shop — Prague\n\nChoose a product:',
        'ref_text': '📊 Referral System:\n\n❓ If someone adds funds via your link you get: 5%\n\n💲 Your earnings: {earnings:.2f} €\n\n🔗 Your referral link:\n{link}',
        'order_confirm': '✅ Order placed!\n\n{product}\nQty: {qty}\nTotal: {price}\n\nPlease add funds to pay 💵',
        'use_buttons': 'Please use the menu buttons 👇',
        'choose_qty': 'Choose quantity:\n\n',
    }
}

PRODUCTS = {
    'ru': {
        '🥦 Premium broccoli': [('1 шт', '300 CZK ≈ $13'), ('2 шт', '599 CZK ≈ $26'), ('3 шт', '750 CZK ≈ $33'), ('4 шт', '1000 CZK ≈ $43')],
        '🌸 Lotus seed flour (Pure 92%)': [('1 кг', '2800 CZK ≈ $122'), ('2 кг', '5300 CZK ≈ $230'), ('3 кг', '7500 CZK ≈ $326')],
        '🍬 Wasanbon sugar': [('0.5 кг', '700 CZK ≈ $30'), ('1 кг', '1200 CZK ≈ $52'), ('2 кг', '2199 CZK ≈ $96'), ('3 кг', '3099 CZK ≈ $135'), ('4 кг', '3999 CZK ≈ $174')],
        '🎧 Клубная музыка (Netflix/RedBull/SoundCloud)': [('1 мес', '300 CZK ≈ $13'), ('2 мес', '600 CZK ≈ $26'), ('3 мес', '800 CZK ≈ $35'), ('4 мес', '1000 CZK ≈ $43')],
    },
    'en': {
        '🥦 Premium broccoli': [('1 pc', '300 CZK ≈ $13'), ('2 pc', '599 CZK ≈ $26'), ('3 pc', '750 CZK ≈ $33'), ('4 pc', '1000 CZK ≈ $43')],
        '🌸 Lotus seed flour (Pure 92%)': [('1 kg', '2800 CZK ≈ $122'), ('2 kg', '5300 CZK ≈ $230'), ('3 kg', '7500 CZK ≈ $326')],
        '🍬 Wasanbon sugar': [('0.5 kg', '700 CZK ≈ $30'), ('1 kg', '1200 CZK ≈ $52'), ('2 kg', '2199 CZK ≈ $96'), ('3 kg', '3099 CZK ≈ $135'), ('4 kg', '3999 CZK ≈ $174')],
        '🎧 Club music (Netflix/RedBull/SoundCloud)': [('1 mo', '300 CZK ≈ $13'), ('2 mo', '600 CZK ≈ $26'), ('3 mo', '800 CZK ≈ $35'), ('4 mo', '1000 CZK ≈ $43')],
    }
}

ALL_PRODUCTS = list(PRODUCTS['ru'].keys()) + list(PRODUCTS['en'].keys())

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

def back_btn(lang='ru'):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(TEXTS[lang]['back'])
    return markup

user_states = {}

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
    lang = get_lang(user_id)
    text = TEXTS[lang]['welcome'].format(name=first_name)
    try:
        bot.send_photo(user_id, MAIN_PHOTO, caption=text, reply_markup=main_menu(lang))
    except:
        bot.send_message(user_id, text, reply_markup=main_menu(lang))

@bot.message_handler(func=lambda m: m.text in ['🛒 Профиль', '🛒 Profile'])
def profile(message):
    user = get_user(message.from_user.id)
    if not user:
        return start(message)
    lang = user[9]
    text = f"📁 {'Профиль' if lang=='ru' else 'Profile'}\n\n🔗 ID: {user[0]}\n👛 {'Баланс' if lang=='ru' else 'Balance'}: {user[3]:.2f} €\n📦 {'Заказов' if lang=='ru' else 'Orders'}: {user[4]}\n💰 {'На сумму' if lang=='ru' else 'Total'}: {user[5]:.2f} €\n🗓 {'Дата' if lang=='ru' else 'Date'}: {user[6]}\n\n📊 {'Группа' if lang=='ru' else 'Group'}: {'Новичёк' if lang=='ru' else 'Newbie'}\n👑 {'Скидка' if lang=='ru' else 'Discount'}: 0%\n⭐ {'Рейтинг' if lang=='ru' else 'Rating'}: 0/10\n🛒 {'Корзина пуста' if lang=='ru' else 'Cart empty'}..."
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=text, reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, text, reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['📟 Поддержка', '📟 Support'])
def support(message):
    lang = get_lang(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('😊', '🙃', '😎')
    markup.row('🤔', '😴', '🥳')
    bot.send_message(message.chat.id, TEXTS[lang]['support_captcha'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['😊', '🙃', '😎', '🤔', '😴', '🥳'])
def captcha_answer(message):
    lang = get_lang(message.from_user.id)
    if message.text == '😊':
        try:
            bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['support_ok'], reply_markup=back_btn(lang))
        except:
            bot.send_message(message.chat.id, TEXTS[lang]['support_ok'], reply_markup=back_btn(lang))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('😊', '🙃', '😎')
        markup.row('🤔', '😴', '🥳')
        bot.send_message(message.chat.id, TEXTS[lang]['support_wrong'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['📜 Новости', '📜 News'])
def news(message):
    lang = get_lang(message.from_user.id)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['news'], reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['news'], reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['🏆 Отзывы', '🏆 Reviews'])
def reviews(message):
    lang = get_lang(message.from_user.id)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['reviews'], reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['reviews'], reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['📦 Оптом', '📦 Wholesale'])
def wholesale(message):
    lang = get_lang(message.from_user.id)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['wholesale'], reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['wholesale'], reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['💡 Ваши идеи', '💡 Your ideas'])
def ideas(message):
    lang = get_lang(message.from_user.id)
    user_states[message.from_user.id] = 'waiting_idea'
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['ideas_prompt'], reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['ideas_prompt'], reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['❗ ЧАВО', '❓ FAQ'])
def faq(message):
    lang = get_lang(message.from_user.id)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['faq'], reply_markup=back_btn(lang))
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['faq'], reply_markup=back_btn(lang))

@bot.message_handler(func=lambda m: m.text in ['💵 Пополнить баланс', '💵 Add funds'])
def add_funds(message):
    lang = get_lang(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('💳 Card / 🍎 Apple Pay')
    markup.row('🟡 BTC (Bitcoin)')
    markup.row('🔵 LTC (LiteCoin)')
    markup.row('🟢 USDT (TRON)')
    markup.row('🔴 TRX (TRON)')
    markup.row('♻️ PROMOCODE')
    markup.row(TEXTS[lang]['back'])
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['add_funds'], reply_markup=markup)
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['add_funds'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['🛍 Магазин', '🛍 Shop'])
def shop(message):
    lang = get_lang(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🏙 Прага / Prague')
    markup.row(TEXTS[lang]['back'])
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['shop_city'], reply_markup=markup)
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['shop_city'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🏙 Прага / Prague')
def shop_prague(message):
    lang = get_lang(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in PRODUCTS[lang].keys():
        markup.row(p)
    markup.row(TEXTS[lang]['back'])
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=TEXTS[lang]['shop_products'], reply_markup=markup)
    except:
        bot.send_message(message.chat.id, TEXTS[lang]['shop_products'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ALL_PRODUCTS)
def product_selected(message):
    lang = get_lang(message.from_user.id)
    product_name = message.text
    if product_name not in PRODUCTS[lang]:
        other = 'en' if lang == 'ru' else 'ru'
        if product_name in PRODUCTS[other]:
            product_name = list(PRODUCTS[lang].keys())[list(PRODUCTS[other].keys()).index(product_name)]
    options = PRODUCTS[lang][product_name]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for qty, price in options:
        markup.row(f"{qty} — {price}")
    markup.row(TEXTS[lang]['back'])
    user_states[message.from_user.id] = {'state': 'selecting_qty', 'product': product_name}
    text = TEXTS[lang]['choose_qty'] + product_name
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['💎 Реферальная система', '💎 Referral system'])
def referral(message):
    user = get_user(message.from_user.id)
    if not user:
        return start(message)
    lang = user[9]
    ref_link = f"https://t.me/cheffhouse_shop_bot?start={user[0]}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🔺 Назад в меню' if lang == 'ru' else '🔺 Back to menu')
    text = TEXTS[lang]['ref_text'].format(earnings=user[8], link=ref_link)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

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
    first_name = message.from_user.first_name or ''
    text = TEXTS[new_lang]['welcome'].format(name=first_name)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=text, reply_markup=main_menu(new_lang))
    except:
        bot.send_message(message.chat.id, text, reply_markup=main_menu(new_lang))

@bot.message_handler(func=lambda m: m.text in ['◀️ В меню', '◀️ Back to menu', '🔺 Назад в меню', '🔺 Back to menu'])
def back_to_menu(message):
    lang = get_lang(message.from_user.id)
    user_states.pop(message.from_user.id, None)
    first_name = message.from_user.first_name or ''
    text = TEXTS[lang]['welcome'].format(name=first_name)
    try:
        bot.send_photo(message.chat.id, MAIN_PHOTO, caption=text, reply_markup=main_menu(lang))
    except:
        bot.send_message(message.chat.id, text, reply_markup=main_menu(lang))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    state = user_states.get(user_id)
    if isinstance(state, dict) and state.get('state') == 'selecting_qty':
        product = state['product']
        qty_price = message.text
        user_states.pop(user_id, None)
        parts = qty_price.split('—')
        qty = parts[0].strip() if len(parts) > 1 else qty_price
        price = parts[1].strip() if len(parts) > 1 else ''
        bot.send_message(user_id, TEXTS[lang]['order_confirm'].format(product=product, qty=qty, price=price), reply_markup=main_menu(lang))
        bot.send_message(ADMIN_ID, f'🛍 Новый заказ!\nПользователь: {user_id}\nТовар: {product}\nКол-во/цена: {qty_price}')
    elif state == 'waiting_idea':
        user_states.pop(user_id, None)
        bot.send_message(ADMIN_ID, f'💡 Идея от {user_id}:\n\n{message.text}')
        bot.send_message(message.chat.id, TEXTS[lang]['ideas_sent'], reply_markup=main_menu(lang))
    else:
        bot.send_message(message.chat.id, TEXTS[lang]['use_buttons'], reply_markup=main_menu(lang))

if __name__ == '__main__':
    init_db()
    print('Бот запущен!')
    bot.polling(none_stop=True)
