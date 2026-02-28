from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError
import logging

class ChannelMembershipMiddleware(BaseMiddleware):
    def __init__(self, public_channel_usernames: str):
        # Split by comma and strip whitespace
        self.channel_usernames = [ch.strip() for ch in public_channel_usernames.split(',') if ch.strip()]
        # Ensure they start with @ or are IDs (ids usually don't need @, usernames do)
        self.normalized_channels = []
        for ch in self.channel_usernames:
            if not ch.startswith("-100") and not ch.startswith("@"):
                 self.normalized_channels.append(f"@{ch}")
            else:
                 self.normalized_channels.append(ch)

    async def __call__(self, handler, event, data):
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        # Skip check for /start if you want, but requirement says mandatory.
        # But allow /start deep links if needed? For now strict lock.

        bot = data["bot"]
        user_id = event.from_user.id
        
        missing_channels = []

        for channel in self.normalized_channels:
            try:
                member = await bot.get_chat_member(channel, user_id)
                if member.status not in ("member", "administrator", "creator"):
                    missing_channels.append(channel)
            except TelegramAPIError as e:
                logging.error(f"Error checking membership for {channel}: {e}")
                # If bot cannot check (not admin or channel invalid), maybe skip or fail secure?
                # Failing secure (adding to missing) is safer for business, but annoying if config is wrong.
                # Let's add to missing so admin notices.
                missing_channels.append(channel)

        if not missing_channels:
            return await handler(event, data)

        # User is missing some channels
        text = (
            "🔐 <b>Botdan qoydalanish uchun quyidagi kanallarga a’zo bo‘ling:</b>\n\n"
            "A’zo bo‘lib, so‘ng “✅ Tekshirish” tugmasini bosing."
        )
        
        keyboard = []
        for ch in missing_channels:
            # We need a link. If it's a private channel ID (-100...), we can't easily guess link without InviteLink cache.
            # Assuming public usernames for now as per config name PUBLIC_CHANNEL_USERNAMES.
            # If ID is used, impossible to give link unless we fetch chat.
            
            btn_text = "📢 Kanalga a'zo bo'lish"
            url = f"https://t.me/{ch.strip('@')}"
            
            # Try to get chat title if possible (adds latency, but better UX)
            try:
                chat_obj = await bot.get_chat(ch)
                btn_text = f"📢 {chat_obj.title}"
                if chat_obj.username:
                    url = f"https://t.me/{chat_obj.username}"
                # If private channel without username, we need invite link.
                elif chat_obj.invite_link:
                    url = chat_obj.invite_link
            except:
                pass

            keyboard.append([InlineKeyboardButton(text=btn_text, url=url)])

        keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        if isinstance(event, Message):
            await event.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        elif isinstance(event, CallbackQuery):
             # If it's the "check" button, answer with alert if still missing
             if event.data == "check_subscription":
                 await event.answer("Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
                 # Optionally update message to refresh list
                 try:
                    await event.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
                 except:
                    pass
             else:
                 await event.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
                 await event.answer()
        return
