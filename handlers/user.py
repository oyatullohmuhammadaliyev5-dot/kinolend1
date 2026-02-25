from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from keyboards import subscribe_keyboard, rating_keyboard, top_movies_keyboard
from utils import check_subscription

router = Router()

WELCOME_TEXT = (
    "🎬 <b>Silence Kinolar Botiga Xush Kelibsiz!</b>\n\n"
    "Bu bot orqali siz kino kodini yuboring va kinoni tomosha qiling.\n\n"
    "📌 Masalan: <code>125</code> deb yozing."
)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    await db.add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name
    )

    ok, missing = await check_subscription(bot, message.from_user.id)
    if ok:
        await message.answer(
            WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=top_movies_keyboard()
        )
    else:
        await message.answer(
            "🔒 <b>Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:</b>",
            parse_mode="HTML",
            reply_markup=subscribe_keyboard(missing)
        )


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery, bot: Bot):
    ok, missing = await check_subscription(bot, call.from_user.id)
    if ok:
        await call.message.edit_text(
            WELCOME_TEXT,
            parse_mode="HTML"
        )
        await call.message.answer("✅ Rahmat! Endi kino kodini yuboring.", reply_markup=top_movies_keyboard())
    else:
        await call.answer("❌ Siz hali barcha kanallarga a'zo emassiz!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=subscribe_keyboard(missing))


@router.callback_query(F.data == "top_movies")
async def show_top_movies(call: CallbackQuery):
    movies = await db.get_top_movies(10)
    if not movies:
        await call.answer("Hozircha kinolar yo'q.", show_alert=True)
        return

    text = "🏆 <b>Eng ko'p ko'rilgan kinolar:</b>\n\n"
    for i, m in enumerate(movies, 1):
        text += (
            f"{i}. 🎬 <b>{m['name']}</b>\n"
            f"   🎭 Janr: {m['genre']} | 👁 Ko'rishlar: {m['views']} | "
            f"⭐ {m['avg_rating']}\n"
            f"   📌 Kod: <code>{m['code']}</code>\n\n"
        )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


@router.message(F.text)
async def handle_code(message: Message, bot: Bot):
    # Skip admin commands
    if message.text.startswith("/"):
        return

    ok, missing = await check_subscription(bot, message.from_user.id)
    if not ok:
        await message.answer(
            "🔒 Avval kanallarga a'zo bo'ling:",
            reply_markup=subscribe_keyboard(missing)
        )
        return

    code = message.text.strip()
    movie = await db.get_movie(code)

    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi.\n"
            "To'g'ri kodni kiriting yoki adminga murojaat qiling.",
            parse_mode="HTML"
        )
        return

    await db.increment_views(code)
    avg = movie['avg_rating']
    caption = (
        f"🎬 <b>{movie['name']}</b>\n"
        f"🎭 Janr: <i>{movie['genre']}</i>\n"
        f"⭐ Reyting: {avg} ({movie['rating_count']} ovoz)\n"
        f"👁 Ko'rishlar: {movie['views'] + 1}\n\n"
        f"📌 Kod: <code>{movie['code']}</code>"
    )
    await message.answer_video(
        video=movie['file_id'],
        caption=caption,
        parse_mode="HTML",
        reply_markup=rating_keyboard(movie['code'])
    )


@router.callback_query(F.data.startswith("rate_"))
async def rate_movie(call: CallbackQuery):
    _, code, rating_str = call.data.split("_", 2)
    rating = int(rating_str)

    result = await db.add_rating(call.from_user.id, code, rating)
    stars = "⭐" * rating

    if result == "added":
        await call.answer(f"✅ Bahoyingiz qabul qilindi: {stars}", show_alert=False)
    elif result == "updated":
        await call.answer(f"🔄 Bahoyingiz yangilandi: {stars}", show_alert=False)
    else:
        await call.answer("❌ Xatolik yuz berdi.", show_alert=True)
