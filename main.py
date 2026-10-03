"""Стартовый Telegram-бот для botdepo: заметки.

Что показывает:
- команды (/start, /list) и обычные текстовые сообщения;
- инлайн-кнопки и обработку нажатий;
- хранение данных в /data (см. storage.py).

Токен бот получает из переменной окружения BOT_TOKEN — на botdepo её
подставляет панель, локально задайте сами (см. README).
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

dp = Dispatcher()


def notes_view(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """Текст со списком заметок и кнопки «удалить» под ним."""
    notes = storage.list_notes(user_id)
    if not notes:
        return "Заметок пока нет. Просто пришлите мне текст.", None
    lines = [f"{i}. {text}" for i, (_, text) in enumerate(notes, start=1)]
    buttons = [
        InlineKeyboardButton(text=f"🗑 {i}", callback_data=f"del:{note_id}")
        for i, (note_id, _) in enumerate(notes, start=1)
    ]
    rows = [buttons[i : i + 5] for i in range(0, len(buttons), 5)]
    return "Ваши заметки:\n\n" + "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот-заметки.\n\n"
        "Пришлите любой текст — сохраню его.\n"
        "/list — показать заметки и удалить ненужные."
    )


@dp.message(Command("list"))
async def show_list(message: Message) -> None:
    text, keyboard = notes_view(message.from_user.id)
    await message.answer(text, reply_markup=keyboard)


@dp.message(F.text)
async def save(message: Message) -> None:
    if message.text.startswith("/"):
        await message.answer("Не знаю такую команду. Есть /start и /list.")
        return
    count = storage.add_note(message.from_user.id, message.text)
    await message.answer(f"Сохранил. Всего заметок: {count}. /list — посмотреть.")


@dp.callback_query(F.data.startswith("del:"))
async def delete(callback: CallbackQuery) -> None:
    storage.delete_note(callback.from_user.id, int(callback.data.split(":", 1)[1]))
    text, keyboard = notes_view(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Удалено")


async def main() -> None:
    bot = Bot(token=os.environ["BOT_TOKEN"])
    me = await bot.get_me()
    logging.info("бот запущен: @%s", me.username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
