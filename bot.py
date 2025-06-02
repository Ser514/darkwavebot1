
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # приклад: '@darkwave_channel'

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

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

@dp.message_handler(commands='start')
async def start_handler(message: types.Message):
    await message.answer("🌑 Привіт у Darkwave.")
("Готовий заповнити анкету? Відповідай на запитання.")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Form.next()
    await message.answer("Скільки тобі років?")

@dp.message_handler(state=Form.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await Form.next()
    await message.answer("Звідки ти?")

@dp.message_handler(state=Form.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await Form.next()
    await message.answer("Яка твоя орієнтація? (Гетеро / Бі / Інше)")

@dp.message_handler(state=Form.orientation)
async def get_orientation(message: types.Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    await Form.next()
    await message.answer("Кого шукаєш?")

@dp.message_handler(state=Form.looking_for)
async def get_looking_for(message: types.Message, state: FSMContext):
    await state.update_data(looking_for=message.text)
    await Form.next()
    await message.answer("Опиши свій вайб, стиль або музику яку слухаєш:")

@dp.message_handler(state=Form.vibe)
async def get_vibe(message: types.Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await Form.next()
    await message.answer("Який твій зріст?")

@dp.message_handler(state=Form.height)
async def get_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await Form.next()
    await message.answer("Вкажи свій Telegram @нік:")

@dp.message_handler(state=Form.contact)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await Form.next()
    await message.answer("Надішли фото (одне):")

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.photo)
async def get_photo(message: types.Message, state: FSMContext):
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
    await state.finish()
