import html
import os
from aiogram import F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from storage import load_results, load_tests
from config import ADMIN_ID

results_router = Router()

MAX_MESSAGE_LEN = 4000


def get_results_tests_keyboard(tests: dict, results: list[dict]) -> InlineKeyboardMarkup:
  """Har bir test bo'yicha nechta natija borligini hisoblab, inline tugmalar yasaydi."""
  counts_by_test: dict[str, int] = {}
  for item in results:
    tid = item.get("test_id")
    if tid:
      counts_by_test[tid] = counts_by_test.get(tid, 0) + 1

  rows = []
  for test_id, test_data in tests.items():
    title = test_data.get("title", test_id)
    res_count = counts_by_test.get(test_id, 0)
    rows.append([
        InlineKeyboardButton(
            text=f"📘 {title} ({res_count} ta natija)",
            callback_data=f"res_test:{test_id}",
        )
    ])
  return InlineKeyboardMarkup(inline_keyboard=rows)


def format_result_line(index: int, entry: dict) -> str:
  full_name = html.escape(str(entry.get("full_name", "Noma'lum")))
  username = entry.get("username")
  username_str = f"@{html.escape(username)}" if username else "yo'q"

  score = entry.get("score", 0)
  total = entry.get("total_questions", 0)
  percent = round((score / total) * 100) if total > 0 else 0
  finished_at = html.escape(str(entry.get("finished_at", "")))

  return (
      f"<b>{index}.</b> {full_name} ({username_str})\n"
      f"   🎯 <b>{score} / {total}</b> ({percent}%)"
      + (f" • 🕒 <code>{finished_at}</code>" if finished_at else "")
  )


def build_test_results_messages(
    test_id: str, test_title: str, filtered_results: list[dict]
) -> list[str]:
  """Tanlangan bitta test natijalari va o'rtacha ko'rsatkichini tayyorlaydi."""
  safe_title = html.escape(test_title)
  safe_id = html.escape(test_id)

  if not filtered_results:
    return [
        f"📭 <b>{safe_title}</b> (<code>{safe_id}</code>) testi bo'yicha"
        " hali birorta ham natija yo'q."
    ]

#   # O'rtacha ball va foizni hisoblash
#   avg_score = sum(r.get("score", 0) for r in filtered_results) / len(filtered_results)
#   avg_total = sum(r.get("total_questions", 0) for r in filtered_results) / len(filtered_results)
#   avg_percent = round((avg_score / avg_total) * 100) if avg_total > 0 else 0

  latest_first = list(reversed(filtered_results))
  lines = [
      format_result_line(idx, item)
      for idx, item in enumerate(latest_first, start=1)
  ]

  header = (
      f"📊 <b>{safe_title}</b> (<code>{safe_id}</code>)\n"
      f"👥 Topshirganlar: <b>{len(filtered_results)}</b> nafar\n"
    #   f"📈 O'rtacha natija: <b>{avg_score:.1f}</b> ({avg_percent}%)\n\n"
  )

  chunks: list[str] = []
  current = header
  for line in lines:
    addition = f"\n\n{line}"
    if len(current) + len(addition) > MAX_MESSAGE_LEN:
      chunks.append(current)
      current = line
    else:
      current += addition
  if current:
    chunks.append(current)
  return chunks


# 1. /results komandasi: argument berilsa darhol o'sha testni, bo'lmasa testlar ro'yxatini chiqaradi
@results_router.message(Command("results"), F.from_user.id == ADMIN_ID)
async def cmd_results_menu(message: types.Message, command: CommandObject):
  tests = load_tests()
  results = load_results()

  arg_test_id = (command.args or "").strip()
  if arg_test_id:
    test_title = (
        tests[arg_test_id].get("title", arg_test_id)
        if arg_test_id in tests
        else arg_test_id
    )
    filtered = [r for r in results if r.get("test_id") == arg_test_id]
    chunks = build_test_results_messages(arg_test_id, test_title, filtered)
    for chunk in chunks:
      await message.answer(chunk, parse_mode="HTML")
    return

  if not tests:
    await message.answer("📭 Hozircha testlar mavjud emas.")
    return

  await message.answer(
      "📊 <b>Natijalarni ko'rish</b>\n"
      "Qaysi test natijalarini ko'rmoqchisiz? Testni tanlang:",
      reply_markup=get_results_tests_keyboard(tests, results),
      parse_mode="HTML",
  )


# 2. Muayyan test tugmasi bosilganda faqat shu test natijalari chiqadi
@results_router.callback_query(F.data.startswith("res_test:"), F.from_user.id == ADMIN_ID)
async def show_single_test_results(callback: types.CallbackQuery):
  test_id = callback.data.removeprefix("res_test:")
  tests = load_tests()
  results = load_results()

  if test_id not in tests:
    await callback.answer("⚠️ Test topilmadi.", show_alert=True)
    return

  test_title = tests[test_id].get("title", test_id)
  filtered = [r for r in results if r.get("test_id") == test_id]
  chunks = build_test_results_messages(test_id, test_title, filtered)

  back_kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Testlar ro'yxatiga qaytish", callback_data="res_back"
          )
      ]]
  )

  # Birinchi bo'lakni xabarni tahrirlab (edit_text) va qaytish tugmasi bilan chiqaramiz
  await callback.message.edit_text(
      chunks[0], reply_markup=back_kb, parse_mode="HTML"
  )
  for extra_chunk in chunks[1:]:
    await callback.message.answer(extra_chunk, parse_mode="HTML")

  await callback.answer()


# 3. Orqaga qaytish tugmasi
@results_router.callback_query(F.data == "res_back", F.from_user.id == ADMIN_ID)
async def back_to_results_menu(callback: types.CallbackQuery):
  tests = load_tests()
  results = load_results()

  if not tests:
    await callback.message.edit_text("📭 Hozircha testlar mavjud emas.")
    await callback.answer()
    return

  await callback.message.edit_text(
      "📊 <b>Natijalarni ko'rish</b>\n"
      "Qaysi test natijalarini ko'rmoqchisiz? Testni tanlang:",
      reply_markup=get_results_tests_keyboard(tests, results),
      parse_mode="HTML",
  )
  await callback.answer()