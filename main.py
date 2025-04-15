import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = '7525662677:AAESpQayGVVLMj5IkTzhVoQ1pJr9cRxctjA'
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
bot = Bot(token=TOKEN)
dp = Dispatcher()
#CREATE STATE
class States(StatesGroup):
    answer1 = State()
    answer2 = State()
    answer3 = State()
    answer4 = State()
    answer5 = State()
    answer6 = State()
    waiting_for_contact = State()
    start = State()
class Search(StatesGroup):
    choosing_param = State()
    entering_value = State()
    confirm_search = State()
class Cars(StatesGroup):
    viewing = State()
#CREATE TABLE
def create_connect():
    conn = sqlite3.connect('sell_carr')
    return conn
def create_tables():
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars(
        car_id INTEGER PRIMARY KEY,
        car_brand TEXT NOT NULL,
        car_model TEXT NOT NULL,
        car_years INT NOT NULL,
        car_mileage INT NOT NULL,
        car_engine_type TEXT NOT NULL,
        car_city TEXT NOT NULL,
        number INT NOT NULL,
        telegram TEXT NOT NULL,
        my_id INT NOT NULL
        );
    ''')
#CREATE FUNC IN TABLE
async def insert_message(car_brand, car_model, car_years, car_mileage, car_engine_type, car_city, number, telegram, my_id):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO cars (car_brand, car_model, car_years, car_mileage, car_engine_type, car_city, number, telegram, my_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', (car_brand, car_model, car_years, car_mileage, car_engine_type, car_city, number, telegram, my_id))
    conn.commit()
    conn.close()
async def get_message():
    conn = create_connect()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM cars')
    rows = cursor.fetchall()

    conn.close()
    return rows
async def get_info_for_text():
    conn = create_connect()
    cursor = conn.cursor()

    cursor.execute('SELECT car_brand, car_model, car_years, car_mileage, car_engine_type, car_city FROM cars')
    rows = cursor.fetchall()

    conn.close()
    return rows
async def get_my_news(my_id):
    conn = create_connect()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM cars WHERE my_id = ?', (my_id,))
    rows = cursor.fetchall()

    conn.close()
    return rows
async def get_car_id():
    conn = create_connect()
    cursor = conn.cursor()

    cursor.execute('SELECT car_id FROM CARS')
    rows = cursor.fetchall()
    conn.close()
    return rows
async def get_news_by_param(param_name: str,param_value: str):
    conn = create_connect()
    cursor = conn.cursor()
    query = f'SELECT * FROM cars WHERE {param_name} = ?'
    cursor.execute(query,(param_value,))
    rows = cursor.fetchall()

    conn.close()
    return rows
async def search_with_multiple_params(filters: dict):
    conn = create_connect()
    cursor = conn.cursor()

    query = "SELECT * FROM cars WHERE "
    query += " AND ".join([f"{k} = ?" for k in filters.keys()])
    values = list(filters.values())

    cursor.execute(query, values)
    rows = cursor.fetchall()
    conn.close()
    return rows
#CALL CREATE DATABASE, TABLES in DATABASE
create_connect()
create_tables()
#create translate for table
PARAM_TRANSLATIONS = {
    "car_brand": "Марка автомобиля",
    "car_model": "Модель",
    "car_years": "Год выпуска",
    "car_city": "Город",
    "car_engine_type": "Тип двигателя",
}

#CREATE KEYBOARD BUTTON FOR START
kb = {
    'kb_start': InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text='Разместить объявление',callback_data='new_news')],
                                     [InlineKeyboardButton(text='Посмотреть авто',callback_data='views_car')],
                                     [InlineKeyboardButton(text='Поиск по параметрам',callback_data='find_values')],
                                     [InlineKeyboardButton(text='Мои объявления',callback_data='my_news')]
                                      ]),
    'send_contact': ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📞 Отправить контакт', request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    ),
    'back': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back')]
    ]),
    'param_keyboard': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Марка Автомобиля', callback_data='car_brand')],
        [InlineKeyboardButton(text='Модель', callback_data='car_model')],
        [InlineKeyboardButton(text='Год выпуска', callback_data='car_years')],
        [InlineKeyboardButton(text='Пробег', callback_data='car_mileage')],
        [InlineKeyboardButton(text='Тип двигателя', callback_data='car_engine_type')],
        [InlineKeyboardButton(text='Откуда продается', callback_data='car_city')]
    ]),
    'confirm_keyboard': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить ещё параметр', callback_data='add_more')],
        [InlineKeyboardButton(text='Начать поиск', callback_data='search')]
    ]),
}
#go back
async def go_back(message):
    await message.answer('Выберите следующее действие:', reply_markup=kb['kb_start'])
#FIST COMMAND START
@dp.message(CommandStart())
async def cmd_start(message):
    await message.answer('Здраствуйте, добро пожаловать в бота👋', reply_markup=kb['kb_start'])
#CREATE HANDLER 'new_news'
@dp.callback_query(F.data == 'new_news')
async def create_broadcast(callback, state):
    await callback.message.answer('Что бы создать объявление вам нужно:\n'
                                  'Пошагово вписать данные:\n')
    await callback.message.answer('Введите марку авто ')
    await state.set_state(States.answer1)
    await callback.answer()
#fill 1 field 'brand car'
@dp.message(States.answer1)
async def filling_brand_field(message, state):
    await state.update_data(car_brand=message.text)
    await message.answer(f'Введите модель {message.text}')
    await state.set_state(States.answer2)
#fill 2 field 'model car'
@dp.message(States.answer2)
async def filling_mode_field(message, state):
    await state.update_data(car_model=message.text)
    data = await state.get_data()
    car_brand = data['car_brand']
    await message.answer(f'Введите год выпуска {car_brand}')
    await state.set_state(States.answer3)
#fill 3 field 'years_car'
@dp.message(States.answer3)
async def filling_years_field(message, state):
    await state.update_data(car_years=message.text)
    data = await state.get_data()
    car_brand = data['car_brand']
    await message.answer(f'Введите пробег {car_brand}')
    await state.set_state(States.answer4)
#fill 4 field 'car_mileage'
@dp.message(States.answer4)
async def filling_mileage_field(message, state):
    await state.update_data(car_mileage=message.text)
    data = await state.get_data()
    car_brand = data['car_brand']
    await message.answer(f'Введите тип двигателя {car_brand}')
    await state.set_state(States.answer5)
#fill 4 field car_type_engine
@dp.message(States.answer5)
async def filling_car_type_engine_field(message, state):
    await state.update_data(car_engine_type=message.text)
    data = await state.get_data()
    car_brand = data['car_brand']
    await message.answer(f'Введите город откуда продаете авто')
    await state.set_state(States.answer6)
#fill 5 field city_car
@dp.message(States.answer6)
async def filling_car_city_field(message, state):
    await state.update_data(car_city=message.text)
    data = await state.get_data()
    car_brand = data['car_brand']
    car_model = data['car_model']
    car_years = data['car_years']
    car_mileage = data['car_mileage']
    car_engine_type = data['car_engine_type']
    car_city = data['car_city']
    await message.answer(f'Ваше объявление готово:\n'
                         f'Марка автомобиля: {car_brand}\n'
                         f'Модель: {car_model}\n'
                         f'Год выпуска: {car_years}\n'
                         f'Пробег: {car_mileage}\n'
                         f'Тип двигателя: {car_engine_type}\n'
                         f'Город: {car_city}\n')
    await message.answer('📞 Отправьте свой контакт для завершения:', reply_markup=kb['send_contact'])
    await state.set_state(States.waiting_for_contact)
#handler wait for contact
@dp.message(States.waiting_for_contact)
async def wait_contact(message, state):
    if not message.contact:
        await message.answer("⚠️ Пожалуйста, используйте кнопку «📞 Отправить контакт» для отправки номера.")
        return
    data = await state.get_data()

    number = message.contact.phone_number
    telegram = message.from_user.username or None
    my_id = message.from_user.id
    await insert_message(
        car_brand=data['car_brand'].lower().strip(),
        car_model=data['car_model'].lower().strip(),
        car_years=data['car_years'].lower().strip(),
        car_mileage=data['car_mileage'].lower().strip(),
        car_engine_type=data['car_engine_type'].lower().strip(),
        car_city=data['car_city'].lower().strip(),
        number=number,
        telegram=telegram.lower(),
        my_id=my_id
    )

    await message.answer("✅ Объявление успешно добавлено! Спасибо 🙌", reply_markup=ReplyKeyboardRemove())
    await message.answer('Вернуться в главное меню😼:', reply_markup=kb['back'])
    await state.clear()
#handler for exit on main
@dp.callback_query(F.data == 'back')
async def back(callback):
    await go_back(callback.message)
    await callback.answer()
#create handler for my_news
@dp.callback_query(F.data == 'my_news')
async def my_news(callback):
    my_id = callback.from_user.id
    rows = await get_my_news(my_id)

    if rows:
        text = "\n\n".join(
            [f"Объявления:\n🚗 Марка: {r[1]}\n📍 Модель: {r[2]}\n📅 Год: {r[3]}" for i, r in enumerate(rows)]
        )
    else:
        text = "У вас пока нет объявлений."

    await callback.message.answer(text)
    await callback.answer()
#create "find by parametrs"
@dp.callback_query(F.data == 'find_values')
async def find_values(callback, state):
    await callback.message.answer('Выберите по каким параметрам будем искать:', reply_markup=kb['param_keyboard'])
    await state.set_state(Search.choosing_param)
#state confirm_search
@dp.callback_query(Search.choosing_param, F.data.in_(['car_brand', 'car_model', 'car_years', 'car_mileage', 'car_engine_type', 'car_city']))
async def choose_param(callback, state):
    param = callback.data
    await state.update_data(current_param=param)
    pretty_name = PARAM_TRANSLATIONS.get(param, param)
    await callback.message.answer(f"Введите значение для {pretty_name}:")
    await state.set_state(Search.entering_value)
    await callback.answer()
#state entering_value
@dp.message(Search.entering_value)
async def entering_value(message,state):
    data = await state.get_data()
    current_param = data['current_param']

    filters = data.get('filters', {})
    filters[current_param] = message.text.lower()
    await state.update_data(filters=filters)
    await message.answer("Хотите добавить ещё параметр или начать поиск?", reply_markup=kb['confirm_keyboard'])
    await state.set_state(Search.confirm_search)
#state confirm_search
@dp.callback_query(Search.confirm_search)
async def confirm_search(callback, state):
    global url
    if callback.data == 'search':
        data = await state.update_data()
        filters = data.get('filters', {})

        rowse = await get_message()
        for row in rowse:
            telegram = row[8]

        numbers = await get_message()
        for number in numbers:
            num = number[7]

        rows = await search_with_multiple_params(filters)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Написать', callback_data='telegrams')]
        ])
        number_phone = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Узнать номер телефона', callback_data='telephone')]
        ])
        all_buttons = keyboard.inline_keyboard + number_phone.inline_keyboard
        keyboard_global = InlineKeyboardMarkup(inline_keyboard=all_buttons)
        if not rows:
            await callback.message.answer("❌ Ничего не найдено.")
        else:
            text = "\n\n".join([f"🚗 {r[1]} {r[2]} | {r[3]} год | {r[6]}" for r in rows])
            await callback.message.answer(f"🔍 Найдено:\n\n{text}", reply_markup=keyboard_global)
            @dp.callback_query(F.data == 'telephone')
            async def telephone(callback):
                await callback.message.answer(f"🔍 Номер телефона: +{num}",reply_markup=kb['back'])
                await callback.answer()
            @dp.callback_query(F.data == 'telegrams')
            async def telegrams(callback):
                await callback.message.answer(f"🔍 Телеграм: <a href='https://t.me/{telegram}'>нажми что бы написать!</a>",parse_mode='html', disable_web_page_preview=True, reply_markup=kb['back'])
                await callback.answer()
        await state.clear()

    elif callback.data == 'add_more':
        await callback.message.answer("Выберите следующий параметр:", reply_markup=kb['param_keyboard'])
        await state.set_state(Search.choosing_param)
    await callback.answer()
#realizate 2 button (views auto)
@dp.callback_query(F.data == 'views_car')
async def start_viewing(callback, state):
    await state.set_state(Cars.viewing)
    await state.update_data(index=0)
    await show_car(callback, 0)
async def show_car(message, index: int):
    cars = await get_info_for_text()


    if index >= len(cars):
        await message.answer('🚫 Больше машин нет.')
        return
    car = cars[index]
    text = (
        f"🚘 Марка: {car[0]}\n"
        f"📍 Модель: {car[1]}\n"
        f"📅 Год выпуска: {car[2]}\n"
        f"📊 Пробег: {car[3]} км\n"
        f"⚙️ Тип двигателя: {car[4]}\n"
        f"🏙 Город: {car[5]}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➡️ Дальше', callback_data=f"next_{index + 1}")],
        [InlineKeyboardButton(text='⛔️ Стоп', callback_data='stop')]
    ])
    await message.answer(text, reply_markup=keyboard)
@dp.callback_query(F.data.startswith("next_"))
async def next_car(callback, state):
    index = int(callback.data.split('_')[1])
    await state.update_data(index=index)
    await show_car(callback.message, index)
    await callback.answer()
@dp.callback_query(F.data == 'stop')
async def stop(callback, state):
    await state.clear()
    await callback.message.answer("🔚 Просмотр остановлен.")
    await callback.answer()

#create bot
async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бота выключили...')
