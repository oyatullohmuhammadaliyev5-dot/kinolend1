# 🎬 Silence Kinolar Bot

Telegram kino bot — majburiy obuna, kino qidirish, reyting tizimi va admin panel bilan.

---

## 📦 O'rnatish

### 1. Loyihani yuklab oling
```bash
git clone <repo_url>
cd silence_bot
```

### 2. Virtual muhit yarating (tavsiya etiladi)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlang
```bash
cp .env.example .env
```
`.env` faylini oching va quyidagilarni to'ldiring:

```env
BOT_TOKEN=your_bot_token_here   # @BotFather dan oling
ADMIN_IDS=123456789             # @userinfobot dan oling
DB_PATH=silence_bot.db
```

### 5. Botni ishga tushiring
```bash
python bot.py
```

---

## 🤖 Bot imkoniyatlari

### 👤 Foydalanuvchilar uchun
| Amal | Tavsif |
|------|--------|
| `/start` | Botni ishga tushirish |
| Kino kodi | Masalan `125` yuboring — kino keladi |
| ⭐ Baho | Kinoga 1–5 yulduz bering |
| 🏆 Top kinolar | Eng ko'p ko'rilganlar ro'yxati |

### 👨‍💼 Adminlar uchun (`/admin`)
| Tugma | Tavsif |
|-------|--------|
| 🎬 Kino qo'shish | Video + nom + kod + janr |
| 🗑 Kino o'chirish | Kod orqali o'chirish |
| 📢 Kanallar | Majburiy obuna kanallarini boshqarish |
| 📊 Statistika | Foydalanuvchilar soni, top kinolar |
| 📨 Xabar yuborish | Hammaga reklama/xabar yuborish |

---

## 📢 Kanal qo'shish formati

Admin panelda kanal qo'shishda quyidagi formatdan foydalaning:

```
-1001234567890|Kanal Nomi|https://t.me/kanal_username
```

> ⚠️ Bot kanalda **admin** bo'lishi shart!

---

## 🏗 Loyiha tuzilmasi

```
silence_bot/
├── bot.py           # Asosiy ishga tushirish fayli
├── config.py        # Konfiguratsiya
├── database.py      # SQLite bazasi bilan ishlash
├── keyboards.py     # Tugmalar (inline va reply)
├── utils.py         # Obuna tekshirish
├── handlers/
│   ├── user.py      # Foydalanuvchi handlerlari
│   └── admin.py     # Admin handlerlari (FSM)
├── requirements.txt
└── .env.example
```

---

## 🛠 Texnik stack

- **Python 3.10+**
- **aiogram 3.x** — Telegram Bot API
- **aiosqlite** — Asinxron SQLite
- **python-dotenv** — Muhit o'zgaruvchilari

---

## 💡 Foydali maslahatlar

- Videolar Telegram serverlarida `file_id` orqali saqlanadi — server xotirasi sarflanmaydi
- Bot bir nechta kanal uchun obunani tekshira oladi
- Reyting tizimi foydalanuvchi boshqa ovoz berishda yangilanadi
- Broadcast xabarida har qanday turdagi media (rasm, video, matn) yuborsa bo'ladi
