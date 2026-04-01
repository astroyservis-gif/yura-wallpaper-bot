import logging
import os
from dotenv import load_dotenv
import sqlite3
import requests
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
GOOGLE_SCRIPT_URL = os.getenv('GOOGLE_URL')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для диалога
class WorkState(StatesGroup):
    waiting_for_money = State()
    waiting_for_type = State()

# --- БАЗА ДАННЫХ (SQLite) ---
def init_db():
    conn = sqlite3.connect('work_log.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_sessions 
                      (user_id INTEGER PRIMARY KEY, start_time TEXT)''')
    conn.commit()
    conn.close()

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Старт"), KeyboardButton(text="🏁 Финиш")]
    ], resize_keyboard=True)

def get_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Флизелин", callback_data="type_флизелин")],
        [InlineKeyboardButton(text="Бумага", callback_data="type_бумага")]
    ])

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привет, Юра! Я помогу считать твой заработок.", reply_markup=get_main_kb())

@dp.message(F.text == "🚀 Старт")
async def start_work(message: types.Message):
    start_time = datetime.now().isoformat()
    conn = sqlite3.connect('work_log.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO active_sessions VALUES (?, ?)", (message.from_user.id, start_time))
    conn.commit()
    conn.close()
    await message.answer(f"Время пошло! Зафиксировал старт в {datetime.now().strftime('%H:%M')}")

@dp.message(F.text == "🏁 Финиш")
async def finish_work(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('work_log.db')
    cursor = conn.cursor()
    cursor.execute("SELECT start_time FROM active_sessions WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        await message.answer("Ты еще не нажал 'Старт'!")
        return

    start_time = datetime.fromisoformat(result[0])
    finish_time = datetime.now()
    duration = (finish_time - start_time).total_seconds() / 3600 # в часах

    await state.update_data(start=start_time, finish=finish_time, hours=round(duration, 2))
    await message.answer(f"Отработано: {round(duration, 2)} ч. Сколько заработал за этот выход (руб)?")
    await state.set_state(WorkState.waiting_for_money)

@dp.message(WorkState.waiting_for_money)
async def process_money(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число, пожалуйста.")
        return
    
    await state.update_data(money=int(message.text))
    await message.answer("Какой тип обоев клеил?", reply_markup=get_type_kb())
    await state.set_state(WorkState.waiting_for_type)

@dp.callback_query(F.data.startswith("type_"))
async def process_type(callback: types.CallbackQuery, state: FSMContext): # Не забудь FSMContext
    wallpaper_type = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Считаем разницу еще раз для точности (в часах)
    # Если часов 0 (тест), берем минимум 0.01 (около 30 секунд), чтобы не было деления на 0
    work_hours = data['hours'] if data['hours'] > 0.01 else 0.02 
    
    # Рассчитываем цену часа
    hourly_rate = round(data['money'] / work_hours, 0)
    
    # Формируем JSON для Google
    payload = {
        "date": data['start'].strftime("%Y-%m-%d"),
        "start": data['start'].strftime("%H:%M"),
        "finish": data['finish'].strftime("%H:%M"),
        "hours": data['hours'], # В таблицу пишем честный 0 или 0.01
        "money": data['money'],
        "hourly": hourly_rate,   # А цену часа считаем от минимального отрезка
        "type": wallpaper_type
    }

    # Отправка в Google Таблицу
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            await callback.message.edit_text(
                f"✅ Записано!\n"
                f"💰 Сумма: {data['money']} руб.\n"
                f"📈 Цена часа: {hourly_rate} руб/ч"
            )
        else:
            await callback.message.edit_text("❌ Ошибка при записи в таблицу.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка связи: {e}")

    await state.clear()

    # Отправка в Google Таблицу
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            await callback.message.edit_text(f"✅ Данные успешно записаны в таблицу!\nИтого: {data['money']} руб.")
        else:
            await callback.message.edit_text("❌ Ошибка при записи в таблицу.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка связи: {e}")

    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())