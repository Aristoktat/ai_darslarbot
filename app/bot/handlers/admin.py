from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.db import async_session
from app.db.models import Plan, Video, User, Subscription, Payment
from app.config import settings
from sqlalchemy import select, func
import logging

router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

class AddPlanStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_days = State()
    waiting_for_price = State()

class AddVideoStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_title = State()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

def get_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel_state")]])

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Batafsil Statistika", callback_data="admin_stats_advanced")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar Listi", callback_data="admin_user_list")],
        [InlineKeyboardButton(text="📢 Xabar Yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔒 Kontent Himoyasi (Toggle)", callback_data="admin_toggle_protection")],
        [InlineKeyboardButton(text="⚙️ Tariflar & Videolar", callback_data="admin_settings_menu")],
    ])

def get_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi Tarif Qo'shish", callback_data="admin_add_plan_start")],
        [InlineKeyboardButton(text="🎥 Yangi Video Qo'shish", callback_data="admin_add_video_start")],
        [InlineKeyboardButton(text="📋 Mavjud Tariflar", callback_data="admin_list_plans")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back_main")],
    ])

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    logging.info(f"Admin access attempt by user_id: {message.from_user.id}")
    if not is_admin(message.from_user.id):
        await message.answer(f"Siz admin emassiz. Sizning ID: <code>{message.from_user.id}</code>", parse_mode="HTML")
        return
    await state.clear()
    await message.answer("🛠 <b>Admin Dashboard</b>\n\nBoshqaruv elementini tanlang:", reply_markup=get_admin_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_cancel_state")
async def admin_cancel_state(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Amallar bekor qilindi.", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 <b>Admin Dashboard</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_settings_menu")
async def admin_settings_menu(callback: CallbackQuery):
    await callback.message.edit_text("⚙️ <b>Tariflar va Videolarni sozlash</b>", reply_markup=get_settings_keyboard(), parse_mode="HTML")

# --- Add Plan Flow ---
@router.callback_query(F.data == "admin_add_plan_start")
async def add_plan_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddPlanStates.waiting_for_name)
    await callback.message.edit_text("📝 <b>Yangi tarif nomini kiriting:</b>\n(Masalan: VIP Obuna)", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AddPlanStates.waiting_for_name)
async def add_plan_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddPlanStates.waiting_for_days)
    await message.answer("📅 <b>Obuna davomiyligini kiriting (kunlarda):</b>\n(Umrbod bo'lsa 0 deb yozing)", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AddPlanStates.waiting_for_days)
async def add_plan_days(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return
    await state.update_data(days=int(message.text))
    await state.set_state(AddPlanStates.waiting_for_price)
    await message.answer("💰 <b>Tarif narxini kiriting (faqat raqam, so'mda):</b>\n(Masalan: 50000)", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AddPlanStates.waiting_for_price)
async def add_plan_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return
    
    data = await state.get_data()
    price_tiyin = int(message.text) * 100
    days = data['days'] if data['days'] > 0 else None
    
    async with async_session() as session:
        new_plan = Plan(name=data['name'], duration_days=days, price=price_tiyin, is_active=True)
        session.add(new_plan)
        await session.commit()
    
    await state.clear()
    await message.answer(f"✅ <b>Tarif muvaffaqiyatli qo'shildi!</b>\n\nNomi: {data['name']}\nDavomiyligi: {data['days']} kun\nNarxi: {message.text} so'm", reply_markup=get_admin_keyboard(), parse_mode="HTML")

# --- Add Video Flow ---
@router.callback_query(F.data == "admin_add_video_start")
async def add_video_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddVideoStates.waiting_for_video)
    await callback.message.edit_text("🎥 <b>Videoni yuboring:</b>\n(Yoki boshqa kanaldan forward qiling)", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AddVideoStates.waiting_for_video, F.video)
async def add_video_file(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddVideoStates.waiting_for_title)
    await message.answer("📝 <b>Video sarlavhasini kiriting:</b>", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AddVideoStates.waiting_for_title)
async def add_video_title(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        max_order = await session.scalar(select(func.max(Video.order))) or 0
        new_video = Video(title=message.text, file_id=data['file_id'], order=max_order + 1, is_active=True)
        session.add(new_video)
        await session.commit()
    
    await state.clear()
    await message.answer(f"✅ <b>Video dars qo'shildi!</b>\n\nSarlavha: {message.text}", reply_markup=get_admin_keyboard(), parse_mode="HTML")

# --- Stats & Users ---
@router.callback_query(F.data == "admin_stats_advanced")
async def show_stats_advanced(callback: CallbackQuery):
    async with async_session() as session:
        user_count = await session.scalar(select(func.count(User.id)))
        active_subs = await session.scalar(select(func.count(Subscription.id)).where(Subscription.is_active == True))
        expired_subs = await session.scalar(select(func.count(Subscription.id)).where(Subscription.is_active == False))
        total_revenue = await session.scalar(select(func.sum(Payment.amount))) or 0
        
    text = (
        f"📊 <b>Kengaytirilgan Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <code>{user_count}</code>\n"
        f"✅ Faol obunalar: <code>{active_subs}</code>\n"
        f"❌ Muddati o'tgan: <code>{expired_subs}</code>\n"
        f"💰 Umumiy tushum: <code>{total_revenue / 100:,.0f}</code> so'm\n"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_user_list")
async def admin_user_list(callback: CallbackQuery):
    async with async_session() as session:
        stmt = select(User, Subscription).outerjoin(Subscription).order_by(User.created_at.desc()).limit(15)
        results = await session.execute(stmt)
        rows = results.all()
        
    text = "👥 <b>Oxirgi 15 foydalanuvchi:</b>\n\n"
    for user, sub in rows:
        sub_status = "✅" if sub and sub.is_active else "❌"
        text += f"{sub_status} {user.full_name or 'No Name'} (<code>{user.id}</code>)\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.message.edit_text("📢 <b>Barcha foydalanuvchilarga yuborilishi kerak bo'lgan xabarni yozing:</b>\n\n(Har qanday media qabul qilinadi)", reply_markup=get_cancel_kb(), parse_mode="HTML")

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.text == "/cancel": 
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    await state.clear()
    sent_msg = await message.answer("⏳ Yuborilmoqda...")
    async with async_session() as session:
        user_ids = (await session.scalars(select(User.id))).all()
    
    success, failed = 0, 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            success += 1
        except: failed += 1
    
    await sent_msg.edit_text(f"📢 <b>Yuborildi!</b>\n\n✅ {success}\n❌ {failed}", parse_mode="HTML")
    await message.answer("🛠 Admin Panel", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_toggle_protection")
async def toggle_protection(callback: CallbackQuery):
    try:
        chat = await callback.bot.get_chat(settings.PRIVATE_GROUP_ID)
        new_state = not getattr(chat, 'has_protected_content', False)
        await callback.bot.set_chat_protected_content(chat_id=settings.PRIVATE_GROUP_ID, has_protected_content=new_state)
        status = "Yoqildi 🔒" if new_state else "O'chirildi 🔓"
        await callback.answer(f"Himoya: {status}", show_alert=True)
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)

@router.callback_query(F.data == "admin_list_plans")
async def list_plans(callback: CallbackQuery):
    async with async_session() as session:
        plans = (await session.scalars(select(Plan))).all()
    text = "📋 <b>Mavjud Tariflar:</b>\n\n"
    for p in plans:
        text += f"- {p.name}: {p.duration_days if p.duration_days else 'Umrbod'} kun, {p.price/100:,.0f} so'm\n"
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard(), parse_mode="HTML")
