from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

start_choice: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Мой список', callback_data='my_list'),
        ],
        [
            InlineKeyboardButton(text='Добавить в список', callback_data='add_paper'),
            InlineKeyboardButton(text='Удалить из списка', callback_data='del_paper')
        ],
        [
            InlineKeyboardButton(text='Выход', callback_data='cancel')
        ]
    ]
)
