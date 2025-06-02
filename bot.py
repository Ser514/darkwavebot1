# coding=utf-8
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo
)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel_id")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot init
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    orientation = State()
    looking_for = State()
    vibe = State()
    height = State()
    contact = State()
    media = State()

# Store user media temp
user_media_store = {}

@dp.message(F.command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🌑 Привіт у Darkwave. Як до тебе звертатися?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Скільки тобі років?")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Звідки ти?")
    await state.set_state(Form.city)

@dp.message(Form.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Гетеро"), KeyboardButton(text="Бі")],
        [KeyboardButton(text="Інше")]
    ], resize_keyboard=True)
    await message.answer("Яка твоя орієнтація?", reply_markup=keyboard)
    await state.set_state(Form.orientation)

@dp.message(Form.orientation)
async def get_orientation(message: Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Дівчину"), KeyboardButton(text="Хлопця")],
        [KeyboardButton(text="Друга"), KeyboardButton(text="Подругу")],
        [KeyboardButton(text="FWB"), KeyboardButton(text="ONS")]
    ], resize_keyboard=True)
    await message.answer("Кого шукаєш?", reply_markup=keyboard)
    await state.set_state(Form.looking_for)

@dp.message(Form.looking_for)
async def get_looking_for(message: Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await message.answer("Опиши свій вайб або музику яку слухаєш:")
    await state.set_state(Form.vibe)

@dp.message(Form.vibe)
async def get_vibe(message: Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await message.answer("Який твій зріст?")
    await state.set_state(Form.height)

@dp.message(Form.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Вкажи свій Telegram @нік:")
    await state.set_state(Form.contact)

@dp.message(Form.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    user_media_store[message.from_user.id] = []
    await message.answer("Надішли до 3 фото або 1 відео + 2 фото. Напиши /done коли завершиш.")
    await state.set_state(Form.media)

@dp.message(Form.media, F.photo | F.video)
async def collect_media(message: Message, state: FSMContext):
    user_id = message.from_user.id
    media = user_media_store.get(user_id, [])

    if message.video:
        if any(isinstance(m, InputMediaVideo) for m in media):
            await message.answer("🎥 Можна лише одне відео.")
            return
        media.append(InputMediaVideo(media=message.video.file_id))
    elif message.photo:
        if sum(isinstance(m, InputMediaPhoto) for m in media) >= 3:
            await message.answer("📸 Вже є 3 фото.")
            return
        media.append(InputMediaPhoto(media=message.photo[-1].file_id))

    user_media_store[user_id] = media
    await message.answer("✅ Додано. /done коли завершиш.")

@dp.message(Form.media, F.text == "/done")
async def finish_media(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    media = user_media_store.get(user_id, [])

    if not media:
        await message.answer("⚠️ Ти не додав медіа.")
        return

    caption = (
        f"🖤 Ім’я: {data.get('name')}\n"
        f"🎂 Вік: {data.get('age')}\n"
        f"📍 Місто: {data.get('city')}\n"
        f"🏳️ Орієнтація: {data.get('orientation')}\n"
        f"💬 Шукає: {data.get('looking_for')}\n"
        f"🎧 Вайб: {data.get('vibe')}\n"
        f"📏 Зріст: {data.get('height')}\n"
        f"🔗 Telegram: {data.get('contact')}"
    )

    try:
        media[0].caption = caption
        media[0].parse_mode = ParseMode.HTML
        await bot.send_media_group(CHANNEL_ID, media=media)
        await message.answer("✅ Анкету надіслано до каналу!")
        await show_profiles(message)
    except Exception as e:
        logger.error(f"❌ Error sending media: {e}")
        await message.answer("⚠️ Помилка надсилання.")
    finally:
        await state.clear()
        user_media_store.pop(user_id, None)

def profile_keyboard(uid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{uid}"),
         InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{uid}")],
        [InlineKeyboardButton(text="✉️ Написати", callback_data=f"msg_{uid}"),
         InlineKeyboardButton(text="📹 Кружок", callback_data=f"circle_{uid}")]
    ])

async def show_profiles(message: Message):
    fake_profiles = [
        {"id": 1, "name": "Аліса", "age": 23, "city": "Київ", "photo": "https://via.placeholder.com/300"},
        {"id": 2, "name": "Макс", "age": 26, "city": "Львів", "photo": "https://via.placeholder.com/300"}
    ]
    for p in fake_profiles:
        text = f"🖤 {p['name']}, {p['age']} років\n📍 {p['city']}"
        await bot.send_photo(chat_id=message.chat.id, photo=p['photo'], caption=text, reply_markup=profile_keyboard(p['id']))

@dp.message(F.text == "/me")
async def check_profile(message: Message, state: FSMContext):
    data = await state.storage.get_data(chat=message.chat.id, user=message.from_user.id)
    if not data:
        await message.answer("📭 Немає анкети. Напиши /start")
        return
    await message.answer(
        f"🖤 Ім’я: {data.get('name')}\n🎂 Вік: {data.get('age')}\n📍 Місто: {data.get('city')}\n"
        f"Хочеш змінити? — /start"
    )

@dp.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await message.answer("⚠️ Очікую іншу відповідь. Напиши /start щоб почати знову.")

# Webhook
async def on_startup(app): await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
async def on_shutdown(app): await bot.delete_webhook()
async def handle_webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)
    update = await request.json()
    await dp.feed_raw_update(bot, update)
    return web.Response()

# AIOHTTP
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
