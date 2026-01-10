from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
import os

from .database import get_history, save_history, init_db, get_stats
from .api import search_all, fetch_movie_by_query
from .utils import logger_bot as logger
from .utils import search_keyboard

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
KINO_TOKEN = os.getenv("KINO_TOKEN")
VK_TOKEN= os.getenv("vk_token")
DEVIDER = "-" * 10

dp = Dispatcher()

@dp.message(Command('start', 'help'))
async def cmd_help(message: types.Message):
    text = (
        "Я — бот для поиска фильмов.\n\n"
        "Правила использования:\n"
        "- Отправьте название фильма (по умолчанию любой текст трактуется как запрос к фильму).\n"
        "- Команды:\n /help — показать это сообщение;\n /history — показать вашу историю запросов.\n"
        "/stats — показать статистику по запрашиваемым вами фильмам.\n\n"
        "Примеры запросов:\n"
        "- «Начало»\n"
        "- «Inception 2010»\n"
        "бро я ии сгенерирован и т.д."
    )
    await message.reply(text, reply_markup=search_keyboard)


@dp.message(Command('history'))
async def cmd_history(message: types.Message):
    if message.from_user is None:
        await message.reply("Тебя не существует")
        return
    rows = await get_history(message.from_user.id, limit=10)
    if not rows:
        await message.reply("У вас пока нет истории запросов.")
        return
    lines = [""]
    for q, title, url, ts in rows:
        line = f"Запрос: {q}\nРезультат: {title or '—'}\nСсылка: {url or '—'}\nВремя (UTC): {ts}\n"
        lines.append(line)
    lines.pop(0)
    await message.reply("\n\n".join(lines), reply_markup=search_keyboard)


@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    if message.from_user is None:
        await message.reply("Тебя не существует")
        return
    rows = await get_stats(message.from_user.id, limit=10)
    if not rows:
        await message.reply("У вас пока нет истории статистики.")
        return
    lines = [""]
    for query, quantity in rows:
        line = f"Запрос: {query}\nЧастота {quantity or '—'}"
        lines.append(line)
    lines.pop(0)
    await message.reply("\n\n".join(lines), reply_markup=search_keyboard)


@dp.message(F.content_type == types.ContentType.TEXT)
async def handle_text(message: types.Message):
    if message.from_user is None or message.text is None:
        await message.reply("пустое сообщение или ошибка чтения id. Попробуйте позже")
        return
    query = message.text.strip()
    await message.chat.do("typing")

    try:
        result = await build_movie_response(query)
    except Exception:
        logger.exception("Error looking up movie")
        await message.reply("Произошла внутренняя ошибка при поиске. Попробуйте позже.")
        return

    if not result:
        await save_history(message.from_user.id, query, None, None)
        await message.reply("Фильм не найден по запросу. Попробуйте указать год или другой вариант названия.")
        return

    for item in result:
        parts = [""]
        for res in item:
            for key, value in res.items():
                if value:
                    parts.append(str(value))
        parts.pop(0)
        await message.reply(f"\n{DEVIDER}\n".join(parts), parse_mode="HTML", reply_markup=search_keyboard)
    await save_history(message.from_user.id, query, query, result[1][0].get("url", ""))


async def build_movie_response(query: str):
    """Поиск фильма во внешних API"""
    answer = []
    answer_poster = []
    try:
        kinopoisk_res = await fetch_movie_by_query(api_key=KINO_TOKEN, query=query, limit=1)
        docs = kinopoisk_res.get("docs", [])
        if docs:
            docs = docs[0]
            raiting = docs.get("rating")
            if raiting:
                raiting = raiting.get("kp")
            descr = docs.get("description")
            poster = docs.get("poster")
            poster_url = ""
            if poster:
                poster_url = poster.get("url")
            answer_poster.append({"descr": descr, "raiting": f"Рейтинг: {raiting}", "poster": poster_url})
            answer.append(answer_poster)
        else:
            return

        res = await search_all(query, vk_token=VK_TOKEN)
        answer.append(res["vk"])
        return answer

    except Exception as e:
        logger.error(f"Error in build_movie_response: {e}")
        return


async def main():
    bot = Bot(token=BOT_TOKEN)
    await init_db()
    await dp.start_polling(bot, skip_updates=True)
