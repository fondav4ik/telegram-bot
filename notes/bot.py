import logging
import asyncio
import sys
import sqlite3
import random

from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.init_db import __init__db
from database.database import select_user_id_in_users, insert_user_in_db, insert_note_in_db, select_all_notes, delete_note_with_index
from state import Authorizer, AppenderNotes, Deleter
from keyboard import kb_list, edit_description_on_note

TOKEN =
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

bot = Bot(token=TOKEN)
dp = Dispatcher()

router = Router()


@router.message(CommandStart())
async def cmd_start(message, state):
    user_id = message.from_user.id

    if not select_user_id_in_users(user_id):
        await message.answer('Для начало нужно зарегистрироваться')
        await message.answer('Напиши что либо в чат!')
        await state.set_state(Authorizer.auth)
    else:
        await message.answer('Добро пожаловать, я бот который записывает ваши заметки! Нажми на кнопочку что бы увидеть мои команды', reply_markup =kb_list())


@router.message(Authorizer.auth)
async def process_auth(message,state):
    tg_id = message.from_user.id

    user_name = message.from_user.username

    if user_name is None:
        user_name = 'Отсутствует'

    insert_user_in_db(tg_id, user_name)
    await message.answer('Вы успешно зарегистрировались, выберите следующее действие', reply_markup=kb_list())

@router.callback_query(F.data == 'show_cmd_list')
async def show_list(callback):
    await callback.message.answer(f'/start — приветственное сообщение и регистрация пользователя\n'
                                  f'/help — показать список всех доступных команд\n'
                                  f'/add_note — добавить новую заметку\n'
                                  f'/list_notes — показать все свои заметки\n'
                                  f'/delete_note — удалить выбранную заметку')
    await callback.answer()


@router.message(Command('help'))
async def cmd_help(message):
    await message.answer(f'/start — приветственное сообщение и регистрация пользователя\n'
                                      f'/help — показать список всех доступных команд\n'
                                      f'/add_note — добавить новую заметку\n'
                                      f'/list_notes — показать все свои заметки\n'
                                      f'/delete_note — удалить выбранную заметку')


@router.message(Command('add_note'))
async def append_notes(message, state):
    await message.answer('Введите текст заметки')
    await state.set_state(AppenderNotes.description)
@router.message(AppenderNotes.description)
async def process_append_description(message,state):
    await message.answer(f'Текст получен: {message.text}', reply_markup=edit_description_on_note())
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    user_id = message.from_user.id
    insert_note_in_db(user_id, message.text, created_at)

    await message.answer(
        f'Заметка добавлена:\n\n'
        f'ID: {user_id}\n'
        f'Текст: {message.text}\n'
        f'Время создания: {created_at}',
        reply_markup=kb_list()
    )

    await state.clear()
@router.callback_query(F.data == 'edit')
async def process_edit_description(callback, state):
    await callback.message.answer('Введите текст заметки:')
    await state.set_state(AppenderNotes.description)
    await callback.answer()


@router.message(Command('list_notes'))
async def cmd_list_notes_in_process(message):
    user_id = message.from_user.id
    rows = select_all_notes(user_id)
    if not rows:
        await message.answer("У вас пока нет заметок.")
        return

    for i, row in enumerate(rows):
        await message.answer(f'{i}. Заметка пользователя {row[1]}\n{row[2]}\nЗаметка создана в {row[3]}', reply_markup=kb_list())


@router.message(Command('delete_note'))
async def del_note(message, state):
    user_id = message.from_user.id
    rows = select_all_notes(user_id)

    if not rows:
        await message.answer("У вас пока нет заметок для удаления.")
        return

    await message.answer('Вот ваши заметки. Напишите номер заметки, которую хотите удалить:')

    for i, row in enumerate(rows, start=1):
        await message.answer(f'{i}. {row[2]} (Создана: {row[3]})')
    await state.set_state(Deleter.index)
@router.message(Deleter.index)
async def process_delete_index(message, state):
    try:
        index = int(message.text)
    except ValueError:
        await message.answer('Введите цифру')
        return

    is_deleted = delete_note_with_index(index)

    if is_deleted:
        await message.answer('Заметка успешно удалена!', reply_markup=kb_list())
        await state.clear()
    else:
        await message.answer('Заметка с таким ID не найдена.')


async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    __init__db()
    try:
        dp.include_router(router=router)
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бота выключили...')
