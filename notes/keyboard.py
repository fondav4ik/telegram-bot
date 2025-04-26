from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

def kb_list():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Показать список команд', callback_data='show_cmd_list')]
    ])
def edit_description_on_note():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить', callback_data='edit')]
    ])