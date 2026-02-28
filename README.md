# Telegram Bot - Pullik Obuna va Video Darslar

Ushbu bot Telegram kanali va yopiq guruhi bilan integratsiya qilingan bo'lib, pullik obuna orqali video darslarni ko'rish va yopiq guruhga kirish imkonini beradi.

## Xususiyatlar
- **Majburiy a'zolik**: Botdan foydalanish uchun ochiq kanalga (@MeningKanalim) a'zo bo'lish shart.
- **Pullik obuna**: 1 oy, 3 oy va Lifetime tariflar (Click/Payme orqali, ulanishi kerak).
- **Video darslar**: Faqat to'lov qilgan foydalanuvchilar uchun bot ichida ochiladi.
- **Yopiq guruh**: To'lov qilganda avtomatik qo'shish (Join Request tasdiqlash yoki havola).
- **Admin panel**: Statistika, tariflar va videolarni boshqarish.
- **Avtomatik chiqarish**: Obuna tugaganda guruhdan chiqarish va xizmatlarni yopish.

## O'rnatish

1. **Loyihani yuklab oling:**
   ```bash
   git clone <repo_url>
   cd yangi_loyiha
   ```

2. **.env faylni sozlang:**
   `.env.example` dan nusxa oling va `.env` deb nomlang. Ichidagi ma'lumotlarni to'ldiring:
   - `BOT_TOKEN`: @BotFather dan olingan token.
   - `ADMIN_IDS`: Adminlarning telegram ID raqamlari (vergul bilan ajratilgan, masalan `[123456, 789012]`).
   - `PUBLIC_CHANNEL_USERNAME`: Ochiq kanal username (masalan `@MeningKanalim`). **Bot bu kanalda admin bo'lishi shart emas, lekin a'zolikni tekshirish uchun ko'ra olishi kerak.**
   - `PRIVATE_GROUP_ID`: Yopiq guruh ID (masalan `-100...`). **Bot bu guruhda ADMIN bo'lishi va foydalanuvchilarni qo'shish/chiqarish huquqiga ega bo'lishi SHART.**
   - `PROVIDER_TOKEN`: To'lov tizimi tokeni (Click/Payme @BotFather dan ulanadi).
   - `POSTGRES_...`: Database sozlamalari (agar Docker ishlatsangiz, standart qolaversin).

3. **Docker orqali ishga tushirish (Tavsiya etiladi):**
   ```bash
   docker-compose up --build -d
   ```

4. **Mahalliy (Local) ishga tushirish:**
   - Talablar: Python 3.11+, PostgreSQL (yoki SQLite).
   ```bash
   pip install -r requirements.txt
   # env faylni o'zgartiring (USE_POSTGRES=False qilib SQLite ishlatish mumkin)
   python -m app.main
   ```

## Admin Panel
Botga `/admin` buyrug'ini yuboring (faqat `ADMIN_IDS` dagi foydalanuvchilar uchun ishlaydi).

- **Tarif qo'shish:** `/add_plan [nomi] [kun] [narx_tiyinda]`
  Masalan 1 oyga 50,000 so'm: `/add_plan "1 Oy" 30 5000000`
- **Video qo'shish:** Videoni botga yuboring va unga reply qilib: `/add_video [sarlavha]`

## Migratsiyalar (Database o'zgarishlari)
Agar `alembic` ishlatmoqchi bo'lsangiz:
1. `alembic init app/migrations`
2. `app/migrations/env.py` faylini `app.db.models` ni ko'radigan qilib sozlang.
3. `alembic revision --autogenerate -m "Initial"`
4. `alembic upgrade head`

Hozirgi holatda `app/db/__init__.py` da `init_db` funksiyasi barchasini avtomatik yaratadi (agar jadvallar yo'q bo'lsa).

## Muhim Eslatmalar
- **Kanal va Guruh:** Botni yopiq guruhga qo'shib, unga "Add Users" va "Ban Users" huquqini bering.
- **To'lovlar:** Telegram to'lovlari test rejimida ishlashi uchun `PROVIDER_TOKEN` ni to'g'ri kiriting (token `284685063...` kabi bo'ladi).
