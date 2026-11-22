import html
import os
from aiogram import Bot, F, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from storage import load_tests
from config import ADMIN_ID

tests_router = Router()


def get_admin_tests_keyboard(tests: dict) -> InlineKeyboardMarkup:
  """Har bir test uchun alohida inline tugma hosil qiladi."""
  rows = []
  for test_id, test_data in tests.items():
    title = test_data.get("title", test_id)
    q_count = len(test_data.get("questions", []))
    rows.append([
        InlineKeyboardButton(
            text=f"📘 {title} ({q_count} ta savol)",
            callback_data=f"admin_link:{test_id}",
        )
    ])
  return InlineKeyboardMarkup(inline_keyboard=rows)


# 1. Admin /mytests buyrug'ini yuborganda barcha testlarni ko'rsatadi
@tests_router.message(Command("mytests"), F.from_user.id == ADMIN_ID)
async def cmd_admin_tests(message: types.Message):
  tests = load_tests()
  if not tests:
    await message.answer(
        "📭 Sizda hali saqlangan testlar mavjud emas.\n"
        "Yangi test yaratish uchun /newtest buyrug'ini yuboring.",
        parse_mode="Markdown",
    )
    return

  await message.answer(
      "📚 <b>Siz yaratgan testlar ro'yxati</b>\n"
      "Havolasini olish uchun kerakli testni tanlang:",
      reply_markup=get_admin_tests_keyboard(tests),
      parse_mode="HTML",
  )


# 2. Test tugmasi bosilganda o'sha testning linkini va ma'lumotini chiqaradi
@tests_router.callback_query(
    F.data.startswith("admin_link:"), F.from_user.id == ADMIN_ID
)
async def send_test_link(callback: types.CallbackQuery, bot: Bot):
  test_id = callback.data.removeprefix("admin_link:")
  tests = load_tests()
  test_data = tests.get(test_id)

  if not test_data:
    await callback.answer(
        "⚠️ Bu test topilmadi yoki o'chirilgan.", show_alert=True
    )
    return

  me = await bot.get_me()
  test_link = f"https://t.me/{me.username}?start={test_id}"
  title = html.escape(test_data.get("title", test_id))
  q_count = len(test_data.get("questions", []))

  # Ro'yxatga qaytish tugmasi
  back_kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Barcha testlarga qaytish", callback_data="admin_tests_back"
          )
      ]]
  )

  await callback.message.edit_text(
      f"📌 <b>Test:</b> {title}\n"
      f"🆔 <b>ID:</b> <code>{html.escape(test_id)}</code>\n"
      f"❓ <b>Savollar soni:</b> {q_count} ta\n\n"
      f"🔗 <b>O'quvchilarga yuborish uchun link:</b>\n"
      f"<code>{html.escape(test_link)}</code>",
      reply_markup=back_kb,
      parse_mode="HTML",
  )
  await callback.answer()


# 3. Ro'yxatga qaytish tugmasi
@tests_router.callback_query(
    F.data == "admin_tests_back", F.from_user.id == ADMIN_ID
)
async def back_to_admin_tests(callback: types.CallbackQuery):
  tests = load_tests()
  if not tests:
    await callback.message.edit_text("📭 Testlar ro'yxati bo'sh.")
    await callback.answer()
    return

  await callback.message.edit_text(
      "📚 <b>Siz yaratgan testlar ro'yxati</b>\n"
      "Havolasini olish uchun kerakli testni tanlang:",
      reply_markup=get_admin_tests_keyboard(tests),
      parse_mode="HTML",
  )
  await callback.answer()