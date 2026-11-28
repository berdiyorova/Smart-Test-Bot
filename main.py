import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, ADMIN_ID, WEB_SERVER_HOST, WEB_SERVER_PORT, WEBHOOK_PATH, WEBHOOK_URL
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
        BotCommand(command="results", description="Natijalarni ko'rish"),
    ]
    await bot.set_my_commands(
        commands=admin_commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_ID),
    )

    user_commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="help", description="Yordam va qoidalar"),
    ]
    await bot.set_my_commands(
        commands=user_commands,
        scope=BotCommandScopeDefault(),
    )


@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def cmd_start(message: types.Message):
    await message.answer(
        text="Assalomu alaykum. Botga xush kelibsiz!"
    )


async def on_startup(bot: Bot) -> None:
    await set_bot_commands(bot)
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logging.info("Webhook o'chirildi.")


def main() -> None:
    logging.basicConfig(filename="test_bot.log", level=logging.INFO)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
