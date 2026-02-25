import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS
from keyboards import (
    admin_main_keyboard, cancel_keyboard,
    channel_manage_keyboard
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── FSM STATES ───────────────────────────────────────────────────────────────

class AddMovie(StatesGroup):
    waiting_video = State()
    waiting_name = State()
    waiting_code = State()
    waiting_genre = State()


class DeleteMovie(StatesGroup):
    waiting_code = State()


class AddChannel(StatesGroup):
    waiting_data = State()


class Broadcast(StatesGroup):
    waiting_message = State()


# ─── ADMIN PANEL ──────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await message.answer(
        "👨‍💼 <b>Admin panel</b>\n\nQuyidagi amallardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard()
    )


# ─── ADD MOVIE ────────────────────────────────────────────────────────────────

@router.message(F.text == "🎬 Kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddMovie.waiting_video)
    await message.answer(
        "🎬 Kino videosini yuboring:",
        reply_markup=cancel_keyboard()
    )


@router.message(AddMovie.waiting_video, F.video)
async def add_movie_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.waiting_name)
    await message.answer("📝 Kino nomini kiriting:")


@router.message(AddMovie.waiting_name, F.text)
async def add_movie_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    await state.update_data(name=message.text)
    await state.set_state(AddMovie.waiting_code)
    await message.answer("🔢 Kino kodini kiriting (masalan: 125):")


@router.message(AddMovie.waiting_code, F.text)
async def add_movie_code(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    code = message.text.strip()
    existing = await db.get_movie(code)
    if existing:
        await message.answer(f"❌ <b>{code}</b> kodi allaqachon mavjud! Boshqa kod kiriting.", parse_mode="HTML")
        return
    await state.update_data(code=code)
    await state.set_state(AddMovie.waiting_genre)
    await message.answer("🎭 Janrni kiriting (masalan: Drama, Komediya, Triller...):")


@router.message(AddMovie.waiting_genre, F.text)
async def add_movie_genre(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    data = await state.get_data()
    success = await db.add_movie(data['code'], data['name'], message.text, data['file_id'])
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🎬 Nom: {data['name']}\n"
            f"📌 Kod: <code>{data['code']}</code>\n"
            f"🎭 Janr: {message.text}",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )
    else:
        await message.answer("❌ Xatolik! Kod takrorlanmasligi kerak.", reply_markup=admin_main_keyboard())


# ─── DELETE MOVIE ─────────────────────────────────────────────────────────────

@router.message(F.text == "🗑 Kino o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(DeleteMovie.waiting_code)
    await message.answer("🗑 O'chirmoqchi bo'lgan kino kodini kiriting:", reply_markup=cancel_keyboard())


@router.message(DeleteMovie.waiting_code, F.text)
async def delete_movie_confirm(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    code = message.text.strip()
    success = await db.delete_movie(code)
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{code}</code> kodli kino o'chirildi.", parse_mode="HTML",
                              reply_markup=admin_main_keyboard())
    else:
        await message.answer(f"❌ <code>{code}</code> kodli kino topilmadi.", parse_mode="HTML",
                              reply_markup=admin_main_keyboard())


# ─── CHANNELS MANAGEMENT ──────────────────────────────────────────────────────

@router.message(F.text == "📢 Kanallar")
async def manage_channels(message: Message):
    if not is_admin(message.from_user.id):
        return
    channels = await db.get_channels()
    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    if not channels:
        text += "Hozircha kanallar yo'q."
    else:
        for ch in channels:
            text += f"• {ch['channel_name']} — <code>{ch['channel_id']}</code>\n"
    await message.answer(text, parse_mode="HTML", reply_markup=channel_manage_keyboard(channels))


@router.callback_query(F.data == "add_channel")
async def add_channel_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AddChannel.waiting_data)
    await call.message.answer(
        "➕ Kanal ma'lumotlarini quyidagi formatda yuboring:\n\n"
        "<code>kanal_id|Kanal nomi|https://t.me/kanal</code>\n\n"
        "Masalan:\n<code>-1001234567890|Mening Kanalim|https://t.me/mening_kanalim</code>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await call.answer()


@router.message(AddChannel.waiting_data, F.text)
async def add_channel_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    try:
        parts = message.text.strip().split("|")
        channel_id, channel_name, channel_link = parts[0].strip(), parts[1].strip(), parts[2].strip()
        await db.add_channel(channel_id, channel_name, channel_link)
        await state.clear()
        await message.answer(
            f"✅ <b>{channel_name}</b> kanali qo'shildi!",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )
    except Exception:
        await message.answer(
            "❌ Format noto'g'ri. Quyidagi formatda yuboring:\n"
            "<code>kanal_id|Kanal nomi|https://t.me/kanal</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("delch_"))
async def delete_channel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = int(call.data.split("_")[1])
    success = await db.delete_channel(ch_id)
    if success:
        channels = await db.get_channels()
        text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
        if not channels:
            text += "Hozircha kanallar yo'q."
        else:
            for ch in channels:
                text += f"• {ch['channel_name']} — <code>{ch['channel_id']}</code>\n"
        await call.message.edit_text(text, parse_mode="HTML",
                                     reply_markup=channel_manage_keyboard(channels))
        await call.answer("✅ Kanal o'chirildi!")
    else:
        await call.answer("❌ Xatolik!", show_alert=True)


# ─── STATISTICS ───────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    user_count = await db.get_user_count()
    movie_count = await db.get_movie_count()
    top_movies = await db.get_top_movies(5)

    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{user_count}</b>\n"
        f"🎬 Kinolar soni: <b>{movie_count}</b>\n\n"
        f"🏆 <b>Top 5 kino:</b>\n"
    )
    for i, m in enumerate(top_movies, 1):
        text += f"{i}. {m['name']} — 👁 {m['views']} | ⭐ {m['avg_rating']}\n"

    await message.answer(text, parse_mode="HTML", reply_markup=admin_main_keyboard())


# ─── BROADCAST ────────────────────────────────────────────────────────────────

@router.message(F.text == "📨 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.waiting_message)
    await message.answer(
        "📨 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=cancel_keyboard()
    )


@router.message(Broadcast.waiting_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()
    await message.answer(f"📤 Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda...",
                         reply_markup=admin_main_keyboard())

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
            await asyncio.sleep(0.05)  # Rate limit prevention
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}",
        parse_mode="HTML"
    )
