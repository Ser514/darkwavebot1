# coding=utf-8
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo
)
from aiogram.enums import ParseMode
from aiogram.client.session.bot import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel_id")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    orientation = State()
    looking_for = State()
    vibe = State()
    height = State()
    contact = State()
    photo = State()

MAX_PHOTOS = 3
user_media_store = {}

@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🌑 Привіт у Darkwave. Як до тебе звертатися?")
    await state.set_state(Form.name)

@dp.message(Form.name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Скільки тобі років?")

@dp.message(Form.age, F.text)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer("Звідки ти?")

@dp.message(Form.city, F.text)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Гетеро"), KeyboardButton(text="Бі")],
            [KeyboardButton(text="Інше")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(Form.orientation)
    await message.answer("Яка твоя орієнтація?", reply_markup=keyboard)

@dp.message(Form.orientation, F.text)
async def get_orientation(message: Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Дівчину"), KeyboardButton(text="Хлопця")],
            [KeyboardButton(text="Друга"), KeyboardButton(text="Подругу")],
            [KeyboardButton(text="FWB"), KeyboardButton(text="ONS")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(Form.looking_for)
    await message.answer("Кого шукаєш?", reply_markup=keyboard)

@dp.message(Form.looking_for, F.text)
async def get_looking_for(message: Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await state.set_state(Form.vibe)
    await message.answer("Опиши свій вайб або музику яку слухаєш:")

@dp.message(Form.vibe, F.text)
async def get_vibe(message: Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await state.set_state(Form.height)
    await message.answer("Який твій зріст?")

@dp.message(Form.height, F.text)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await state.set_state(Form.contact)
    await message.answer("Вкажи свій Telegram @нік:")

@dp.message(Form.contact, F.text)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Form.photo)
    await message.answer("Надішли до 3 фото або 1 відео + 2 фото. Напиши /done коли завершиш.")

@dp.message(Form.photo, F.photo | F.video)
async def collect_media(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_media_store:
        user_media_store[user_id] = []

    media_list = user_media_store[user_id]

    if message.video:
        if any(isinstance(m, InputMediaVideo) for m in media_list):
            await message.answer("🎥 Вже є відео. Можна лише одне.")
            return
        media_list.append(InputMediaVideo(media=message.video.file_id))
    elif message.photo:
        photo_count = sum(isinstance(m, InputMediaPhoto) for m in media_list)
        if photo_count >= MAX_PHOTOS:
            await message.answer("📸 Максимум 3 фото.")
            return
        media_list.append(InputMediaPhoto(media=message.photo[-1].file_id))
    await message.answer("✅ Додано. Ще щось? /done коли все.")

@dp.message(Form.photo, F.text == "/done")
async def finish_media_collection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    media = user_media_store.get(user_id, [])

    if not media:
        await message.answer("⚠️ Ти не надіслав жодного медіа.")
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
        await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await message.answer("✅ Анкету опубліковано.")
        await show_profiles(message)
    except Exception as e:
        logger.exception("❌ Помилка надсилання:")
        await message.answer("⚠️ Помилка публікації.")
    finally:
        user_media_store.pop(user_id, None)
        await state.clear()

def profile_interaction_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{user_id}"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{user_id}")
        ],
        [
            InlineKeyboardButton(text="✉️ Написати", callback_data=f"msg_{user_id}"),
            InlineKeyboardButton(text="📹 Кружок", callback_data=f"circle_{user_id}")
        ]
    ])

async def show_profiles(message: Message):
    # Тимчасові фейкові анкети — заміни на справжні із бази!
    fake_profiles = [
        {"id": 1001, "name": "Аліса", "age": 23, "city": "Київ", "photo": "AgACAgQAAxkBA..."},
        {"id": 1002, "name": "Макс", "age": 26, "city": "Львів", "photo": "AgACAgQAAxkBA..."}
    ]
    for profile in fake_profiles:
        caption = f"🖤 {profile['name']}, {profile['age']} років\n📍 {profile['city']}"
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=profile["photo"],
            caption=caption,
            reply_markup=profile_interaction_keyboard(profile["id"])
        )

@dp.message(F.text == "/me")
async def my_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        await message.answer("📭 У тебе ще нема анкети. Напиши /start")
        return
    text = (
        f"🖤 Ім’я: {data.get('name')}\n"
        f"🎂 Вік: {data.get('age')}\n"
        f"📍 Місто: {data.get('city')}\n"
        f"Щоб змінити — напиши /start"
    )
    await message.answer(text)

@dp.message()
async def fallback(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer("⚠️ Очікую іншу відповідь. Напиши /start щоб почати заново.")

async def on_startup(app):
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
    logger.info(f"Webhook встановлено: {webhook_url}")

async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook видалено")

async def handle_webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)
    update = await request.json()
    await dp.feed_raw_update(bot, update)
    return web.Response()

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
