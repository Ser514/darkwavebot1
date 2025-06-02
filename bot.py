import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🔐 ENV-змінні
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

# ⚙️ Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🤖 Ініціалізація бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 📋 Стан машини
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

user_profiles = {}

def profile_caption(data):
    return f"""
🖤 Ім’я: {data.get('name')}
🎂 Вік: {data.get('age')}
📍 Місто: {data.get('city')}
🏳️ Орієнтація: {data.get('orientation')}
💬 Шукає: {data.get('looking_for')}
🎧 Вайб: {data.get('vibe')}
📏 Зріст: {data.get('height')}
🔗 Telegram: {data.get('contact')}
"""

@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🌑 Привіт у Darkwave.\nяк до тебе звертатися?")
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
    await state.set_state(Form.orientation)
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Гетеро"), KeyboardButton(text="Бі")],
        [KeyboardButton(text="Інше")]
    ], resize_keyboard=True)
    await message.answer("Яка твоя орієнтація?", reply_markup=keyboard)

@dp.message(Form.orientation, F.text)
async def get_orientation(message: Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    await state.set_state(Form.looking_for)
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Дівчину"), KeyboardButton(text="Хлопця")],
        [KeyboardButton(text="Друга"), KeyboardButton(text="Подругу")],
        [KeyboardButton(text="FWB"), KeyboardButton(text="ONS")]
    ], resize_keyboard=True)
    await message.answer("Кого шукаєш?", reply_markup=keyboard)

@dp.message(Form.looking_for, F.text)
async def get_looking_for(message: Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await state.set_state(Form.vibe)
    await message.answer("Опиши свій вайб, стиль або музику яку слухаєш:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))

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
    await state.set_state(Form.media)
    await message.answer("Надішли до 3 фото або 1 відео і до 2 фото:")

@dp.message(Form.media)
async def get_media(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    media = user_profiles.get(user_id, {"media": []})["media"]

    if message.photo:
        media.append(InputMediaPhoto(media=message.photo[-1].file_id))
    elif message.video:
        media.append(InputMediaVideo(media=message.video.file_id))
    else:
        await message.answer("Надішли тільки фото або відео")
        return

    if len(media) >= 3:
        caption = profile_caption(data)
        try:
            media[0].caption = caption
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            await message.answer("✅ Твою анкету надіслано до каналу. Дякуємо!")
        except Exception as e:
            logging.exception("❌ Помилка при надсиланні анкети:")
            await message.answer("⚠️ Сталася помилка при надсиланні анкети. Зв'яжися з адміном.")
        await state.clear()
        user_profiles.pop(user_id, None)
    else:
        user_profiles[user_id] = {"media": media}
        await message.answer(f"Можна ще {3 - len(media)} файл(и).")

# 🔁 Відповідь на неочікувані повідомлення в будь-якому стані
@dp.message()
async def fallback(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer("⚠️ Очікую іншу відповідь. Якщо хочеш перезапустити анкету — напиши /start")

# 🔗 Webhook старт
async def on_startup(app):
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
    logger.info(f"Webhook встановлено: {webhook_url}")

# 🧹 Webhook стоп
async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook видалено")

# 🔁 Обробка запитів Telegram
async def handle_webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)
    update = await request.json()
    logging.info(f"💬 Отримано оновлення: {update}")
    await dp.feed_raw_update(bot, update)
    return web.Response()

# 🧩 Запуск aiohttp сервера
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
