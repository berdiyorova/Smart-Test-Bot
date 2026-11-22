import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, ReplyKeyboardRemove
from aiogram.filters import Command

from config import BOT_TOKEN, ADMIN_ID
from create_test import router
from take_test import take_test_router
from admin_tests import tests_router
from admin_results import results_router




bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router=router)
dp.include_router(router=take_test_router)
dp.include_router(router=tests_router)
dp.include_router(router=results_router)


async def set_bot_commands(bot: Bot):
    admin_commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="newtest", description="Yangi test yaratish"),
        BotCommand(command="mytests", description="Testlarimni ko'rish"),
        BotCommand(command="results", description="Natijalarni ko'rish")
    ]
    await bot.set_my_commands(
        commands=admin_commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
        )
    
    user_commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="help", description="Yordam va qoidalar")
    ]
    await bot.set_my_commands(
        commands=user_commands,
        scope=BotCommandScopeDefault()
    )


@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def cmd_start(message: types.Message):
    await message.answer(
        text="Assalomu alaykum. Botga xush kelibsiz!"
    )




async def main():
    logging.basicConfig(filename="test_bot.log", level=logging.INFO)

    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__=="__main__":
    asyncio.run(main())
