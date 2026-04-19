import logging
import sqlite3
import json
import time
from datetime import datetime
from telebot import TeleBot, types

BOT_TOKEN = "8659993864:AAEBH4hJXwDhP67SfT5XMYyWTdZn15MKLlA"
ADMIN_ID = 8237810301
COURIER_GROUP_ID = -1003953531389
MAIN_PHOTO = "https://i.ibb.co/sTVxqHk/IMG-5853.jpg"
SHOP_PHOTO = "https://i.postimg.cc/FK0sX1pL/IMG-5556.jpg"
CHANNEL_LINK = "https://t.me/chef_house_cz"

bot = TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# ─── DB ───────────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0,
        orders INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        reg_date TEXT,
        referrer_id INTEGER DEFAULT NULL,
        ref_earnings REAL DEFAULT 0,
        language TEXT DEFAULT 'ru',
        first_order_done INTEGER DEFAULT 0,
        shop_verified INTEGER DEFAULT 0
    )''')
    # Добавить колонку если БД старая (без неё)
    try:
        c.execute('ALTER TABLE users ADD COLUMN shop_verified INTEGER DEFAULT 0')
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS carts (
        user_id INTEGER,
        product TEXT,
        qty TEXT,
        price TEXT,
        PRIMARY KEY (user_id, product, qty)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        items TEXT,
        total TEXT,
        address TEXT,
        status TEXT DEFAULT 'new',
        courier_id INTEGER DEFAULT NULL,
        created_at TEXT,
        is_referral INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS known_groups (
        chat_id INTEGER PRIMARY KEY,
        title TEXT,
        chat_type TEXT,
        seen_at TEXT
    )''')
    conn.commit()
    conn.close()

def save_group(chat_id, title, chat_type):
    conn = db()
    c = conn.cursor()
    seen_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT OR REPLACE INTO known_groups (chat_id, title, chat_type, seen_at) VALUES (?,?,?,?)',
              (chat_id, title, chat_type, seen_at))
    conn.commit()
    conn.close()

def get_known_groups():
    conn = db()
    c = conn.cursor()
    c.execute('SELECT chat_id, title, chat_type, seen_at FROM known_groups ORDER BY seen_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def db():
    return sqlite3.connect('bot.db')

def get_user(user_id):
    conn = db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    u = c.fetchone()
    conn.close()
    return u

def add_user(user_id, username, first_name, referrer_id=None):
    conn = db()
    c = conn.cursor()
    reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, reg_date, referrer_id) VALUES (?,?,?,?,?)',
              (user_id, username, first_name, reg_date, referrer_id))
    conn.commit()
    conn.close()

def get_lang(user_id):
    u = get_user(user_id)
    return u[9] if u else 'ru'

def set_lang(user_id, lang):
    conn = db()
    c = conn.cursor()
    c.execute('UPDATE users SET language=? WHERE user_id=?', (lang, user_id))
    conn.commit()
    conn.close()

def get_shop_verified(user_id):
    u = get_user(user_id)
    return u[11] == 1 if u else False

def set_shop_verified(user_id):
    conn = db()
    c = conn.cursor()
    c.execute('UPDATE users SET shop_verified=1 WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = db()
    c = conn.cursor()
    c.execute('SELECT product, qty, price FROM carts WHERE user_id=?', (user_id,))
    items = c.fetchall()
    conn.close()
    return items

def add_to_cart(user_id, product, qty, price):
    conn = db()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO carts (user_id, product, qty, price) VALUES (?,?,?,?)',
              (user_id, product, qty, price))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = db()
    c = conn.cursor()
    c.execute('DELETE FROM carts WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def create_order(user_id, items, total, address, is_referral=0):
    conn = db()
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO orders (user_id, items, total, address, created_at, is_referral) VALUES (?,?,?,?,?,?)',
              (user_id, json.dumps(items, ensure_ascii=False), total, address, created_at, is_referral))
    order_id = c.lastrowid
    c.execute('UPDATE users SET orders=orders+1, first_order_done=1 WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = db()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE id=?', (order_id,))
    o = c.fetchone()
    conn.close()
    return o

def set_order_courier(order_id, courier_id):
    conn = db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status=?, courier_id=? WHERE id=?', ('taken', courier_id, order_id))
    conn.commit()
    conn.close()

# ─── TEXTS ────────────────────────────────────────────────────────────────────

TEXTS = {
    'ru': {
        'welcome': '👋 Привет, {name}!\n\nДобро пожаловать в Chef House 🌿\nТолько премиальные ингредиенты\nОткройте нужный раздел ниже 👇',
        'back': '◀️ В меню',
        'support_captcha': '🤖 Подтвердите что вы не робот\n\nВыберите смайлик: 😊',
        'support_wrong': '❌ Неверно! Попробуйте ещё раз\n\nВыберите смайлик: 😊',
        'support_ok': '✅ Проверка пройдена!\n\n📟 Поддержка Chef House\n\nНапишите ваш вопрос и мы ответим в ближайшее время.\n📩 @Chef_support_cz',
        'news': '📜 Новости Chef House\n\nПодписывайтесь на наш канал:\n👉 @chef_house_cz',
        'reviews': '🏆 Отзывы\n\nЧитайте отзывы в нашем канале:\n👉 @chef_house_cz',
        'business': '💼 Для бизнеса\n\nОптовые заказы и сотрудничество.\nСвяжитесь с менеджером:\n📩 @Chef_support_cz',
        'about': '🌿 О нас\n\nChef House — магазин премиальных ингредиентов в Праге.\n\n🏪 Доставляем по всей Праге\n⚡️ Быстрая курьерская доставка\n💎 Только проверенные поставщики\n\n📩 Поддержка: @Chef_support_cz\n📢 Канал: @chef_house_cz',
        'ideas_prompt': '🔥 ИДЕИ и ПОЖЕЛАНИЯ 🔥\n\nОставьте свои идеи по развитию шопа.\nВаши идеи анонимные!\n\n✍️ Напишите вашу идею:',
        'ideas_sent': '✅ Спасибо! Ваша идея отправлена анонимно.',
        'shop_city': '🛍 Магазин Chef House\n\n🌿 Выберите ваш город:',
        'shop_products': '🛍 Магазин — Прага\n\nВыберите товар:',
        'ref_text': '📊 Реферальная система:\n\n❓ Приведи друга — при его первом заказе ты получишь 🎁 +1 брокколи бесплатно!\n\n💲 Ваш доход: {earnings:.2f} €\n\n🔗 Ваша реферальная ссылка:\n{link}',
        'choose_qty': '📦 Выберите количество:\n\n',
        'added_to_cart': '✅ Добавлено в корзину!\n\n{product}\n{qty} — {price}',
        'cart_empty': '🛒 Корзина пуста',
        'cart_header': '🛒 Ваша корзина:\n\n',
        'cart_total': '\n💰 Итого: {total}',
        'cart_cleared': '🗑 Корзина очищена',
        'ask_address': '📍 Введите адрес доставки (улица, номер дома) или отправьте геопозицию:',
        'order_placed': '✅ Заказ #{order_id} оформлен!\n🚴 Курьер скоро свяжется с вами лично.',
        'order_placed_2': '🌿 Вы стали частью Chef House!\n\nЗакрытое сообщество для клиентов:\n- Эксклюзивные акции\n- Ранний доступ к новинкам\n- Актуальные новости и обновления\n- Прямая связь с командой\n👥 Вступить в группу: t.me/chef_house_cz\n\n📣 Наш канал с новостями и акциями:\n👉 t.me/chef_house_cz',
        'courier_took': '🚴 Курьер взял ваш заказ #{order_id}!\n\nОжидайте доставку.',
        'profile': '📁 Профиль\n\n🔗 ID: {user_id}\n💰 Баланс: {balance:.2f} €\n📦 Заказов: {orders}\n🗓 Дата: {reg_date}',
        'use_buttons': 'Используйте кнопки меню 👇',
        'lang_changed': '🇷🇺 Язык изменён на русский',
    },
    'en': {
        'welcome': '👋 Hello, {name}!\n\nWelcome to Chef House 🌿\nOnly premium ingredients\nChoose a section below 👇',
        'back': '◀️ Back to menu',
        'support_captcha': '🤖 Confirm you are not a robot\n\nChoose the emoji: 😊',
        'support_wrong': '❌ Wrong! Try again\n\nChoose the emoji: 😊',
        'support_ok': '✅ Verified!\n\n📟 Chef House Support\n\nWrite your question and we will answer soon.\n📩 @Chef_support_cz',
        'news': '📜 Chef House News\n\nFollow our channel:\n👉 @chef_house_cz',
        'reviews': '🏆 Reviews\n\nRead reviews in our channel:\n👉 @chef_house_cz',
        'business': '💼 For Business\n\nWholesale orders and partnerships.\nContact our manager:\n📩 @Chef_support_cz',
        'about': '🌿 About Us\n\nChef House — premium ingredients shop in Prague.\n\n🏪 Delivery across Prague\n⚡️ Fast courier delivery\n💎 Verified suppliers only\n\n📩 Support: @Chef_support_cz\n📢 Channel: @chef_house_cz',
        'ideas_prompt': '🔥 IDEAS & SUGGESTIONS 🔥\n\nLeave your ideas here.\nYour ideas are anonymous!\n\n✍️ Write your idea:',
        'ideas_sent': '✅ Thank you! Your idea was sent anonymously.',
        'shop_city': '🛍 Chef House Shop\n\n🌿 Choose your city:',
        'shop_products': '🛍 Shop — Prague\n\nChoose a product:',
        'ref_text': '📊 Referral System:\n\n❓ Bring a friend — on their first order you get 🎁 +1 broccoli for free!\n\n💲 Your earnings: {earnings:.2f} €\n\n🔗 Your referral link:\n{link}',
        'choose_qty': '📦 Choose quantity:\n\n',
        'added_to_cart': '✅ Added to cart!\n\n{product}\n{qty} — {price}',
        'cart_empty': '🛒 Cart is empty',
        'cart_header': '🛒 Your cart:\n\n',
        'cart_total': '\n💰 Total: {total}',
        'cart_cleared': '🗑 Cart cleared',
        'ask_address': '📍 Enter delivery address (street, house number) or send your geolocation:',
        'order_placed': '✅ Order #{order_id} placed!\n🚴 A courier will contact you personally soon.',
        'order_placed_2': '🌿 You have joined Chef House!\n\nExclusive community for customers:\n- Exclusive deals\n- Early access to new products\n- Latest news and updates\n- Direct contact with the team\n👥 Join the group: t.me/chef_house_cz\n\n📣 Our news and deals channel:\n👉 t.me/chef_house_cz',
        'courier_took': '🚴 Courier took your order #{order_id}!\n\nExpect delivery.',
        'profile': '📁 Profile\n\n🔗 ID: {user_id}\n💰 Balance: {balance:.2f} €\n📦 Orders: {orders}\n🗓 Date: {reg_date}',
        'use_buttons': 'Please use the menu buttons 👇',
        'lang_changed': '🇺🇸 Language changed to English',
    }
}

PRODUCTS = {
    'ru': {
        '🥦 Premium broccoli':            [('1 шт', '300 CZK'), ('2 шт', '600 CZK'), ('3 шт', '750 CZK'), ('4 шт', '1000 CZK')],
        '🍄 Wild forest selection':        [('1', '500 CZK'), ('3', '1400 CZK'), ('5', '2200 CZK')],
        '🌸 Мука семян лотоса (Pure 92%)': [('1 кг', '2800 CZK'), ('2 кг', '5300 CZK'), ('3 кг', '7500 CZK')],
        '🎧 Клубная музыка (диски!)':       [('1 мес', '300 CZK'), ('2 мес', '600 CZK'), ('3 мес', '800 CZK'), ('4 мес', '1000 CZK')],
    },
    'en': {
        '🥦 Premium broccoli':             [('1 pc', '12€'), ('2 pc', '24€'), ('3 pc', '30€'), ('4 pc', '40€')],
        '🍄 Wild forest selection':         [('1', '20€'), ('3', '56€'), ('5', '88€')],
        '🌸 Lotus seed flour (Pure 92%)':   [('1 kg', '112€'), ('2 kg', '212€'), ('3 kg', '300€')],
        '🎧 Club music (discs!)':           [('1 mo', '12€'), ('2 mo', '24€'), ('3 mo', '32€'), ('4 mo', '40€')],
    }
}

PRODUCT_PHOTOS = {
    '🥦 Premium broccoli':            'https://i.postimg.cc/J47y33q7/IMG-4367.jpg',
    '🍄 Wild forest selection':        'https://i.postimg.cc/bNYG00Tw/IMG-4357.jpg',
    '🌸 Мука семян лотоса (Pure 92%)': 'https://i.postimg.cc/CMsBfrjL/IMG-5568.jpg',
    '🌸 Lotus seed flour (Pure 92%)':  'https://i.postimg.cc/CMsBfrjL/IMG-5568.jpg',
}

PRODUCT_DESCRIPTIONS = {
    'ru': {
        '🥦 Premium broccoli': (
            '🥦 Premium broccoli\n\n'
            'Выращено с настроением.\n'
            'Собрано для тех, кто чувствует больше.\n\n'
            'Лёгкость, ясность и правильный вайб\n'
            'в каждой детали.\n\n'
            '✨ Clean energy. Right vibe.\n\n'
            '📍 Only Prague\n\n'
            '👇 Выберите количество:'
        ),
        '🍄 Wild forest selection': (
            '🍄 Forest selection\n\n'
            'Более 5 видов на выбор.\n\n'
            'Разные текстуры, оттенки и характер.\n\n'
            'Каждый найдёт своё:\n'
            'от мягкого и лёгкого до насыщенного и глубокого.\n\n'
            'Сезонный сбор. Натуральное качество.\n\n'
            '✨ Choose your vibe.\n\n'
            '👇 Выберите количество:'
        ),
        '🌸 Мука семян лотоса (Pure 92%)': (
            '🌸 Мука семян лотоса (Pure 92%)\n\n'
            'Чистый состав. Лёгкая текстура.\n'
            'Баланс и спокойное ощущение внутри.\n\n'
            'Для тех, кто выбирает качество\n'
            'и ровный ритм без перегрузки.\n\n'
            '✨ A gentle lift. A closer feeling.\n\n'
            '👇 Выберите количество:'
        ),
        '🎧 Клубная музыка (диски!)': (
            '🎧 Клубная музыка\n\n'
            'Физические диски с подборкой\n'
            'клубных треков и ночного звучания.\n\n'
            'Чистый звук. Атмосфера движения.\n'
            'То, что задаёт настроение.\n\n'
            '✨ Late night energy.\n\n'
            '👇 Выберите количество:'
        ),
    },
    'en': {
        '🥦 Premium broccoli': (
            '🥦 Premium broccoli\n\n'
            'Grown with a good mood.\n'
            'Harvested for those who feel more.\n\n'
            'Lightness, clarity and the right vibe\n'
            'in every detail.\n\n'
            '✨ Clean energy. Right vibe.\n\n'
            '📍 Only Prague\n\n'
            '👇 Choose quantity:'
        ),
        '🍄 Wild forest selection': (
            '🍄 Forest selection\n\n'
            '5+ species available.\n'
            'Different textures, shades and character.\n\n'
            'Everyone finds their own:\n'
            'from light and gentle to rich and deep.\n\n'
            'Seasonal harvest. Natural quality.\n\n'
            '✨ Choose your vibe.\n\n'
            '👇 Choose quantity:'
        ),
        '🌸 Lotus seed flour (Pure 92%)': (
            '🌸 Lotus seed flour (Pure 92%)\n\n'
            'Clean composition. Light texture.\n'
            'Balance and a calm feeling inside.\n\n'
            'For those who choose quality\n'
            'and a steady rhythm without overload.\n\n'
            '✨ A gentle lift. A closer feeling.\n\n'
            '👇 Choose quantity:'
        ),
        '🎧 Club music (discs!)': (
            '🎧 Club music\n\n'
            'Physical discs with a curated selection\n'
            'of club tracks and night vibes.\n\n'
            'Clean sound. Movement atmosphere.\n'
            'Sets the mood right.\n\n'
            '✨ Late night energy.\n\n'
            '👇 Choose quantity:'
        ),
    },
}

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────

def main_menu(lang='ru'):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == 'ru':
        markup.row('🛍 Магазин', '🛒 Профиль')
        markup.row('📟 Поддержка', '📜 Новости')
        markup.row('🏆 Отзывы', '💼 Для бизнеса')
        markup.row('💡 Ваши идеи', 'ℹ️ О нас')
        markup.row('💎 Реферальная система')
        markup.row('🇺🇸 Change the language')
    else:
        markup.row('🛍 Shop', '🛒 Profile')
        markup.row('📟 Support', '📜 News')
        markup.row('🏆 Reviews', '💼 For business')
        markup.row('💡 Your ideas', 'ℹ️ About us')
        markup.row('💎 Referral system')
        markup.row('🇷🇺 Сменить язык')
    return markup

def inline_cities(lang='ru'):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🏙 Прага / Prague', callback_data='city_prague'))
    return markup

CAPTCHA_EMOJIS = ['⚗️', '🔒', '🌿', '🍄', '🧊', '🔑', '🚪', '🪪']

def make_shop_captcha():
    import random
    correct = random.choice(CAPTCHA_EMOJIS)
    pool = [e for e in CAPTCHA_EMOJIS if e != correct]
    options = random.sample(pool, 3) + [correct]
    random.shuffle(options)
    return correct, options

def inline_shop_captcha(options):
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = [types.InlineKeyboardButton(e, callback_data=f'scaptcha_{e}') for e in options]
    markup.add(*buttons)
    return markup

def inline_city_after_captcha():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🏙 Прага / Prague', callback_data='city_prague'))
    return markup

def inline_products(lang='ru'):
    markup = types.InlineKeyboardMarkup()
    for i, p in enumerate(PRODUCTS[lang].keys()):
        markup.add(types.InlineKeyboardButton(p, callback_data=f'prod_{i}'))
    return markup

def inline_qty(prod_idx, lang='ru'):
    markup = types.InlineKeyboardMarkup()
    product = list(PRODUCTS[lang].keys())[prod_idx]
    options = PRODUCTS[lang][product]
    for j, (qty, price) in enumerate(options):
        markup.add(types.InlineKeyboardButton(f'{qty} — {price}', callback_data=f'qty_{prod_idx}_{j}'))
    markup.add(types.InlineKeyboardButton('◀️ Назад' if lang == 'ru' else '◀️ Back', callback_data='back_to_products'))
    return markup

def inline_after_cart(lang='ru'):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton('🛒 Корзина', callback_data='show_cart'),
            types.InlineKeyboardButton('🛍 Продолжить', callback_data='continue_shopping'),
        )
        markup.add(
            types.InlineKeyboardButton('✅ Оформить заказ', callback_data='checkout'),
            types.InlineKeyboardButton('◀️ Назад', callback_data='back_to_products'),
        )
    else:
        markup.add(
            types.InlineKeyboardButton('🛒 Cart', callback_data='show_cart'),
            types.InlineKeyboardButton('🛍 Continue', callback_data='continue_shopping'),
        )
        markup.add(
            types.InlineKeyboardButton('✅ Place order', callback_data='checkout'),
            types.InlineKeyboardButton('◀️ Back', callback_data='back_to_products'),
        )
    return markup

def inline_cart_actions(lang='ru'):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton('✅ Оформить заказ', callback_data='checkout'),
            types.InlineKeyboardButton('🗑 Очистить', callback_data='clear_cart')
        )
        markup.add(types.InlineKeyboardButton('🛍 Продолжить покупки', callback_data='continue_shopping'))
    else:
        markup.add(
            types.InlineKeyboardButton('✅ Place order', callback_data='checkout'),
            types.InlineKeyboardButton('🗑 Clear', callback_data='clear_cart')
        )
        markup.add(types.InlineKeyboardButton('🛍 Continue shopping', callback_data='continue_shopping'))
    return markup

def inline_courier_take(order_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Взять заказ', callback_data=f'take_{order_id}'))
    return markup

# ─── STATES ───────────────────────────────────────────────────────────────────

user_states = {}

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def send_main(chat_id, lang, text, chat_type='private'):
    kb = main_menu(lang) if chat_type == 'private' else None
    try:
        bot.send_photo(chat_id, MAIN_PHOTO, caption=text, reply_markup=kb)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=kb)

def send_photo_inline(chat_id, text, markup, chat_type='private'):
    kb = markup if chat_type == 'private' else None
    try:
        bot.send_photo(chat_id, MAIN_PHOTO, caption=text, reply_markup=kb)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=kb)

def parse_price(price_str):
    try:
        if 'CZK' in price_str:
            return int(price_str.split(' CZK')[0].strip())
        elif '€' in price_str:
            return int(price_str.replace('€', '').strip())
    except Exception:
        pass
    return 0

def cart_text(user_id, lang):
    items = get_cart(user_id)
    if not items:
        return TEXTS[lang]['cart_empty'], None
    lines = ''
    total = 0
    for product, qty, price in items:
        lines += f'• {product}\n  {qty} — {price}\n'
        total += parse_price(price)
    first_price = items[0][2] if items else ''
    total_str = f'{total} CZK' if 'CZK' in first_price else f'{total}€'
    text = TEXTS[lang]['cart_header'] + lines + TEXTS[lang]['cart_total'].format(total=total_str)
    return text, inline_cart_actions(lang)

def send_order_to_courier(order_id, user_id, items, address, is_referral):
    print(f'[COURIER] Вызов send_order_to_courier: order_id={order_id}, user_id={user_id}, group={COURIER_GROUP_ID}')
    lines = '\n'.join([f'• {p} {q} — {pr}' for p, q, pr in items])
    ref_note = '\n\n🎁 Реферальный заказ! +1 брокколи бесплатно' if is_referral else ''
    text = (
        f'🛍 Новый заказ #{order_id}\n'
        f'👤 Пользователь: {user_id}\n\n'
        f'{lines}\n\n'
        f'🚴 Доставка: 125-250 CZK (5-10€)\n\n'
        f'📍 Адрес:\n{address}'
        f'{ref_note}'
    )
    # Извлекаем координаты если адрес — геопозиция
    geo_coords = None
    if address.startswith('geo:'):
        try:
            _, coords = address.split(':', 1)
            lat, lon = coords.split(',')
            geo_coords = (float(lat), float(lon))
        except Exception as e_geo:
            print(f'[COURIER] ⚠️ Не удалось распарсить geo: {e_geo}')
    print(f'[COURIER] Текст сообщения: {repr(text[:100])}...')
    print(f'[COURIER] Отправляю простое сообщение (без parse_mode, без reply_markup) в группу {COURIER_GROUP_ID}...')
    try:
        msg = bot.send_message(COURIER_GROUP_ID, text, parse_mode=None)
        print(f'[COURIER] ✅ Текст успешно отправлен, message_id={msg.message_id}')
        try:
            bot.edit_message_reply_markup(COURIER_GROUP_ID, msg.message_id, reply_markup=inline_courier_take(order_id))
            print(f'[COURIER] ✅ Кнопка "Взять заказ" добавлена')
        except Exception as e_btn:
            print(f'[COURIER] ⚠️ Не удалось добавить кнопку: {e_btn}')
        if geo_coords:
            try:
                bot.send_location(COURIER_GROUP_ID, geo_coords[0], geo_coords[1])
                print(f'[COURIER] ✅ Геолокация отправлена: {geo_coords}')
            except Exception as e_loc:
                print(f'[COURIER] ⚠️ Не удалось отправить геолокацию: {e_loc}')
    except Exception as e:
        print(f'[COURIER] ❌ Ошибка отправки в группу {COURIER_GROUP_ID}: {type(e).__name__}: {e}')
        logging.error(f'Courier send error: {type(e).__name__}: {e}')
        print(f'[COURIER] Fallback: отправляю в ADMIN_ID={ADMIN_ID}')
        try:
            bot.send_message(ADMIN_ID, f'⚠️ Не удалось отправить заказ в группу {COURIER_GROUP_ID}!\n\n{text}', reply_markup=inline_courier_take(order_id))
            print(f'[COURIER] Fallback отправлен админу')
        except Exception as e2:
            print(f'[COURIER] ❌ Fallback тоже не удался: {type(e2).__name__}: {e2}')
            logging.error(f'Admin notify error: {e2}')

def check_referral_bonus(user_id):
    u = get_user(user_id)
    if not u:
        return False
    referrer_id = u[7]
    first_order_done = u[10]
    if referrer_id and first_order_done == 0:
        return True
    return False

# ─── ADMIN DEBUG (самый первый handler) ───────────────────────────────────────

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id == ADMIN_ID)
def admin_debug(message):
    groups = get_known_groups()
    if groups:
        lines = '\n'.join([f'<code>{g[0]}</code> — {g[1]} ({g[2]}) [{g[3]}]' for g in groups])
        text = f'💬 chat_id этого чата: <code>{message.chat.id}</code>\n\n📋 known_groups:\n{lines}'
    else:
        text = f'💬 chat_id этого чата: <code>{message.chat.id}</code>\n\n📋 known_groups: пусто'
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ─── GROUP TRACKER (должен быть первым, до handle_text) ───────────────────────

@bot.message_handler(func=lambda m: m.chat.type in ('group', 'supergroup'),
                     content_types=['text', 'photo', 'sticker', 'document', 'location', 'new_chat_members', 'left_chat_member'])
def track_group(message):
    chat = message.chat
    print(f'[GROUP] Сообщение из группы: chat_id={chat.id}, title={chat.title}, type={chat.type}')
    save_group(chat.id, chat.title or '', chat.type)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['id'])
def cmd_id(message):
    if message.chat.type != 'private' or message.from_user.id != ADMIN_ID:
        return
    groups = get_known_groups()
    if groups:
        lines = '\n'.join([f'<code>{g[0]}</code> — {g[1]} ({g[2]})\n{g[3]}' for g in groups])
        bot.send_message(message.chat.id, f'📋 known_groups:\n\n{lines}', parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, '📋 known_groups пуста. Бот ещё не видел групп.')

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    username = message.from_user.username or ''
    first_name = message.from_user.first_name or ''

    # Админ получает список всех известных групп
    if user_id == ADMIN_ID:
        groups = get_known_groups()
        if groups:
            lines = '\n'.join([f'• <code>{g[0]}</code> — {g[1]} ({g[2]}) [{g[3]}]' for g in groups])
            bot.send_message(user_id, f'📋 Известные группы бота:\n\n{lines}', parse_mode='HTML')
        else:
            bot.send_message(user_id, '📋 Бот ещё не видел ни одной группы.\n\nДобавь бота в группу и отправь там любое сообщение.')

    referrer_id = None
    parts = message.text.split()
    if len(parts) > 1:
        try:
            referrer_id = int(parts[1])
            if referrer_id == user_id:
                referrer_id = None
        except Exception:
            pass
    add_user(user_id, username, first_name, referrer_id)
    lang = get_lang(user_id)
    send_main(user_id, lang, TEXTS[lang]['welcome'].format(name=first_name))

# Profile
@bot.message_handler(func=lambda m: m.text in ['🛒 Профиль', '🛒 Profile'])
def profile(message):
    u = get_user(message.from_user.id)
    if not u:
        return start(message)
    lang = u[9]
    text = TEXTS[lang]['profile'].format(
        user_id=u[0], balance=u[3], orders=u[4], reg_date=u[6]
    )
    send_photo_inline(message.chat.id, text, main_menu(lang))

# Support
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
        send_photo_inline(message.chat.id, TEXTS[lang]['support_ok'], main_menu(lang))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('😊', '🙃', '😎')
        markup.row('🤔', '😴', '🥳')
        bot.send_message(message.chat.id, TEXTS[lang]['support_wrong'], reply_markup=markup)

# News
@bot.message_handler(func=lambda m: m.text in ['📜 Новости', '📜 News'])
def news(message):
    lang = get_lang(message.from_user.id)
    send_photo_inline(message.chat.id, TEXTS[lang]['news'], main_menu(lang))

# Reviews
@bot.message_handler(func=lambda m: m.text in ['🏆 Отзывы', '🏆 Reviews'])
def reviews(message):
    lang = get_lang(message.from_user.id)
    send_photo_inline(message.chat.id, TEXTS[lang]['reviews'], main_menu(lang))

# Business
@bot.message_handler(func=lambda m: m.text in ['💼 Для бизнеса', '💼 For business'])
def business(message):
    lang = get_lang(message.from_user.id)
    send_photo_inline(message.chat.id, TEXTS[lang]['business'], main_menu(lang))

# About
@bot.message_handler(func=lambda m: m.text in ['ℹ️ О нас', 'ℹ️ About us'])
def about(message):
    lang = get_lang(message.from_user.id)
    send_photo_inline(message.chat.id, TEXTS[lang]['about'], main_menu(lang))

# Ideas
@bot.message_handler(func=lambda m: m.text in ['💡 Ваши идеи', '💡 Your ideas'])
def ideas(message):
    lang = get_lang(message.from_user.id)
    user_states[message.from_user.id] = 'waiting_idea'
    send_photo_inline(message.chat.id, TEXTS[lang]['ideas_prompt'], main_menu(lang))

# Referral
@bot.message_handler(func=lambda m: m.text in ['💎 Реферальная система', '💎 Referral system'])
def referral(message):
    u = get_user(message.from_user.id)
    if not u:
        return start(message)
    lang = u[9]
    ref_link = f'https://t.me/cheffhouse_shop_bot?start={u[0]}'
    text = TEXTS[lang]['ref_text'].format(earnings=u[8], link=ref_link)
    send_photo_inline(message.chat.id, text, main_menu(lang))

# Language
@bot.message_handler(func=lambda m: m.text == '🇺🇸 Change the language')
def change_to_english(message):
    set_lang(message.from_user.id, 'en')
    first_name = message.from_user.first_name or ''
    send_main(message.chat.id, 'en', TEXTS['en']['welcome'].format(name=first_name))

@bot.message_handler(func=lambda m: m.text == '🇷🇺 Сменить язык')
def change_to_russian(message):
    set_lang(message.from_user.id, 'ru')
    first_name = message.from_user.first_name or ''
    send_main(message.chat.id, 'ru', TEXTS['ru']['welcome'].format(name=first_name))

# Shop entry — капча (один раз)
@bot.message_handler(func=lambda m: m.text in ['🛍 Магазин', '🛍 Shop'])
def shop(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    if get_shop_verified(user_id):
        send_shop_city_photo(message.chat.id, lang)
        return
    correct, options = make_shop_captcha()
    user_states[user_id] = {'state': 'shop_captcha', 'correct': correct}
    text = (
        f'🧪Chef House.\n\n'
        f'🔒 Закрытый доступ.\n\n'
        f'⚠️ Вход возможен только 18+.\n'
        f'‼️ Подтвердите доступ.\n'
        f'Выберите изображение где нарисовано {correct}'
    )
    bot.send_message(message.chat.id, text, reply_markup=inline_shop_captcha(options))

# ─── INLINE CALLBACKS ─────────────────────────────────────────────────────────

def send_shop_city_photo(chat_id, lang):
    try:
        bot.send_photo(chat_id, MAIN_PHOTO, caption=TEXTS[lang]['shop_city'], reply_markup=inline_cities(lang))
    except Exception:
        bot.send_message(chat_id, TEXTS[lang]['shop_city'], reply_markup=inline_cities(lang))

SHOP_PRODUCTS_TEXT = 'Хранилище.\n\nПрага.\nДоступ к подбору открыт.'

def send_shop_products(chat_id, lang):
    try:
        bot.send_photo(chat_id, SHOP_PHOTO, caption=SHOP_PRODUCTS_TEXT, reply_markup=inline_products(lang))
    except Exception:
        bot.send_message(chat_id, SHOP_PRODUCTS_TEXT, reply_markup=inline_products(lang))

@bot.callback_query_handler(func=lambda c: c.data.startswith('scaptcha_'))
def cb_shop_captcha(call):
    user_id = call.from_user.id
    state = user_states.get(user_id)
    chosen = call.data.split('scaptcha_', 1)[1]
    if not (isinstance(state, dict) and state.get('state') == 'shop_captcha'):
        bot.answer_callback_query(call.id)
        return
    correct = state.get('correct')
    if chosen == correct:
        user_states.pop(user_id, None)
        set_shop_verified(user_id)
        bot.answer_callback_query(call.id, '✅')
        lang = get_lang(user_id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_shop_city_photo(call.message.chat.id, lang)
    else:
        bot.answer_callback_query(call.id, '⛔ Неверно')
        correct2, options2 = make_shop_captcha()
        user_states[user_id] = {'state': 'shop_captcha', 'correct': correct2}
        text = (
            f'⛔ Доступ закрыт. Попробуйте снова.\n\n'
            f'Выберите изображение где нарисовано {correct2}'
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=inline_shop_captcha(options2))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=inline_shop_captcha(options2))

@bot.callback_query_handler(func=lambda c: c.data == 'city_prague')
def cb_city(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    send_shop_products(call.message.chat.id, lang)

@bot.callback_query_handler(func=lambda c: c.data == 'back_to_products')
def cb_back_products(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    send_shop_products(call.message.chat.id, lang)

@bot.callback_query_handler(func=lambda c: c.data.startswith('prod_'))
def cb_product(call):
    lang = get_lang(call.from_user.id)
    prod_idx = int(call.data.split('_')[1])
    product = list(PRODUCTS[lang].keys())[prod_idx]
    bot.answer_callback_query(call.id)
    fallback = product + ('\n\n👇 Выберите количество:' if lang == 'ru' else '\n\n👇 Choose quantity:')
    text = PRODUCT_DESCRIPTIONS[lang].get(product, fallback)
    photo = PRODUCT_PHOTOS.get(product, MAIN_PHOTO)
    try:
        bot.send_photo(call.message.chat.id, photo, caption=text, reply_markup=inline_qty(prod_idx, lang))
    except Exception as e:
        logging.error(f'cb_product send error: {e}')
        bot.send_message(call.message.chat.id, text, reply_markup=inline_qty(prod_idx, lang))

@bot.callback_query_handler(func=lambda c: c.data.startswith('qty_'))
def cb_qty(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    prod_idx = int(parts[1])
    qty_idx = int(parts[2])
    product = list(PRODUCTS[lang].keys())[prod_idx]
    qty, price = PRODUCTS[lang][product][qty_idx]
    add_to_cart(call.from_user.id, product, qty, price)
    text = TEXTS[lang]['added_to_cart'].format(product=product, qty=qty, price=price)
    bot.send_message(call.message.chat.id, text, reply_markup=inline_after_cart(lang))

@bot.callback_query_handler(func=lambda c: c.data == 'continue_shopping')
def cb_continue(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    send_shop_products(call.message.chat.id, lang)

@bot.callback_query_handler(func=lambda c: c.data == 'show_cart')
def cb_show_cart(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    text, markup = cart_text(call.from_user.id, lang)
    if markup:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda c: c.data == 'clear_cart')
def cb_clear_cart(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    clear_cart(call.from_user.id)
    bot.send_message(call.message.chat.id, TEXTS[lang]['cart_cleared'])

@bot.callback_query_handler(func=lambda c: c.data == 'checkout')
def cb_checkout(call):
    lang = get_lang(call.from_user.id)
    bot.answer_callback_query(call.id)
    items = get_cart(call.from_user.id)
    if not items:
        bot.send_message(call.message.chat.id, TEXTS[lang]['cart_empty'])
        return
    # Minimum order check: cart total must be >= 1000 CZK / 40€ (+ 125 CZK / 5€ delivery = 50€ minimum)
    total = sum(parse_price(price) for _, _, price in items)
    first_price = items[0][2] if items else ''
    is_czk = 'CZK' in first_price
    min_total = 1000 if is_czk else 40
    if total < min_total:
        msg = ('❌ Минимальный заказ от 50€ (включая доставку 5€)'
               if lang == 'ru' else
               '❌ Minimum order from 50€ (including 5€ delivery)')
        bot.send_message(call.message.chat.id, msg)
        return
    user_states[call.from_user.id] = {'state': 'waiting_address', 'items': items}
    delivery_note = ('🚴 Доставка: 5-10€ (уточнит курьер)\n\n'
                     if lang == 'ru' else
                     '🚴 Delivery: 5-10€ (courier will confirm)\n\n')
    bot.send_message(call.message.chat.id, delivery_note + TEXTS[lang]['ask_address'])

@bot.callback_query_handler(func=lambda c: c.data.startswith('take_'))
def cb_take_order(call):
    order_id = int(call.data.split('_')[1])
    courier_id = call.from_user.id
    order = get_order(order_id)
    if not order:
        bot.answer_callback_query(call.id, 'Заказ не найден')
        return
    if order[6] is not None:
        bot.answer_callback_query(call.id, 'Заказ уже взят')
        return
    set_order_courier(order_id, courier_id)
    bot.answer_callback_query(call.id, '✅ Заказ взят!')
    # Notify client
    user_id = order[1]
    lang = get_lang(user_id)
    try:
        bot.send_message(user_id, TEXTS[lang]['courier_took'].format(order_id=order_id))
    except Exception as e:
        logging.error(f'Notify client error: {e}')
    # Update courier message
    try:
        new_text = call.message.text + f'\n\n✅ Взят курьером: @{call.from_user.username or courier_id}'
        bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass

# ─── ADDRESS / GEO / IDEA HANDLER ─────────────────────────────────────────────

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    state = user_states.get(user_id)
    if isinstance(state, dict) and state.get('state') == 'waiting_address':
        loc = message.location
        address = f'geo:{loc.latitude},{loc.longitude}'
        _finalize_order(user_id, lang, state['items'], address)
    else:
        bot.send_message(message.chat.id, TEXTS[lang]['use_buttons'], reply_markup=main_menu(lang))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    state = user_states.get(user_id)

    if isinstance(state, dict) and state.get('state') == 'waiting_address':
        address = message.text
        items = state['items']
        _finalize_order(user_id, lang, items, address)

    elif state == 'waiting_idea':
        user_states.pop(user_id, None)
        bot.send_message(ADMIN_ID, f'💡 Идея от {user_id}:\n\n{message.text}')
        bot.send_message(message.chat.id, TEXTS[lang]['ideas_sent'], reply_markup=main_menu(lang))

    else:
        bot.send_message(message.chat.id, TEXTS[lang]['use_buttons'], reply_markup=main_menu(lang))

def _finalize_order(user_id, lang, items, address):
    print(f'[ORDER] _finalize_order: user_id={user_id}, address={address}, items={items}')
    is_referral = 1 if check_referral_bonus(user_id) else 0
    order_id = create_order(user_id, items, '—', address, is_referral)
    print(f'[ORDER] Заказ создан: #{order_id}, is_referral={is_referral}')
    user_states.pop(user_id, None)
    clear_cart(user_id)
    # Notify client — message 1
    bot.send_message(user_id, TEXTS[lang]['order_placed'].format(order_id=order_id), reply_markup=main_menu(lang))
    # Notify client — message 2 after 2 seconds
    time.sleep(2)
    try:
        bot.send_message(user_id, TEXTS[lang]['order_placed_2'])
    except Exception:
        pass
    # Send to courier group
    send_order_to_courier(order_id, user_id, items, address, is_referral)
    # Notify admin
    try:
        bot.send_message(ADMIN_ID, f'🛍 Новый заказ #{order_id} от {user_id}\n📍 {address}')
    except Exception:
        pass

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    # Показывать команды только в личных чатах, убрать из групп
    try:
        bot.set_my_commands(
            [types.BotCommand('start', 'Запустить бота')],
            scope=types.BotCommandScopeAllPrivateChats()
        )
        bot.delete_my_commands(scope=types.BotCommandScopeAllGroupChats())
        bot.delete_my_commands(scope=types.BotCommandScopeAllChatAdministrators())
        print('Команды бота настроены: только private чаты')
    except Exception as e:
        print(f'Ошибка настройки команд: {e}')
    # Тест отправки в курьерскую группу при старте
    print(f'[STARTUP] Проверка доступа к курьерской группе {COURIER_GROUP_ID}...')
    try:
        test_msg = bot.send_message(COURIER_GROUP_ID, 'тест', parse_mode=None)
        print(f'[STARTUP] ✅ Тест успешен! message_id={test_msg.message_id}')
    except Exception as e:
        print(f'[STARTUP] ❌ Не удалось отправить тест в группу {COURIER_GROUP_ID}: {type(e).__name__}: {e}')
    print('Chef House бот запущен!')
    bot.polling(none_stop=True)
