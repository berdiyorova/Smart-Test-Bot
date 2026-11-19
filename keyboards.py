from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_test_markup = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[[KeyboardButton(text="Testni boshlash")]],
    input_field_placeholder="Testni boshlash uchun tugmani bosing..."
    )
