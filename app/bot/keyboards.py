from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.db.models import Plan, Video

def get_welcome_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 KURSDA O'QISHNI BOSHLASH")],
            [KeyboardButton(text="ℹ️ Loyiha haqida"), KeyboardButton(text="📞 Admin")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Quyidagi tugmani bosing 👇"
    )

def get_check_subscription_keyboard(channel_url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=channel_url)],
            [InlineKeyboardButton(text="✅ A'zolikni tekshirish", callback_data="check_subscription")]
        ]
    )

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Video darslar"), KeyboardButton(text="🔴 Jonli guruhga kirish")],
            [KeyboardButton(text="📊 Mening obunam"), KeyboardButton(text="ℹ️ Loyiha haqida")]
        ],
        resize_keyboard=True
    )

def get_plans_keyboard(plans: list[Plan]):
    keyboard = []
    # Sort plans: 1 Month, 3 Month, Lifetime (assuming length/price correlates)
    plans.sort(key=lambda x: x.price)

    for plan in plans:
        price_display = f"{plan.price / 100:,.0f} so'm".replace(",", " ")
        
        icon = "💎"
        if "1" in plan.name or "bir" in plan.name.lower(): icon = "🥉"
        elif "3" in plan.name or "uch" in plan.name.lower(): icon = "🥈"
        elif "lifetime" in plan.name.lower() or "umrbod" in plan.name.lower(): icon = "🥇"
        
        btn_text = f"{icon} {plan.name} ({price_display})"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_plan:{plan.id}")])
    
    # Back is usually good, but the flow is simpler without deep nest.
    # User requested flow: "Tanlang 👇" then buttons.
    # No explicit back button requested in "Plan Selection" part of prompt, 
    # but "Masalan 1 oylik tanlanganda... Orqaga" appears in "Mening obunam".
    # I'll keep Back button in plan selection just in case.
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_videos_keyboard(videos: list[Video], page: int = 1, total_pages: int = 1):
    keyboard = []
    for video in videos:
        keyboard.append([InlineKeyboardButton(text=f"🎥 {video.title}", callback_data=f"watch_video:{video.id}")])
    
    pagination_row = []
    if page > 1:
        pagination_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"videos_page:{page-1}"))
    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"videos_page:{page+1}"))
    
    if pagination_row:
        keyboard.append(pagination_row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_renewal_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Obunani yangilash", callback_data="renew_subscription")]
        ]
    )
