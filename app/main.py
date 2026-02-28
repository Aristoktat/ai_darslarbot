import asyncio
import logging
import sys
import os
from datetime import timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Project Imports
from app.config import settings
from app.db import init_db, async_session
from app.bot.handlers import user, admin
from app.bot.middlewares import ChannelMembershipMiddleware
from app.services.subscriptions import disable_expired_subscriptions

# Logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def check_expired_subscriptions(bot: Bot):
    logger.info("Checking for expired subscriptions...")
    async with async_session() as session:
        expired_subs = await disable_expired_subscriptions(session)
        for sub in expired_subs:
            try:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Obunani yangilash", callback_data="check_permissions")]
                ])
                await bot.send_message(
                    sub.user_id, 
                    "⏳ <b>Obunangiz tugadi.</b>\n\nPlatformadan foydalanishni davom ettirish uchun obunani yangilang.", 
                    reply_markup=kb, 
                    parse_mode="HTML"
                )
                # Kick/Unban logic to restrict access
                await bot.ban_chat_member(chat_id=settings.PRIVATE_GROUP_ID, user_id=sub.user_id, until_date=timedelta(seconds=60))
                await bot.unban_chat_member(chat_id=settings.PRIVATE_GROUP_ID, user_id=sub.user_id)
                logger.info(f"Kicked user {sub.user_id} due to expiration.")
            except Exception as e:
                logger.error(f"Failed to kick user {sub.user_id}: {e}")

async def handle_health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
    await site.start()
    logger.info(f"Health check server started on port {settings.PORT}")

async def main():
    # 1. Initialize DB (Creates tables if not exists)
    await init_db()
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routers
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # 4. Start Health Check Web Server
    await start_web_server()

    # 5. Start Background Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expired_subscriptions, 'interval', minutes=5, kwargs={'bot': bot})
    scheduler.start()

    # 6. Set Bot Commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Boshlash"),
        BotCommand(command="help", description="Yordam"),
    ])

    logger.info("Bot application fully initialized. Starting polling...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error during polling: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
