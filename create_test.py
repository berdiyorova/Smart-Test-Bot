from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from keyboards import after_question_markup
from config import ADMIN_ID
from storage import save_test


TESTS: dict[str, dict] = {}
router = Router()


class QuizFormStates(StatesGroup):
    waiting_title = State()
    waiting_question = State()
    waiting_options = State()
    waiting_correct = State()


def get_after_question_keyboard():
  return after_question_markup


@router.message(
    Command("cancel"),
    F.from_user.id == ADMIN_ID,
    StateFilter(
        QuizFormStates.waiting_title,
        QuizFormStates.waiting_question,
        QuizFormStates.waiting_options,
        QuizFormStates.waiting_correct,
    ),
)
async def cancel_test_creation(message: types.Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "🛑 **Test tuzish bekor qilindi.**\n"
      "Kiritilayotgan savollar va vaqtinchalik ma'lumotlar tozalandi.\n\n"
      "Qayta boshlash uchun /newtest buyrug'ini yuboring.",
      parse_mode="Markdown",
  )


@router.callback_query(
    F.data == "cancel_quiz", 
    F.from_user.id == ADMIN_ID,
    StateFilter(
        QuizFormStates.waiting_title,
        QuizFormStates.waiting_question,
        QuizFormStates.waiting_options,
        QuizFormStates.waiting_correct
    )
)
async def cancel_quiz(callback: types.CallbackQuery, state: FSMContext):
  await state.clear()
  await callback.answer("Bekor qilindi")
  await callback.message.edit_text(
      "🛑 Test tuzish bekor qilindi.\n"
      "Kiritilayotgan savollar va vaqtinchalik ma'lumotlar tozalandi.\n\n"
      "Qayta boshlash uchun /newtest buyrug'ini yuboring.",
      parse_mode="Markdown",
  )


@router.message(Command("newtest"), F.from_user.id == ADMIN_ID)
async def start_quiz_form(message: types.Message, state: FSMContext):
  await state.clear()
  await state.set_state(QuizFormStates.waiting_title)
  await message.answer(
      "📝 Yangi test formasi\n\n"
      "Test nomini kiriting (masalan: `Matematika - 1-chorak`):",
      parse_mode="Markdown",
      reply_markup=ReplyKeyboardRemove()
  )


@router.message(QuizFormStates.waiting_title, F.from_user.id == ADMIN_ID)
async def form_get_title(message: types.Message, state: FSMContext):
  title = message.text.strip()
  await state.update_data(title=title, questions=[])
  await state.set_state(QuizFormStates.waiting_question)

  await message.answer(
      f"📌 Test nomi: {title}\n\n"
      "1-savol matnini yuboring:",
      parse_mode="Markdown",
  )


@router.message(QuizFormStates.waiting_question, F.from_user.id == ADMIN_ID)
async def form_get_question(message: types.Message, state: FSMContext):
  question_text = message.text.strip()
  await state.update_data(current_question=question_text)
  await state.set_state(QuizFormStates.waiting_options)

  await message.answer(
      "Javob variantlarini HAR BIRINI YANGI QATORDA yuboring"
      " (kamida 2 ta):\n\n"
      "Masalan:\n"
      "`print()`\n"
      "`echo()`\n"
      "`scan()`",
      parse_mode="Markdown",
  )


@router.message(QuizFormStates.waiting_options, F.from_user.id == ADMIN_ID)
async def form_get_options(message: types.Message, state: FSMContext):
  options = [line.strip() for line in message.text.splitlines() if line.strip()]

  if len(options) < 2:
    await message.answer(
        "⚠️ Kamida 2 ta variant kiriting (har birini yangi qatorda)."
    )
    return

  await state.update_data(current_options=options)
  await state.set_state(QuizFormStates.waiting_correct)

  options_preview = "\n".join(
      f"{i + 1}. {opt}" for i, opt in enumerate(options)
  )
  await message.answer(
      f"To'g'ri javob raqamini yuboring (`1` dan `{len(options)}` gacha):\n\n"
      f"{options_preview}",
      parse_mode="Markdown",
  )


@router.message(QuizFormStates.waiting_correct, F.from_user.id == ADMIN_ID)
async def form_get_correct(message: types.Message, state: FSMContext):
  data = await state.get_data()
  options = data["current_options"]

  try:
    correct_num = int(message.text.strip())
    if correct_num < 1 or correct_num > len(options):
      raise ValueError
  except ValueError:
    await message.answer(
        f"❌ Iltimos, `1` dan `{len(options)}` gacha bo'lgan raqam kiriting.",
        parse_mode="Markdown",
    )
    return

  new_question = {
      "question": data["current_question"],
      "options": options,
      "correct_index": correct_num - 1,
  }

  questions = data["questions"]
  questions.append(new_question)
  await state.update_data(questions=questions)

  await message.answer(
      f"✅ {len(questions)}-savol qo'shildi!\n"
      f"Savol: {new_question['question']}\n"
      f"To'g'ri javob: **{correct_num}. {options[correct_num - 1]}**\n\n"
      "Davom etamizmi?",
      reply_markup=get_after_question_keyboard(),
      parse_mode="Markdown",
  )


@router.callback_query(F.data == "add_more_q", F.from_user.id == ADMIN_ID)
async def add_another_question(
    callback: types.CallbackQuery, state: FSMContext
):
  data = await state.get_data()
  next_num = len(data.get("questions", [])) + 1
  await state.set_state(QuizFormStates.waiting_question)

  await callback.message.edit_text(
      f"{next_num}-savol matnini yuboring:", parse_mode="Markdown"
  )
  await callback.answer()


@router.callback_query(F.data == "save_quiz", F.from_user.id == ADMIN_ID)
async def save_finished_quiz(
    callback: types.CallbackQuery, state: FSMContext, bot: Bot
):
  data = await state.get_data()
  questions = data.get("questions", [])

  if not questions:
    await callback.answer("Kamida 1 ta savol qo'shing!", show_alert=True)
    return

  test_id = save_test(title=data["title"], questions=questions)
  await state.clear()

  me = await bot.get_me()
  test_link = f"https://t.me/{me.username}?start={test_id}"

  await callback.message.edit_text(
      f"📝 Test saqlandi!\n\n"
      f"📌 Nomi: {data['title']}\n"
      f"❓ Savollar soni: {len(questions)} ta\n\n"
      f"🔗 Ulashish uchun link:\n`{test_link}`",
      parse_mode="Markdown",
  )
  await callback.answer()
