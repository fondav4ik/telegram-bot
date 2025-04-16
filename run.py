import logging
import asyncio
import sys
import datetime
import sqlite3
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = ''

# Create DB connection
def create_connect():
    conn = sqlite3.connect('reminder.db')
    return conn

# Create reminders table if not exists
def create_table():
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminder(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT,
        text TEXT NOT NULL,
        time TEXT NOT NULL
    );''')
    conn.commit()
    conn.close()

# Get user's reminder
async def get_message(user_id):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminder WHERE user_id = ?;', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

# Get all reminders for a user
async def get_text_time(user_id):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT text, time FROM reminder WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    return rows

# Insert a new reminder
async def insert_message(user_id, text, time):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute(''' INSERT INTO reminder (user_id, text, time) VALUES (?, ?, ?);''', (user_id, text, time))
    conn.commit()
    conn.close()

# Send reminders at the scheduled time
async def send_reminders():
    print("🟢 send_reminders started!")

    while True:
        now = datetime.now().strftime("%H:%M")
        print(f"⏰ Current time: {now}")

        reminders = get_reminders()
        print(f"🔍 Found {len(reminders)} reminders")

        for reminder_id, user_id, text, time in reminders:
            if now == time:
                try:
                    await bot.send_message(user_id, f"🔔 Reminder: {text} — {time}")
                    print(f"✅ Sent to user {user_id}")
                    await del_reminder_id_by(reminder_id, user_id)
                except Exception as e:
                    print(f"❌ Error: {e}")
        await asyncio.sleep(60)

# Startup task
async def on_startup():
    print("🚀 Starting send_reminders")
    asyncio.create_task(send_reminders())

create_connect()
create_table()

# Inline Keyboard Markups
kb = {
    'start': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Add Reminder', callback_data='add_reminder')],
        [InlineKeyboardButton(text='📋 My Reminders', callback_data='my_reminder')],
        [InlineKeyboardButton(text='❌ Delete Reminder', callback_data='del_reminder')],
        [InlineKeyboardButton(text='🕒 Change Time', callback_data='change_time')],
        [InlineKeyboardButton(text='ℹ️ Help', callback_data='help')],
    ]),
    'del_reminders': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Delete one from list', callback_data='del_reminders')]
    ]),
    'back': InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Back', callback_data='back')]
    ])
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Get all reminders
def get_reminders():
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, text, time FROM reminder")
    reminders = cursor.fetchall()
    conn.close()
    return reminders

# States for FSM
class States(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_id = State()
    waiting_for_change_time = State()
    waiting_for_new_time = State()

# Start command handler
@dp.message(CommandStart())
async def cmd_start(message):
    await message.answer('Hi, I am your reminder bot!', reply_markup=kb['start'])

# Add reminder callback
@dp.callback_query(F.data == 'add_reminder')
async def add_reminder(callback, state):
    await callback.message.answer('What do you want to be reminded of?')
    await state.set_state(States.waiting_for_text)
    await callback.answer()

# Handle text input for reminder
@dp.message(States.waiting_for_text)
async def waiting_for_next(message, state):
    text = message.text
    await state.update_data(text=text)
    await message.answer('When should I remind you? (HH:MM format)')
    await state.set_state(States.waiting_for_time)

# Handle time input for reminder
@dp.message(States.waiting_for_time)
async def waiting_for_time(message: Message, state: FSMContext):
    time = message.text.strip()
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time):
        await message.answer("⛔ Invalid time format. Please use HH:MM (e.g., 08:30).")
        return
    await state.update_data(time=time)

    data = await state.get_data()
    text = data['text']
    time = data['time']
    user_id = message.from_user.id
    await insert_message(user_id, text, time)

    await message.answer(f'Reminder added successfully\nChoose next action', reply_markup=kb['start'])

# View reminders
@dp.callback_query(F.data == 'my_reminder')
async def view_my_reminder(callback, state):
    user_id = callback.from_user.id
    rows = await get_text_time(user_id)

    if rows:
        text = "\n\n".join([f"🔔 Reminder {i + 1}:\n🕒 {r[1]} — {r[0]}" for i, r in enumerate(rows)])
    else:
        text = "You have no reminders."

    await callback.message.answer(text, reply_markup=kb['back'])
    await callback.answer()

# Go back to start
@dp.callback_query(F.data == 'back')
async def back(callback):
    await callback.message.answer('Choose next action:', reply_markup=kb['start'])
    await callback.answer()

# Delete reminder callback
@dp.callback_query(F.data == 'del_reminder')
async def del_reminder(callback, state):
    await callback.message.answer('Enter the reminder number to delete!')
    await view_my_reminder(callback, state)
    await state.set_state(States.waiting_for_id)

# Handle reminder ID for deletion
@dp.message(States.waiting_for_id)
async def waiting_for_id(message, state):
    index = message.text
    user_id = message.from_user.id
    await state.update_data(index=index)

    await del_reminder_id_by(index, user_id)

    await message.answer('Reminder deleted!')
    await message.answer('Choose next action:', reply_markup=kb['start'])

# Delete reminder from database
async def del_reminder_id_by(reminder_id, user_id):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM reminder WHERE user_id = ? LIMIT 1 OFFSET ?', (user_id, int(reminder_id) - 1))
    result = cursor.fetchone()

    if result:
        reminder_id = result[0]
        cursor.execute("DELETE FROM reminder WHERE id = ?", (reminder_id,))
        conn.commit()

# Help callback
@dp.callback_query(F.data == 'help')
async def helps(callback):
    await callback.message.answer('I am your reminder bot. Here is what I can do:\n'
                                  '- ➕ <b>Add Reminder</b>\n'
                                  '- 📋 <b>My Reminders</b>\n'
                                  '- ❌ <b>Delete Reminder</b>\n'
                                  '- 🕒 <b>Change Time</b>\n'
                                  '- ℹ️ <b>Help</b>\n', parse_mode='html', reply_markup=kb['back'])

# Change time callback
@dp.callback_query(F.data == 'change_time')
async def changes_time(callback, state):
    await view_my_reminder(callback,state)
    await callback.message.answer('Enter the reminder index to change time')
    await state.set_state(States.waiting_for_change_time)
    await callback.answer()

# Handle reminder index for time change
@dp.message(States.waiting_for_change_time)
async def changes_times(message, state):
    reminder_id = message.text
    await state.update_data(reminder_id=reminder_id)
    await message.answer('Enter new time in HH:MM format')
    await state.set_state(States.waiting_for_new_time)

# Handle new time for reminder
@dp.message(States.waiting_for_new_time)
async def new_times(message,state):
    new_time = message.text
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", new_time):
        await message.answer("⛔ Invalid time format. Please use HH:MM (e.g., 08:30).")
        return
    await state.update_data(new_time=new_time)
    user_id = message.from_user.id
    data = await state.get_data()
    reminder_id = data['reminder_id']
    await change_time_in_bd(user_id, reminder_id, new_time)
    await message.answer(f"✅ Reminder time changed to {new_time}!", reply_markup=kb['start'])
    await state.clear()

# Update time in database
async def change_time_in_bd(user_id, reminder_index, new_time):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM reminder WHERE user_id = ? LIMIT 1 OFFSET ?", (user_id, int(reminder_index) - 1))
    row = cursor.fetchone()

    if row:
        reminder_id = row[0]
        cursor.execute("UPDATE reminder SET time = ? WHERE id = ?", (new_time, reminder_id))
        conn.commit()

    cursor.close()
    conn.close()

# Debug command for database
@dp.message(Command("debug"))
async def debug_db(message: Message):
    conn = create_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminder WHERE user_id = ?", (message.from_user.id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        await message.answer("❌ No reminders in database.")
    else:
        msg = "\n".join([f"🆔 {r[0]} | {r[2]} at {r[3]}" for r in rows])
        await message.answer(f"✅ Found:\n{msg}")

# Main entry point
async def main():
    logging.info("Bot is starting...")

    # Start reminders task
    asyncio.create_task(send_reminders())

    # Start polling the bot
    await dp.start_polling(bot)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped...')
