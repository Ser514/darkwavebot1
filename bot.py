import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🔐 ENV-змінні
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Наприклад: @darkwave_love
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")  # https://your-app.onrender.com
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
    photo = State()

# 🚀 /start
@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await message.answer("🌑 Привіт у Darkwave.\nГотовий заповнити анкету? Відповідай на запитання.")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Скільки тобі років?")

@dp.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer("Звідки ти?")

@dp.message(Form.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Form.orientation)
    await message.answer("Яка твоя орієнтація? (Гетеро / Бі / Інше)")

@dp.message(Form.orientation)
async def get_orientation(message: Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    await state.set_state(Form.looking_for)
    await message.answer("Кого шукаєш?")

@dp.message(Form.looking_for)
async def get_looking_for(message: Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await state.set_state(Form.vibe)
    await message.answer("Опиши свій вайб, стиль або музику яку слухаєш:")

@dp.message(Form.vibe)
async def get_vibe(message: Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await state.set_state(Form.height)
    await message.answer("Який твій зріст?")

@dp.message(Form.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await state.set_state(Form.contact)
    await message.answer("Вкажи свій Telegram @нік:")

@dp.message(Form.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Form.photo)
    await message.answer("Надішли фото (одне):")

@dp.message(Form.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    caption = f"""
🖤 Ім’я: {data['name']}
🎂 Вік: {data['age']}
📍 Місто: {data['city']}
🏳️ Орієнтація: {data['orientation']}
💬 Шукає: {data['looking_for']}
🎧 Вайб: {data['vibe']}
📏 Зріст: {data['height']}
🔗 Telegram: {data['contact']}
"""
    await bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=caption)
    await message.answer("✅ Твою анкету надіслано до каналу. Дякуємо!")
    await state.clear()

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
    await dp.feed_raw_update(bot, update)
    return web.Response()

# 🧩 Запуск aiohttp сервера
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
