import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramConflictError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# 🔧 Конфіг
BOT_TOKEN = "7735699455:AAHG1QV9B-h6IwCCvHYmw0nlqUy0PcwBZSw"
CHANNEL_ID = "@darkwave_love"

# ✅ Валідація
if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("❌ BOT_TOKEN або CHANNEL_ID не задані")

# 🔔 Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚀 Ініціалізація
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# 📋 Стан анкети
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

# 📍 Команда /start
@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await message.answer("🌑 Привіт у Darkwave.\nГотовий заповнити анкету? Відповідай на запитання.")
    await state.set_state(Form.name)

@router.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Скільки тобі років?")

@router.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer("Звідки ти?")

@router.message(Form.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Form.orientation)
    await message.answer("Яка твоя орієнтація? (Гетеро / Бі / Інше)")

@router.message(Form.orientation)
async def get_orientation(message: Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    await state.set_state(Form.looking_for)
    await message.answer("Кого шукаєш?")

@router.message(Form.looking_for)
async def get_looking_for(message: Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await state.set_state(Form.vibe)
    await message.answer("Опиши свій вайб, стиль або музику яку слухаєш:")

@router.message(Form.vibe)
async def get_vibe(message: Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await state.set_state(Form.height)
    await message.answer("Який твій зріст?")

@router.message(Form.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await state.set_state(Form.contact)
    await message.answer("Вкажи свій Telegram @нік:")

@router.message(Form.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Form.photo)
    await message.answer("Надішли фото (одне):")

@router.message(Form.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    caption = f"""
🖤 Ім’я: {data['name']}
📍 Місто: {data['city']}
🎧 Вайб: {data['vibe']}
💬 Шукає: {data['looking_for']}
📏 Зріст: {data['height']}
🔗 Telegram: {data['contact']}
"""
    await bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=caption)
    await message.answer("✅ Твою анкету надіслано до каналу. Дякуємо!")
    await state.clear()

@router.message(Form.photo)
async def warn_photo(message: Message):
    await message.answer("📸 Надішли саме фото, будь ласка.")

# ▶️ Запуск
async def main():
    try:
        logger.info("⏳ Видаляю активний webhook (якщо є)...")
        await bot.delete_webhook(drop_pending_updates=True)

        logger.info("🚀 Запускаю polling...")
        await dp.start_polling(bot)

    except TelegramConflictError as e:
        logger.error(f"⚠️ TelegramConflictError: {e}")
        raise SystemExit("🔴 Бот уже працює десь іще. Завершую...")

    except Exception as e:
        logger.exception("❌ Помилка при запуску")
        raise e

if __name__ == "__main__":
    asyncio.run(main())
