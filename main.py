#! /usr/bin/python3
# -*- coding: utf-8 -*-

from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db_work
from config import TG_TOKEN, ADMIN, LIST_FOR_MESSAGE
import logging
import msg_text
import subsidiary
import inline

# тест гита

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=storage)

commands = ['start', 'help', 'gods', 'ask_users']


@dp.message_handler(commands=commands)
async def send_welcome(message: types.Message):
    if message.chat.type == 'private':
        if message.text == '/start':
            await message.answer(msg_text.start_message)
            db_work.chek_user(message.from_user)
        if message.text == '/help':
            await message.answer(msg_text.help_message)
        if message.from_user.id in ADMIN:
            if message.text == '/gods':
                await message.answer(msg_text.gods_message)
            if message.text == '/ask_users':
                date = db_work.get_count_user_bot()
                await message.answer(f'Общее количество подписчиков: {date} чел.')


@dp.message_handler(commands=['ask_paper', 'ask_paper1', 'ask_paper4'])
async def get_paper(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in ADMIN:
            if message.text == '/ask_paper':
                data = db_work.get_paper('7 day')
                msg_data = 'За последнюю неделю народ интересовался следующими тикерам: \n'
                for i in data:
                    msg_data = msg_data + i[0].strip() + f' в количестве {i[1]} раз \n'
                await message.answer(msg_data)
            if message.text == '/ask_paper1':
                data = db_work.get_paper('1 hour')
                msg_data = 'За последний час народ интересовался следующими тикерам: \n'
                for i in data:
                    msg_data = msg_data + i[0].strip() + f' в количестве {i[1]} раз \n'
                await message.answer(msg_data)
            if message.text == '/ask_paper4':
                data = db_work.get_paper('4 hour')
                msg_data = 'За последние 4 часа народ интересовался следующими тикерам: \n'
                for i in data:
                    msg_data = msg_data + i[0].strip() + f' в количестве {i[1]} раз \n'
                await message.answer(msg_data)


@dp.message_handler(commands=['list'])
async def inline_buttons(message: types.Message):
    if message.chat.type == 'private':
        await message.answer('Выберите действие', reply_markup=inline.start_choice)


@dp.message_handler(content_types='text')
async def send_text(message: types.Message, url_true=False):
    if message.chat.type == 'private':
        result = subsidiary.subs(message.text)
        result.get_query()
        if len(result.ticket) <= 6 and not message.text.startswith(('/', '!')):
            result.get_parser_finviz()
            if result.final_short:
                result.get_parser_yahoo()
                if result.final_options:
                    result.get_message
                    await message.answer(result.message)
                    db_work.chek_paper(result.ticket)
                else:
                    await message.answer('По данному тикеру нет информации об опционах на указанный период.')
            else:
                await message.answer(
                    'Проверьте правильность тикера. Возможно акция не торгуется на американской бирже.')
        else:
            await message.answer('Проверьте правильность тикера.')


"""НАЧАЛО Описываем взаимодействия с inline кнопками"""


class FSMAdmin(StatesGroup):
    add_paper = State()
    del_paper = State()


@dp.message_handler(content_types=['text'], state=FSMAdmin.add_paper)
async def load_add_paper(message: types.Message, state: FSMContext):
    async with state.proxy() as date:
        date['paper'] = '#' + message.text.lower()
        date['user_id'] = message.from_user.id
        result = subsidiary.subs(message.text.lower())
        result.get_query()
        if len(result.ticket) <= 6 and not message.text.startswith(('/', '!')):
            chek_paper = db_work.chek_paper_in_wl(date['user_id'], date['paper'])
            result.get_parser_finviz()
            if result.final_short:
                if len(chek_paper) == 0:
                    db_work.add_paper_in_wl(date['user_id'], date['paper'])
                    await message.answer(f"Добавлен тикер {date['paper']}")
                else:
                    await message.answer(f"Тикер {date['paper']} уже добавлен в избранное")
            else:
                await message.answer('Проверьте правильность тикера. Возможно акция не торгуется на американской бирже.')
        else:
            await message.answer('Проверьте правильность тикера')
    await message.answer('Действие:', reply_markup=inline.start_choice)
    await state.finish()


@dp.message_handler(content_types=['text'], state=FSMAdmin.del_paper)
async def load_del_paper(message: types.Message, state: FSMContext):
    async with state.proxy() as date:
        date['paper'] = '#' + message.text.lower()
        date['user_id'] = message.from_user.id
        chek_p = db_work.chek_paper_in_wl(date['user_id'], date['paper'])
        if len(chek_p) != 0:
            db_work.del_paper_in_wl(date['user_id'], date['paper'])
            await message.answer(f"Удален тикер {date['paper']}")
        else:
            await message.answer(f"Тикер {date['paper']} не найден в избранном")
    await message.answer('Действие:', reply_markup=inline.start_choice)
    await state.finish()


@dp.callback_query_handler(text=['add_paper', 'del_paper'])
async def ask_paper(call: types.CallbackQuery):
    if call.data == 'add_paper':
        await FSMAdmin.add_paper.set()
    elif call.data == 'del_paper':
        await FSMAdmin.del_paper.set()
    await bot.send_message(chat_id=call.from_user.id, text="Укажите тикер")


@dp.callback_query_handler(text='my_list')
async def get_my_list(call: types.CallbackQuery):
    my_list = db_work.get_my_watch_list(call.from_user.id)
    prt_message = 'В избранном находятся следующие тикеры: \n'
    for i in my_list:
        shorts = subsidiary.subs(i[0].strip()[1:])
        shorts.ticket = i[0].strip()[1:]
        shorts.get_parser_finviz()
        prt_message = prt_message + '#' + str(shorts.final_short['tiker']) + ' ' + str(shorts.final_short['title']) + ' ' \
            '' + str(shorts.final_short['volume']) + '\n'

    await bot.send_message(chat_id=call.from_user.id, text=prt_message)


@dp.callback_query_handler(text='cancel')
async def cancel_work(call: types.CallbackQuery):
    await call.answer('Вы отменили операцию')
    await call.message.edit_reply_markup()


"""КОНЕЦ Взаимодействия с inline кнопками"""

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
