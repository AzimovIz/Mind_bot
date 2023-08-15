from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
import json
import os
from dotenv import load_dotenv

if os.path.isfile(".env"):
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
else:
    with open(".env", "w") as file:
        file.write("TOKEN = 'bot_token_here'\nOPENAI_TOKEN = 'openai_token'")
    print("insert bot token in .env file")
    exit(0)

import data_base.utils as db
from gpt_util import chat_gpt_query

prompts = {}

with open("prompts.json", "r", encoding="utf-8") as file:
    prompts = json.load(file)

nl = "\n"


class States(StatesGroup):
    add_marker = State()
    add_note = State()
    search = State()
    del_note = State()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# buttons
@dp.callback_query_handler(lambda callback_query: True, state='*')
async def callback_inline(callback_query, state: FSMContext):
    if str(callback_query.data).startswith('list_marker_'):
        await state.update_data(last_menu=str(callback_query.data))
        markers_kb = InlineKeyboardMarkup()
        if head_marker := str(callback_query.data).split("_")[-1]:
            markers = db.get_child_markers(callback_query.from_user.id, head_marker)
        else:
            markers = db.get_root_markers(callback_query.from_user.id)

        for marker in markers:
            markers_kb.add(InlineKeyboardButton(f"🗄 {marker.value}", callback_data=f"list_marker_{marker.id}"))

        if head_marker:
            markers_kb.row(InlineKeyboardButton("+🗄", callback_data=f"add_marker_{head_marker}"),
                           InlineKeyboardButton("+🗒", callback_data=f"add_note_{head_marker}"))
            exit_marker = db.get_parent_marker(callback_query.from_user.id, head_marker)
            markers_kb.add(InlineKeyboardButton("📖Знания тут", callback_data=f"list_notes_{head_marker}"))
            markers_kb.add(InlineKeyboardButton("❌Удалить этот маркер", callback_data=f"del_marker_{head_marker}"))
            markers_kb.add(InlineKeyboardButton("⬅️", callback_data=f"list_marker_{exit_marker}".replace("None", "")))
            marker_path = "/" + "/".join(db.get_path(callback_query.from_user.id, head_marker))
        else:
            markers_kb.add(InlineKeyboardButton("+🗄", callback_data=f"add_marker_{head_marker}"))
            marker_path = "/"

        await bot.edit_message_text(f"Cписок маркеров\nСейчас в {marker_path}",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id,
                                    reply_markup=markers_kb)

    if str(callback_query.data).startswith('list_notes_'):
        await state.update_data(last_menu=str(callback_query.data))
        notes_kb = InlineKeyboardMarkup()
        head_marker = str(callback_query.data).split("_")[-1]

        notes = db.get_notes(callback_query.from_user.id, head_marker)

        notes_kb.add(InlineKeyboardButton("+🗒", callback_data=f"add_note_{head_marker}"))
        notes_kb.add(InlineKeyboardButton("❌Удалить знание", callback_data=f"del_note_{head_marker}"))
        exit_marker = db.get_parent_marker(callback_query.from_user.id, head_marker)
        notes_kb.add(InlineKeyboardButton("⬅️", callback_data=f"list_marker_{exit_marker}".replace("None", "")))
        marker_path = "/" + "/".join(db.get_path(callback_query.from_user.id, head_marker))
        await bot.edit_message_text(f"Cписок знаний в {marker_path}:\n"
                                    f"{nl.join([i['value'] for i in notes])}",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id,
                                    reply_markup=notes_kb)

    if str(callback_query.data).startswith('add_marker_'):
        await States.add_marker.set()
        if head_marker_id := str(callback_query.data).split("_")[-1]:
            await state.update_data(head_marker_id=head_marker_id)
        else:
            await state.update_data(head_marker_id="")

        await bot.edit_message_text("Название маркера?\nОтмена - /start",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id, )

    if str(callback_query.data).startswith('add_note_'):
        await States.add_note.set()
        if head_marker_id := str(callback_query.data).split("_")[-1]:
            await state.update_data(head_marker_id=head_marker_id)
        else:
            await state.update_data(head_marker_id="")

        await bot.edit_message_text("Текст знания?\nОтмена - /start",
                                    callback_query.from_user.id,
                                    callback_query.message.message_id, )

    if str(callback_query.data).startswith('del_marker_'):
        await state.update_data(last_menu=str(callback_query.data))
        if marker_id := str(callback_query.data).split("_")[-1]:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️", callback_data=f"list_marker_"))
            try:
                db.delete_marker(user_id=callback_query.from_user.id, marker_id=marker_id)
                await bot.edit_message_text("Маркер удален!!!",
                                            callback_query.from_user.id,
                                            callback_query.message.message_id,
                                            reply_markup=kb)
            except Exception as err:
                print(f"From: {callback_query.from_user.id}, {callback_query.data}\n{err}")
                await bot.edit_message_text("Не получилось далить маркер!",
                                            callback_query.from_user.id,
                                            callback_query.message.message_id,
                                            reply_markup=kb)

    if str(callback_query.data).startswith('del_note_'):
        await States.del_note.set()
        await state.update_data(last_menu=str(callback_query.data))
        head_marker = str(callback_query.data).split("_")[-1]

        notes = db.get_notes(callback_query.from_user.id, head_marker)

        marker_path = "/" + "/".join(db.get_path(callback_query.from_user.id, head_marker))
        text = f"Cписок знаний в {marker_path}:\n"
        for i in range(len(notes)):
            text += nl + f"{i}: {notes[i]['value']}"

        text += "\nКакое знание удалить? Напиши номер\nОтмена - /start"
        await bot.edit_message_text(text,
                                    callback_query.from_user.id,
                                    callback_query.message.message_id)

        await state.update_data(in_marker=head_marker)

    await bot.answer_callback_query(callback_query.id)


# comands
@dp.message_handler(commands=["start", "search"], state='*')
async def commands(message: types.Message, state: FSMContext):
    com = message.get_command()

    if com == '/start':
        try:
            await state.finish()
        except:
            pass

        start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Список маркеров", callback_data='list_marker_'))
        await bot.send_message(message.from_user.id,
                               "Привет)",
                               reply_markup=start_kb)

    if com == '/search':
        try:
            await state.finish()
        except:
            pass
        await bot.send_message(message.from_user.id, "Что найти?")
        await States.search.set()


@dp.message_handler(state=States.add_marker)
async def state_case_met(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if head_marker_id := user_data["head_marker_id"]:
        db.create_marker(message.from_user.id, message.text, head_marker_id)
    else:
        db.create_marker(message.from_user.id, message.text)

    exit_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️", callback_data=user_data["last_menu"]))

    await bot.send_message(message.from_user.id,
                           f"Маркер '{message.text}' добавлен!",
                           reply_markup=exit_kb)
    await state.finish()


@dp.message_handler(state=States.add_note)
async def state_case_met(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if not (head_marker_id := user_data["head_marker_id"]):
        await bot.send_message(message.from_user.id,
                               f"Знание '{message.text}' не может быть создано тут(\n"
                               f"Выбери маркер и создай знание в нем", )
    else:
        db.create_note(message.from_user.id, head_marker_id, message.text)
        exit_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️", callback_data=user_data["last_menu"]))
        await bot.send_message(message.from_user.id,
                               f"Знание '{message.text}' добавлено!",
                               reply_markup=exit_kb)
    await state.finish()


@dp.message_handler(state=States.search)
async def state_case_met(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, "Ищу...")
    try:
        tree = db.get_tree(message.from_user.id)
        location = chat_gpt_query(prompts["ask_file_location"].format(message.text, tree))
        data = db.get_notes_from_location(message.from_user.id, location)
        answer = chat_gpt_query(prompts["read_file"].format(message.text, data))
        await bot.send_message(message.from_user.id, str(answer))

    except Exception as err:
        print(f"From: {message.from_user.id}, {message.text}\nErr: {err}")
        await bot.send_message(message.from_user.id, "Что-то пошло не так, попробуте еще раз) - /search")

    await state.finish()


@dp.message_handler(state=States.del_note)
async def state_case_met(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, f"Удаляю...", )
    user_data = await state.get_data()
    if not (marker_id := user_data["in_marker"]):
        await bot.send_message(message.from_user.id,
                               f"Ошибка! Знание не удалено!", )
    else:
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️", callback_data=f"list_notes_{marker_id}"))
        try:
            db.delete_note_pos(user_id=message.from_user.id, marker_id=marker_id, note_pos=message.text)
            await bot.send_message(message.from_user.id,
                                   "Знание удалено!",
                                   reply_markup=kb)
        except Exception as err:
            print(f"From: {message.from_user.id}, {message.text}\n{err}")
            await bot.send_message(message.from_user.id,
                                   "Не получилось далить знание!",
                                   reply_markup=kb)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp)
