from aiogram import F, Router, types
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from storage import get_test_by_id, save_test_result, get_user_test_result
from config import ADMIN_ID

take_test_router = Router()


class TakeTestStates(StatesGroup):
  answering = State()


async def show_question(
    target: types.Message | types.CallbackQuery, state: FSMContext
):
  data = await state.get_data()
  questions = data["questions"]
  q_index = data["q_index"]
  question = questions[q_index]

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=opt, callback_data=f"quiz_ans_{idx}")]
          for idx, opt in enumerate(question["options"])
      ]
  )
  text = (
      f"📘 {data['test_title']}\n"
      f"Savol {q_index + 1} / {len(questions)}:\n\n"
      f"{question['question']}"
  )

  if isinstance(target, types.CallbackQuery):
    await target.message.edit_text(
        text, reply_markup=keyboard, parse_mode="Markdown"
    )
  else:
    await target.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@take_test_router.message(CommandStart(deep_link=True))
async def start_test_by_link(
    message: types.Message, command: CommandObject, state: FSMContext
):
  test_id = (command.args or "").strip()
  test_data = get_test_by_id(test_id)

  if not test_data:
    await message.answer("⚠️ Bu test havolasi eskirgan yoki test topilmadi.")
    return

  user_id = message.from_user.id
  existing_result = get_user_test_result(user_id=user_id, test_id=test_id)

  if existing_result:
    await state.clear()
    await message.answer(
        "⛔ Siz bu testni allaqachon ishlagansiz!\n\n"
        f"📘 Test: {existing_result['test_title']}\n"
        f"🎯 Avvalgi natijangiz: {existing_result['score']} /"
        f" {existing_result['total_questions']}",
        parse_mode="Markdown",
    )
    return

  await state.clear()
  await state.set_state(TakeTestStates.answering)
  await state.set_data({
      "test_id": test_id,
      "test_title": test_data["title"],
      "questions": test_data["questions"],
      "q_index": 0,
      "score": 0,
  })

  await message.answer(
      f"🚀 \"{test_data['title']}\" testi boshlandi!\n"
      f"Jami savollar: {len(test_data['questions'])} ta.",
      parse_mode="Markdown",
  )
  await show_question(message, state)


@take_test_router.message(CommandStart())
async def cmd_start_plain(message: types.Message):
  await message.answer(
      "Assalomu alaykum! Test ishlash uchun o'qituvchingiz yuborgan maxsus"
      " test havolasi ustiga bosing."
  )


@take_test_router.callback_query(TakeTestStates.answering, F.data.startswith("quiz_ans_"))
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
  chosen_idx = int(callback.data.removeprefix("quiz_ans_"))
  data = await state.get_data()

  questions = data["questions"]
  q_index = data["q_index"]
  score = data["score"]
  current_q = questions[q_index]

  if chosen_idx == current_q["correct_index"]:
    score += 1
    await callback.answer("✅ To'g'ri!", show_alert=False)
  else:
    correct_ans = current_q["options"][current_q["correct_index"]]
    await callback.answer(
        f"❌ Noto'g'ri. To'g'ri javob: {correct_ans}", show_alert=True
    )

  q_index += 1
  if q_index < len(questions):
    await state.update_data(q_index=q_index, score=score)
    await show_question(callback, state)
  else:
    total = len(questions)
    user = callback.from_user
    test_id = data["test_id"]

    # Agar parallel sessiya tufayli natija allaqachon yozilgan bo'lsa, dublikat qo'shmaymiz
    if get_user_test_result(user_id=user.id, test_id=test_id) is None:
      save_test_result(
          user_id=user.id,
          full_name=user.full_name,
          username=user.username,
          test_id=test_id,
          test_title=data["test_title"],
          score=score,
          total_questions=total,
      )

    await state.clear()
    await callback.message.edit_text(
        f"🏁 Test yakunlandi!\n\n"
        f"📘 Test: {data['test_title']}\n"
        f"👤 O'quvchi: {user.full_name}\n"
        f"🎯 Natija: {score} / {total}\n\n"
        "Natijangiz saqlandi.",
        parse_mode="Markdown",
    )
    await callback.answer()
