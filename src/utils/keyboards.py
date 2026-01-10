from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

search_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/history"),
            KeyboardButton(text="/stats"),
            KeyboardButton(text="/help")
        ]
    ],
    resize_keyboard=True
)
