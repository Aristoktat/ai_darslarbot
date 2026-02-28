from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, SuccessfulPayment, LabeledPrice, ContentType, ChatJoinRequest
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from app.db import async_session
from app.db.models import User, Plan, Subscription, Payment, Video
from app.services.subscriptions import get_active_subscription, create_subscription
from app.config import settings
from app.bot.keyboards import get_main_menu, get_plans_keyboard, get_videos_keyboard, get_welcome_keyboard, get_subscription_renewal_keyboard
from sqlalchemy import select
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message):
    async with async_session() as session:
        # Check/Create user
        user = await session.execute(select(User).where(User.id == message.from_user.id))
        user = user.scalar_one_or_none()
        if not user:
            new_user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(new_user)
            await session.commit()
    
    # Check if user has active sub
    async with async_session() as session:
        active_sub = await get_active_subscription(session, message.from_user.id)
    
    # Provide the Welcome screen first (as requested) regardless of sub, or skip to menu if sub?
    # User request "Start -> Azolik -> Plans" implies a flow.
    # But if they already paid, showing plans is weird.
    # If active sub, show "Main Menu" with specific welcome back text.
    
    if active_sub:
        await message.answer(f"Xush kelibsiz, {message.from_user.full_name}! Obunangiz faol.", reply_markup=get_main_menu())
    else:
        text = (
            "🤖 <b>AI Darslar Platformasiga xush kelibsiz!</b>\n\n"
            "Bu yerda siz:\n\n"
            "🎬 Sun’iy intellektni 0 dan boshlab o‘rganasiz\n"
            "💰 AI orqali daromad qilishni amalda ko‘rasiz\n"
            "🛠 Telegram bot, sayt va avtomatlashtirishni real loyihalarda qilasiz\n"
            "🔴 Jonli darslarda savol-javob qilasiz\n"
            "📂 Barcha darslar bosqichma-bosqich va tushunarli\n\n"
            "🔥 73% o‘quvchilar 1 oy ichida o‘zining birinchi AI loyihasini ishga tushirgan.\n\n"
            "Boshlash uchun pastdagi tugmani bosing 👇"
        )
        # Using a reliable placeholder image. You can replace URL with a file_id later.
        photo_url = "https://img.freepik.com/free-vector/artificial-intelligence-landing-page-template_23-2148264359.jpg"
        
        await message.answer_photo(
            photo=photo_url,
            caption=text,
            reply_markup=get_welcome_keyboard(),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "check_subscription")
async def check_permissions(callback: CallbackQuery):
    # This is handled by Middleware mostly, but if middleware passes, it reaches here.
    # If middleware passes, it means user IS a member.
    await callback.message.delete()
    await callback.message.answer("Quyidagi menyudan foydalaning:", reply_markup=get_welcome_keyboard())

@router.message(F.text == "🚀 KURSDA O'QISHNI BOSHLASH")
async def start_button_handler(message: Message):
    # This button is clicked. Middleware checked membership.
    # Show plans.
    async with async_session() as session:
        plans_result = await session.execute(select(Plan).where(Plan.is_active == True))
        plans = plans_result.scalars().all()
        
    text = (
        "🎓 <b>AI Darslar Tariflari</b>\n\n"
        "Qaysi paket sizga mos?\n\n"
        "🥉 1 Oylik — tez boshlash va sinab ko‘rish\n"
        "🥈 3 Oylik — chuqur o‘rganish va real loyiha\n"
        "🥇 Lifetime — umrbod kirish + barcha yangilanishlar\n\n"
        "Har bir paketda:\n"
        "✔ Video darslar\n"
        "✔ Jonli darslar\n"
        "✔ Amaliy topshiriqlar\n"
        "✔ Yopiq guruh\n"
        "✔ Doimiy yangilanishlar\n\n"
        "⚠️ Jonli darslar guruhida joylar cheklangan.\n"
        "Tanlang 👇"
    )
    await message.answer(text, reply_markup=get_plans_keyboard(plans), parse_mode="HTML")

@router.message(F.text == "ℹ️ Loyiha haqida")
async def about_handler(message: Message):
    text = (
        "ℹ️ **Loyiha haqida**\n\n"
        "Bizning platforma orqali siz zamonaviy AI texnologiyalarini o'rganasiz.\n"
        "Darslar amaliy va natijaga yo'naltirilgan.\n\n"
        "Murojaat uchun: @AdminUser (o'zgartiring)"
    )
    await message.answer(text)

@router.callback_query(F.data.startswith("buy_plan:"))
async def process_payment(callback: CallbackQuery):
    plan_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            await callback.answer("Tarif topilmadi.", show_alert=True)
            return

    # Text before Invoice
    msg_text = (
        f"📦 <b>Siz tanladingiz: {plan.name}</b>\n\n"
        "Nimalar ochiladi?\n\n"
        "🎬 Barcha video darslar\n"
        "🔴 Jonli darslar guruhi\n"
        "📂 Materiallar\n"
        "💬 Yopiq community\n"
        "📈 Real amaliy topshiriqlar\n\n"
        "To‘lovni tasdiqlang 👇"
    )
    await callback.message.answer(msg_text, parse_mode="HTML")

    prices = [LabeledPrice(label=plan.name, amount=plan.price)]
    
    try:
        await callback.message.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Originalniy Platforma - {plan.name}",
            description=f"To'lov qilish uchun pastdagi tugmani bosing",
            payload=f"plan_id:{plan.id}",
            provider_token=settings.PROVIDER_TOKEN,
            currency=settings.CURRENCY,
            prices=prices,
            start_parameter=f"buy-plan-{plan_id}",
            photo_url="https://via.placeholder.com/300x200?text=Premium+Access",
            photo_height=200,
            photo_width=300,
            need_name=True,
            need_phone_number=False,
            is_flexible=False
        )
        await callback.answer()
    except TelegramBadRequest as e:
        await callback.message.answer(f"Xatolik: To'lov tizimi ishlamayapti.\nSabab: {e.message}")
        await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    plan_id = int(payload.split(":")[1]) if payload.startswith("plan_id:") else None
    
    if not plan_id:
        await message.answer("Xatolik: Noto'g'ri to'lov ma'lumoti.")
        return

    async with async_session() as session:
        new_payment = Payment(
            user_id=message.from_user.id,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
            provider=settings.PROVIDER_TOKEN,
            tg_charge_id=payment_info.telegram_payment_charge_id,
        )
        session.add(new_payment)
        
        new_sub = await create_subscription(session, message.from_user.id, plan_id)
        await session.commit()

    text = (
        "🎉 <b>Tabriklaymiz! To‘lov qabul qilindi.</b>\n\n"
        "Endi siz platformaning to‘liq a’zosisiz.\n\n"
        "Quyidagilar ochildi:\n"
        "🎬 Video darslar\n"
        "🔴 Jonli dars guruhi\n"
        "📊 Obuna boshqaruvi\n\n"
        "Boshlash uchun menyudan tanlang 👇"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")
    
    # Provide immediate link after payment
    try:
        invite_link = await message.bot.create_chat_invite_link(
            chat_id=settings.PRIVATE_GROUP_ID,
            member_limit=1,
            name=f"User {message.from_user.id}"
        )
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        link_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Guruhga kirish (Bir martalik)", url=invite_link.invite_link)]
        ])
        
        await message.answer("🎁 Mana guruhga kirish uchun bir martalik havolangiz:", reply_markup=link_kb)
    except Exception as e:
        print(f"Error creating link after payment: {e}")

@router.message(F.text == "🎬 Video darslar")
async def list_videos(message: Message):
    async with async_session() as session:
        active_sub = await get_active_subscription(session, message.from_user.id)
        
        if not active_sub:
             await message.answer("Video darslarni ko'rish uchun obuna bo'lishingiz kerak.", reply_markup=get_subscription_renewal_keyboard())
             return

        videos_res = await session.execute(select(Video).where(Video.is_active == True).order_by(Video.order))
        videos = videos_res.scalars().all()
        
    text = (
        "🎬 **Video Darslar**\n\n"
        "Bosqichma-bosqich o‘rganing:\n\n"
        "1️⃣ AI asoslari\n"
        "2️⃣ ChatGPT bilan ishlash\n"
        "3️⃣ Telegram bot yaratish\n"
        "4️⃣ AI orqali pul ishlash\n"
        "5️⃣ Avtomatlashtirish\n"
        "6️⃣ Real loyiha\n\n"
        "Kerakli bo‘limni tanlang 👇"
    )
    
    if not videos:
        await message.answer("Hozircha video darslar yo'q.")
        return

    page = 1
    per_page = 5
    total_pages = (len(videos) + per_page - 1) // per_page
    current_videos = videos[(page-1)*per_page : page*per_page]
    
    await message.answer(text, reply_markup=get_videos_keyboard(current_videos, page, total_pages), parse_mode="HTML")

@router.message(F.text == "🔴 Jonli guruhga kirish")
async def group_access_handler(message: Message):
    async with async_session() as session:
        active_sub = await get_active_subscription(session, message.from_user.id)
        
        if not active_sub:
             await message.answer("Guruhga kirish uchun obuna bo'lishingiz kerak.", reply_markup=get_subscription_renewal_keyboard())
             return

    text = (
        "🔴 **Jonli Dars Guruhi**\n\n"
        "Bu yerda:\n"
        "✔ Haftalik jonli darslar\n"
        "✔ Savol-javob\n"
        "✔ Real loyihalar\n"
        "✔ Networking\n\n"
        "Quyidagi link orqali kirish so‘rovi yuboring 👇"
    )
    
    try:
        # Create 1-time Invite Link
        invite_link = await message.bot.create_chat_invite_link(
             chat_id=settings.PRIVATE_GROUP_ID,
             member_limit=1,
             name=f"Access Request {message.from_user.id}"
        )
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Guruhga kirish (Bir martalik)", url=invite_link.invite_link)]
        ])
        
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Guruh havolasini yaratishda xatolik: {e}\nAdmin bilan bog'laning.")


@router.message(F.text == "📊 Mening obunam")
async def subscription_status_handler(message: Message):
    async with async_session() as session:
        active_sub = await get_active_subscription(session, message.from_user.id)
        if not active_sub:
             await message.answer("Sizda hozirda faol obuna yo'q.", reply_markup=get_subscription_renewal_keyboard())
             return
        
        # We need plan name. Eager load or join?
        # Subscription model has `plan` relationship but default lazy loading might fail in async without specific options.
        # Let's fetch plan manually or use joinedload option in get_active_subscription query.
        # For simplicity, simple fetch:
        plan = await session.get(Plan, active_sub.plan_id)
        
    start_str = active_sub.start_date.strftime("%d.%m.%Y")
    end_str = active_sub.end_date.strftime("%d.%m.%Y") if active_sub.end_date else "Cheksiz"
    status = "✅ Aktiv" if active_sub.is_active else "❌ Nofaol"
    
    text = (
        "📊 **Obuna ma’lumotlari**\n\n"
        f"Tarif: {plan.name}\n"
        f"Boshlanish: {start_str}\n"
        f"Tugash: {end_str}\n"
        f"Holat: {status}\n\n"
        "Obuna tugaganda avtomatik chiqarilasiz."
    )
    
    # Buttons: Renew, Back
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Uzaytirish", callback_data="buy_subscription")], 
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "renew_subscription")
async def renew_subscription_cb(callback: CallbackQuery):
    await start_button_handler(callback.message)
    await callback.answer()

@router.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery):
    await callback.message.delete()
    # Can't easily "go back" to start menu without sending new message.
    await callback.message.answer("Asosiy menyu", reply_markup=get_welcome_keyboard())

# ... Video watch handlers remain same ...
@router.callback_query(F.data.startswith("watch_video:"))
async def watch_video(callback: CallbackQuery):
    video_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        active_sub = await get_active_subscription(session, callback.from_user.id)
        if not active_sub:
            await callback.answer("Obunangiz yo'q yoki tugagan.", show_alert=True)
            return
            
        video = await session.get(Video, video_id)
        if not video:
            await callback.answer("Video topilmadi.", show_alert=True)
            return
            
    try:
        await callback.message.answer_video(
            video.file_id, 
            caption=f"🎬 {video.title}",
            protect_content=True
        )
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Videoni yuborishda xatolik: {e}")
        await callback.answer()

@router.callback_query(F.data.startswith("videos_page:"))
async def videos_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        videos_res = await session.execute(select(Video).where(Video.is_active == True).order_by(Video.order))
        videos = videos_res.scalars().all()
        
    per_page = 5
    total_pages = (len(videos) + per_page - 1) // per_page
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    current_videos = videos[(page-1)*per_page : page*per_page]
    
    await callback.message.edit_reply_markup(reply_markup=get_videos_keyboard(current_videos, page, total_pages))
    await callback.answer()

@router.chat_join_request()
async def chat_join_request_handler(update: ChatJoinRequest):
    if update.chat.id != settings.PRIVATE_GROUP_ID:
        return

    async with async_session() as session:
        active_sub = await get_active_subscription(session, update.from_user.id)
        
    if active_sub:
        await update.approve()
        try:
            await update.bot.send_message(update.from_user.id, "Guruhga kirish so'rovingiz tasdiqlandi! ✅")
        except:
            pass
    else:
        # Decline but send message
        await update.decline()
        try:
            await update.bot.send_message(update.from_user.id, "Guruhga kirish uchun avval obuna to'lashingiz kerak.")
        except:
            pass
