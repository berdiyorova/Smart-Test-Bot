from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# start_test_markup = ReplyKeyboardMarkup(
#     resize_keyboard=True,
#     keyboard=[[KeyboardButton(text="🚀 Test yechishni boshlash")]],
#     input_field_placeholder="Testni boshlash uchun tugmani bosing..."
#     )


# new_test_markup = ReplyKeyboardMarkup(
#     resize_keyboard=True,
#     keyboard=[[KeyboardButton(text="🚀 Test tuzishni boshlash")]],
#     input_field_placeholder="Test tuzish uchun tugmani bosing..."
#     )


after_question_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana savol qo'shish", callback_data="add_more_q")],
        [InlineKeyboardButton(text="✅ Testni saqlash", callback_data="save_quiz")],
        [InlineKeyboardButton(text="❌ Testni bekor qilish", callback_data="cancel_quiz")]
    ]
)
