import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

import os
import re
import sys
import requests
import asyncio
import hashlib
import glob
import hashlib
from aiogram import types
from asyncio import sleep
from aiogram.filters import StateFilter
import sqlite3
import uuid
from aiogram.fsm.state import State, StatesGroup
class SetEmoji(StatesGroup):
    waiting_for_emoji = State()
    
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
class RenameProfile(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_rename_approve = State()  # Новое состояние для одобрения с новым именем

from db import init_db, get_profile_name, save_profile_name

DB_PATH = "vpn.db"
init_db(DB_PATH)

import subprocess
from datetime import datetime, timedelta, timezone
import psutil
import platform
import socket

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

cancel_markup = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

USERS_FILE = "users.txt"

LAST_MENU_FILE = "last_menu.json"

class SetEmojiState(StatesGroup):
    waiting_for_emoji = State()
    
# для SQLite
def save_profile_name(user_id, new_profile_name, db_path="/root/vpn.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    res = cur.fetchone()
    if res:
        cur.execute("UPDATE users SET profile_name=? WHERE id=?", (new_profile_name, user_id))
    else:
        cur.execute("INSERT INTO users (id, profile_name) VALUES (?, ?)", (user_id, new_profile_name))
    conn.commit()
    conn.close()


def save_user_id(user_id):
    try:
        user_id = str(user_id)
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w") as f:
                f.write(f"{user_id}\n")
        else:
            with open(USERS_FILE, "r+") as f:
                users = set(line.strip() for line in f)
                if user_id not in users:
                    f.write(f"{user_id}\n")
    except Exception as e:
        print(f"[save_user_id] Ошибка при сохранении user_id: {e}")


import json

MAX_BOT_MENUS = 1

PENDING_FILE = "pending_users.json"

class AdminAnnounce(StatesGroup):
    waiting_for_text = State()
    
async def safe_send_message(chat_id, text, **kwargs):
    print(f"[SAFE_SEND] chat_id={chat_id}, text={text[:50]}, kwargs={kwargs}")
    try:
        await bot.send_message(chat_id, text, **kwargs)
        print(f"[SAFE_SEND] success to {chat_id}!")
    except Exception as e:
        print(f"[Ошибка отправки сообщения] chat_id={chat_id}: {e}")


def get_last_menu_ids(user_id):
    if not os.path.exists(LAST_MENUS_FILE):
        return []
    try:
        with open(LAST_MENUS_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(user_id), [])
    except Exception:
        return []

async def delete_last_menus(user_id):
    if not os.path.exists(LAST_MENUS_FILE):
        return
    with open(LAST_MENUS_FILE, "r") as f:
        data = json.load(f)
    ids = data.get(str(user_id), [])
    for mid in ids:
        try:
            await bot.delete_message(user_id, mid)
        except Exception:
            pass
    data[str(user_id)] = []
    with open(LAST_MENUS_FILE, "w") as f:
        json.dump(data, f)

def set_last_menu_id(user_id, msg_id):
    data = {}
    if os.path.exists(LAST_MENUS_FILE):
        with open(LAST_MENUS_FILE, "r") as f:
            data = json.load(f)
    user_id = str(user_id)
    data[user_id] = [msg_id]
    with open(LAST_MENUS_FILE, "w") as f:
        json.dump(data, f)


    

def add_pending(user_id, username, fullname):
    pending = {}
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r") as f:
            pending = json.load(f)
    pending[str(user_id)] = {"username": username, "fullname": fullname}
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f)

def remove_pending(user_id):
    if not os.path.exists(PENDING_FILE):
        return
    with open(PENDING_FILE, "r") as f:
        pending = json.load(f)
    pending.pop(str(user_id), None)
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f)

def is_pending(user_id):
    if not os.path.exists(PENDING_FILE):
        return False
    try:
        with open(PENDING_FILE, "r") as f:
            pending = json.load(f)
    except Exception:
        pending = {}
    return str(user_id) in pending


load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID не задан в .env")
ADMIN_ID = int(ADMIN_ID)
EMOJI_FILE = "user_emojis.json"
LAST_MENUS_FILE = "last_menus.json"
MAX_MENUS_PER_USER = 3  # или сколько надо, обычно 3-5


ITEMS_PER_PAGE = 5
AUTHORIZED_USERS = [ADMIN_ID]  # Список Telegram ID пользователей
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

print(f"=== BOT START ===")
print(f"BOT_TOKEN starts with: {BOT_TOKEN[:8]}... (length: {len(BOT_TOKEN) if BOT_TOKEN else 0})")
print(f"ADMIN_ID: {ADMIN_ID} ({type(ADMIN_ID)})")
print(f"==================")

# Проверяем, что переменные окружения корректны
if not BOT_TOKEN or BOT_TOKEN == "<Enter API Token>":
    print("Ошибка: BOT_TOKEN не задан или содержит значение по умолчанию.")
    sys.exit(1)

if not ADMIN_ID or ADMIN_ID == "<Enter your user ID>":
    print("Ошибка: ADMIN_ID не задан или содержит значение по умолчанию.")
    sys.exit(1)


class VPNSetup(StatesGroup):
    """Класс состояний для управления процессами настройки VPN через бота."""

    choosing_option = State()  # Состояние выбора опции (добавление/удаление клиента).
    entering_client_name = State()  # Состояние ввода имени клиента.
    entering_days = State()  # Состояние ввода количества дней для сертификата.
    deleting_client = State()  # Состояние подтверждения удаления клиента.
    list_for_delete = State()  # Состояние выбора клиента из списка для удаления.
    choosing_config_type = State()  # Состояние для выбора конфигурации
    choosing_protocol = State()  # Для выбора протокола OpenVPN
    choosing_wg_type = State()  # Для выбора типа WireGuard
    confirming_rename = State()  # Для подтверждения переименования файлов WireGuard


# Описание для вашего бота
BOT_DESCRIPTION = """
ТУТ ВАШ ТЕКСТ
"""

BOT_SHORT_DESCRIPTION = "ТУТ ВАШ ТЕКСТ"


def user_registered(user_id):
    # Если юзер найден в базе — ОК
    return bool(get_profile_name(user_id))

APPROVED_FILE = "approved_users.txt"

# ==== Эмодзи хранение ====
@dp.message(StateFilter(SetEmoji.waiting_for_emoji))
async def set_user_emoji(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    client_name = (await state.get_data())['client_name']
    emoji = message.text.strip()

    # Удаляем текст "Введи смайл..."
    try:
        await message.reply_to_message.delete()
    except Exception:
        pass

    if emoji == "❌":
        set_emoji_for_user(client_name, "")  # твоя функция
        reply_text = "Смайл удалён"
    else:
        set_emoji_for_user(client_name, emoji)  # твоя функция
        reply_text = f"Установлен смайл: {emoji}"

    # Отправляем и через 2 сек удаляем сообщение
    info_msg = await message.answer(reply_text)
    await sleep(2)
    try:
        await info_msg.delete()
    except Exception:
        pass

    # Показываем меню управления пользователем
    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID), user_id=user_id)
    )
    await state.clear()

def is_approved_user(user_id):
    user_id = str(user_id)
    if not os.path.exists(APPROVED_FILE):
        return False
    with open(APPROVED_FILE, "r") as f:
        approved = [line.strip() for line in f]
    return user_id in approved

def approve_user(user_id):
    user_id = str(user_id)
    if not is_approved_user(user_id):
        with open(APPROVED_FILE, "a") as f:
            f.write(user_id + "\n")

def set_user_emoji(user_id, emoji):
    data = {}
    if os.path.exists(EMOJI_FILE):
        with open(EMOJI_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[str(user_id)] = emoji
    with open(EMOJI_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_user_emoji(user_id):
    if not os.path.exists(EMOJI_FILE):
        return ""
    with open(EMOJI_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(str(user_id), "")

async def switch_menu(callback: types.CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await callback.message.delete()
    except Exception:
        pass  # сообщение уже могло быть удалено
    await bot.send_message(callback.from_user.id, text, reply_markup=reply_markup, parse_mode=parse_mode)

async def set_bot_commands():
    """
    Асинхронная функция для установки списка команд бота.
    """
    async with Bot(token=BOT_TOKEN) as bot:
        commands = [
            BotCommand(command="start", description="Запустить бота"),
        ]

        await bot.set_my_commands(commands)

@dp.callback_query(lambda c: c.data.startswith("approve_rename_"))
async def process_application_rename(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_", 2)[-1])
    # Сохраняем id заявки (меню заявки)
    await state.update_data(approve_user_id=user_id, pending_menu_msg_id=callback.message.message_id)
    try:
        await callback.message.delete()  # Уже удаляем
    except Exception:
        pass
    msg = await bot.send_message(
        callback.from_user.id,
        f"Введи новое имя для пользователя (id <code>{user_id}</code>):",
        parse_mode="HTML"
    )
    await state.set_state(RenameProfile.waiting_for_rename_approve)
    await state.update_data(rename_prompt_id=msg.message_id)
    await callback.answer()



@dp.message(RenameProfile.waiting_for_rename_approve)
async def process_rename_new_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    rename_prompt_id = data.get("rename_prompt_id")
    pending_menu_msg_id = data.get("pending_menu_msg_id")

    # Удаляем prompt "Введи новое имя..."
    if rename_prompt_id:
        try:
            await bot.delete_message(message.chat.id, rename_prompt_id)
        except Exception:
            pass

    # Удаляем само сообщение пользователя (введённое имя)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    user_id = data.get("approve_user_id")
    if not user_id:
        await message.answer("Ошибка: не найден id пользователя.")
        await state.clear()
        return

    if not re.match(r"^[a-zA-Z0-9_-]{1,32}$", new_name):
        await safe_send_message(
            message.chat.id, "❌ Некорректное имя! Используй только буквы, цифры, _ и -."
        )
        await state.clear()
        return

    result = await execute_script("1", new_name, "30")
    if result["returncode"] == 0:
        save_profile_name(user_id, new_name)
        approve_user(user_id)
        remove_pending(user_id)
        save_user_id(user_id)  # ВАЖНО! — сразу в users.txt
        msg = await safe_send_message(
            user_id,
            f"✅ Ваша заявка одобрена!\nИмя профиля: <b>{new_name}</b>\nТеперь вам доступны функции VPN.",
            parse_mode="HTML",
            reply_markup=create_user_menu(new_name)
        )
        # УДАЛЯЕМ сообщение "Пользователь ... активирован"
        try:
            await bot.delete_message(message.chat.id, msg.message_id)
        except Exception:
            pass

        # Главное меню админу
        stats = get_server_info()
        menu = await show_menu(
            message.chat.id,
            stats + "\n<b>Главное меню:</b>",
            create_main_menu()
        )
        set_last_menu_id(message.chat.id, menu.message_id)
    else:
        await safe_send_message(
            message.chat.id,
            f"❌ Ошибка: {result['stderr']}"
        )
    await state.clear()




    

async def ensure_user_client(user_id: int):
    client_name = get_profile_name(user_id)
    
    if not await client_exists("openvpn", client_name):
        result = await execute_script("1", client_name, "30")  # Срок по умолчанию: 10 лет
        if result["returncode"] != 0:
            print(f"Ошибка создания клиента: {result['stderr']}")
            return False

    return True


async def update_bot_description():
    """
    Асинхронная функция для обновления описания бота.

    Описание устанавливается для русского языка ("ru").
    """
    async with Bot(token=BOT_TOKEN) as bot:
        await bot.set_my_description(BOT_DESCRIPTION, language_code="ru")


BOT_ABOUT = "ТУТ ВАШ ТЕКСТ"


async def update_bot_about():
    """Асинхронная функция для обновления раздела «О боте»."""
    async with Bot(token=BOT_TOKEN) as bot:
        await bot.set_my_short_description(BOT_ABOUT, language_code="ru")


def get_external_ip():
    try:
        response = requests.get("https://api.ipify.org", timeout=10)
        if response.status_code == 200:
            return response.text
        return "IP не найден"
    except requests.Timeout:
        return "Ошибка: запрос превысил время ожидания."
    except requests.ConnectionError:
        return "Ошибка: нет подключения к интернету."
    except requests.RequestException as e:
        return f"Ошибка при запросе: {e}"
SERVER_IP = get_external_ip()

def get_server_info():
    ip = SERVER_IP
    uptime_seconds = int(psutil.boot_time())
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    hostname = socket.gethostname()
    os_version = platform.platform()
    return f"""<b>💻 Сервер:</b> <code>{hostname}</code>
<b>🌐 IP:</b> <code>{ip}</code>
<b>🕒 Аптайм:</b> <code>{str(uptime).split('.')[0]}</code>
<b>🧠 RAM:</b> <code>{mem}%</code>
<b>⚡ CPU:</b> <code>{cpu}%</code>
<b>🛠 ОС:</b> <code>{os_version}</code>
"""

# ==== Главное меню ====
def create_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users_menu")],
        [InlineKeyboardButton(text="➕➖ Добавить или удалить", callback_data="add_del_menu")],
        [InlineKeyboardButton(text="♻️ Пересоздать файлы", callback_data="7")],
        [InlineKeyboardButton(text="📦 Создать бэкап", callback_data="8")],
        [InlineKeyboardButton(text="📋 Заявки на одобрение", callback_data="admin_pending_list")],
        [InlineKeyboardButton(text="🛠 Управление сервером", callback_data="server_manage_menu")],
        [InlineKeyboardButton(text="📢 Объявление", callback_data="announce_menu")],
        [InlineKeyboardButton(text="🟢 Кто онлайн", callback_data="who_online")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.callback_query(lambda c: c.data == "server_manage_menu")
async def server_manage_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return
    await callback.message.edit_text(
        "🛠 <b>Управление сервером:</b>", 
        reply_markup=create_server_manage_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "restart_bot")
async def handle_bot_restart(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    msg = await callback.message.edit_text("♻️ Перезапускаю бота через systemd...")
    await callback.answer()
    await asyncio.sleep(1)
    await msg.delete()
    await bot.send_message(
        callback.from_user.id,
        f"{get_server_info()}\n<b>👨‍💻 Главное меню:</b>",
        reply_markup=create_main_menu(),
        parse_mode="HTML"
    )

    os.system("systemctl restart vpnbot.service")

@dp.callback_query(lambda c: c.data == "reboot_server")
async def handle_reboot(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    msg = await callback.message.edit_text("🔁 Сервер перезагружается...")
    await callback.answer()
    await asyncio.sleep(1)
    await msg.delete()
    await bot.send_message(
        callback.from_user.id,
        f"{get_server_info()}\n<b>👨‍💻 Главное меню:</b>",
        reply_markup=create_main_menu(),
        parse_mode="HTML"
    )
    os.system("reboot")


def create_server_manage_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="♻️ Перезагрузка бота", callback_data="restart_bot")],
        [types.InlineKeyboardButton(text="🔁 Перезагрузка сервера", callback_data="reboot_server")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")],
    ])




@dp.callback_query(lambda c: c.data == "admin_pending_list")
async def show_pending_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет прав!", show_alert=True)
        return

    # Нет файла с заявками
    if not os.path.exists(PENDING_FILE):
        await callback.message.delete()
        msg = await bot.send_message(callback.from_user.id, "Нет заявок.")
        await asyncio.sleep(1)
        try:
            await bot.delete_message(callback.from_user.id, msg.message_id)
        except Exception:
            pass
        # Показываем главное меню!
        stats = get_server_info()
        menu = await bot.send_message(
            callback.from_user.id,
            stats + "\n<b>Главное меню:</b>",
            reply_markup=create_main_menu(),
            parse_mode="HTML"
        )
        set_last_menu_id(callback.from_user.id, menu.message_id)
        return

    # Файл есть, но заявок нет
    with open(PENDING_FILE) as f:
        pending = json.load(f)
    if not pending:
        await callback.message.delete()
        msg = await bot.send_message(callback.from_user.id, "Нет заявок.")
        await asyncio.sleep(1)
        try:
            await bot.delete_message(callback.from_user.id, msg.message_id)
        except Exception:
            pass
        # Показываем главное меню!
        stats = get_server_info()
        menu = await bot.send_message(
            callback.from_user.id,
            stats + "\n<b>Главное меню:</b>",
            reply_markup=create_main_menu(),
            parse_mode="HTML"
        )
        set_last_menu_id(callback.from_user.id, menu.message_id)
        return

    # Если заявки есть — стандартный вывод
    text = "📋 <b>Заявки на одобрение:</b>\n"
    keyboard = []
    for uid, info in pending.items():
        username = info.get("username") or "-"
        fullname = info.get("fullname") or "-"
        text += f"\nID: <code>{uid}</code> @{username}\nИмя: {fullname}\n"
        keyboard.append([
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{uid}"),
            InlineKeyboardButton(text="✏️ Одобрить с изменением имени", callback_data=f"approve_rename_{uid}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{uid}"),
        ])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "add_user")
async def add_user_start(callback: types.CallbackQuery, state: FSMContext):
    await delete_last_menus(callback.from_user.id)  # Чистим старые меню!
    await state.update_data(action="1")  # <-- вот ЭТО!
    msg = await bot.send_message(
        callback.from_user.id,
        "Введите имя нового пользователя:",
        reply_markup=cancel_markup
    )
    await state.update_data(add_user_msg_id=msg.message_id)
    await state.set_state(VPNSetup.entering_client_name)
    await callback.answer()


# ==== Список пользователей с эмодзи ====
@dp.callback_query(lambda c: c.data == "users_menu")
async def users_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет прав!", show_alert=True)
        return

    clients = await get_clients("openvpn")
    online = get_online_users_from_log()
    if not clients:
        await show_menu(callback.from_user.id, "❌ Нет пользователей.", create_main_menu())
        return
    keyboard = []
    for client in clients:
        if client == "antizapret-client":
            continue
        emoji = ""
        user_id = get_user_id_by_name(client)
        if user_id:
            emoji = get_user_emoji(user_id)
        online_status = "🟢" if client in online else "🔴"
        display_name = f"{emoji + ' ' if emoji else ''}{online_status} {client}"
        if user_id:
            keyboard.append([
                InlineKeyboardButton(text=display_name, callback_data=f"manage_userid_{user_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(text=display_name, callback_data=f"manage_user_{client}")
            ])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await show_menu(
        callback.from_user.id,
        "Список пользователей. Нажмите на пользователя для управления:",
        markup
    )
    await callback.answer()

def create_wg_menu(client_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обычный VPN",
                callback_data=f"download_wg_vpn_{client_name}"
            ),
            InlineKeyboardButton(
                text="Antizapret (Рекомендую)",
                callback_data=f"download_wg_antizapret_{client_name}"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_user_menu_{client_name}")]
    ])

def create_amnezia_menu(client_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обычный VPN",
                callback_data=f"download_am_vpn_{client_name}"
            ),
            InlineKeyboardButton(
                text="Antizapret (Рекомендую)",
                callback_data=f"download_am_antizapret_{client_name}"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_user_menu_{client_name}")]
    ])

@dp.callback_query(lambda c: c.data.startswith("get_wg_"))
async def get_wg_menu(callback: types.CallbackQuery):
    client_name = callback.data[len("get_wg_"):]
    await delete_last_menus(callback.from_user.id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        callback.from_user.id,
        "Выберите тип WireGuard-конфига:",
        reply_markup=create_wg_menu(client_name)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("get_amnezia_"))
async def get_amnezia_menu(callback: types.CallbackQuery):
    client_name = callback.data[len("get_amnezia_"):]
    await delete_last_menus(callback.from_user.id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        callback.from_user.id,
        "Выберите тип Amnezia-конфига:",
        reply_markup=create_amnezia_menu(client_name)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("download_wg_"))
async def download_wg_config(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    _, _, wg_type, client_name = parts
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"

    if wg_type == "vpn":
        file_path = f"/root/antizapret/client/wireguard/vpn/${FILEVPN_NAME} - Обычный VPN -{client_name}.conf"
    else:
        file_path = f"/root/antizapret/client/wireguard/antizapret/${FILEVPN_NAME} -{client_name}.conf"

    # Генерируем, если нет файла
    if not os.path.exists(file_path):
        subprocess.run(['/root/antizapret/client.sh', '4', client_name], check=True)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await delete_last_menus(user_id)

    if os.path.exists(file_path):
        await bot.send_document(user_id, FSInputFile(file_path), caption=f"🔐 {os.path.basename(file_path)}")
        await notify_admin_download(user_id, username, os.path.basename(file_path), "wg")
    else:
        await bot.send_message(user_id, "❌ Файл не найден")

    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID), user_id=user_id)
    )

    await callback.answer()






@dp.callback_query(lambda c: c.data.startswith("download_wg_"))
async def download_wg_config(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    _, _, wg_type, client_name = parts
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"

    if wg_type == "vpn":
        file_path = f"/root/antizapret/client/wireguard/vpn/${FILEVPN_NAME} - Обычный VPN -{client_name}.conf"
    else:
        file_path = f"/root/antizapret/client/wireguard/antizapret/${FILEVPN_NAME} -{client_name}.conf"

    # Генерируем если нет файла
    if not os.path.exists(file_path):
        subprocess.run(['/root/antizapret/client.sh', '4', client_name], check=True)

    # Удаляем старое меню
    try:
        await callback.message.delete()
    except Exception:
        pass
    await delete_last_menus(user_id)

    # Отправляем файл если есть
    if os.path.exists(file_path):
        await bot.send_document(user_id, FSInputFile(file_path), caption=f"🔐 {os.path.basename(file_path)}")
        await notify_admin_download(user_id, username, os.path.basename(file_path), "wg")
    else:
        await bot.send_message(user_id, "❌ Файл не найден")

    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID), user_id=user_id)
    )
    await callback.answer()






# ==== Админ: установка смайла ====
@dp.callback_query(lambda c: c.data.startswith("set_emoji_"))
async def set_emoji_start(callback: types.CallbackQuery, state: FSMContext):
    client_name = callback.data[len("set_emoji_"):]
    user_id = callback.from_user.id
    target_user_id = get_user_id_by_name(client_name)
    if not target_user_id:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return
    await state.set_state(SetEmojiState.waiting_for_emoji)
    await state.update_data(target_user_id=target_user_id, client_name=client_name)

    # Инлайн-кнопка отмены
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_set_emoji")]
        ]
    )
    msg = await bot.send_message(
        user_id,
        "Введи смайл (эмодзи) для этого пользователя, или отправь ❌ чтобы убрать смайл.",
        reply_markup=markup
    )
    # Сохраним id сообщения для удаления
    await state.update_data(input_message_id=msg.message_id)

@dp.callback_query(lambda c: c.data == "cancel_set_emoji")
async def cancel_set_emoji(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("input_message_id")
    client_name = data.get("client_name")
    try:
        await callback.bot.delete_message(callback.from_user.id, msg_id)
    except:
        pass
    await callback.answer("Отменено")
    await state.clear()
    await show_menu(
        callback.from_user.id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=True, user_id=get_user_id_by_name(client_name))
    )



@dp.message(SetEmojiState.waiting_for_emoji)
async def set_emoji_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    client_name = data.get("client_name")
    input_msg_id = data.get("input_message_id")

    # Удаляем сообщение с инструкцией
    try:
        await message.bot.delete_message(message.from_user.id, input_msg_id)
    except:
        pass

    emoji = message.text.strip()
    if emoji == "❌":
        set_user_emoji(target_user_id, "")
        text = "Смайл убран."
    else:
        if len(emoji) > 2:
            warn_msg = await message.answer("❌ Слишком длинный смайл!")
            await asyncio.sleep(2)
            await warn_msg.delete()
            return
        set_user_emoji(target_user_id, emoji)
        text = f"Установлен смайл: {emoji}"

    # Вывести уведомление, потом удалить через 2 сек
    notif = await message.answer(text)
    await asyncio.sleep(2)
    try:
        await notif.delete()
    except:
        pass

    await show_menu(
        message.from_user.id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=True, user_id=target_user_id)
    )
    await state.clear()

    
# ==== Выдача WireGuard ====
@dp.callback_query(lambda c: c.data.startswith("get_wg_"))
async def send_wg_config(callback: types.CallbackQuery):
    client_name = callback.data[len("get_wg_"):]
    user_id = callback.from_user.id
    await execute_script("4", client_name)
    file_path = find_conf("/root/antizapret/client/wireguard", client_name)
    if not file_path:
        await callback.answer("❌ Файл WG не найден", show_alert=True)
        return
    await bot.send_document(
        user_id,
        FSInputFile(file_path),
        caption=f"🔐 WireGuard: {os.path.basename(file_path)}"
    )
    await callback.answer("✅ WireGuard-конфиг отправлен.")

    
def find_conf(base_dir, client_name):
    # Ищет во всех подпапках и по всем шаблонам
    patterns = [
        f"{base_dir}/*/*{client_name}*.conf",
        f"{base_dir}/*{client_name}*.conf",
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None    


def find_wg_conf(client_name):
    patterns = [
        f"/root/antizapret/client/wireguard/*/*{client_name}*.conf",
        f"/root/antizapret/client/wireguard/*{client_name}*.conf",
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

   

# Новый вариант — по user_id
@dp.callback_query(lambda c: c.data.startswith("manage_userid_"))
async def manage_user_by_id(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_", 2)[-1])
    client_name = get_profile_name(target_user_id)
    if not client_name:
        await callback.answer("Ошибка: пользователь не найден!", show_alert=True)
        return
    await delete_last_menus(callback.from_user.id)
    await show_menu(
        callback.from_user.id,
        f"Управление клиентом <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(callback.from_user.id == ADMIN_ID))
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("manage_user_"))
async def manage_user(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await delete_last_menus(user_id)
    client_name = callback.data.split("_", 2)[-1]
    await state.update_data(client_name=client_name)  # <= вот это всегда!
    await show_menu(
        user_id,
        f"Управление клиентом <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID))
    )
    await callback.answer()


def get_user_id_by_name(profile_name):
    conn = sqlite3.connect("/root/vpn.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE profile_name=?", (profile_name,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None



@dp.callback_query(lambda c: c.data == "7")
async def recreate_files(callback: types.CallbackQuery, state: FSMContext):
    result = await execute_script("7")
    if result["returncode"] == 0:
        await callback.message.edit_text("✅ Файлы успешно пересозданы!")
        await asyncio.sleep(1)
        try:
            await callback.message.delete()
        except Exception:
            pass
        # Удаляем все предыдущие меню!
        await delete_last_menus(callback.from_user.id)
        await state.clear()
        # Делаем с инфой сервера если админ
        if callback.from_user.id == ADMIN_ID:
            stats = get_server_info()
            menu_text = stats + "\n<b>Главное меню:</b>"
        else:
            menu_text = "Главное меню:"
        msg = await bot.send_message(callback.from_user.id, menu_text, reply_markup=create_main_menu(), parse_mode="HTML")
        set_last_menu_id(callback.from_user.id, msg.message_id)
    else:
        await callback.message.edit_text(f"❌ Ошибка: {result['stderr']}")
    await callback.answer()




@dp.callback_query(lambda c: c.data == "announce_menu")
async def admin_announce_menu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Нет прав!", show_alert=True)
        return

    # Удаляем все старые меню (ПРАВИЛЬНО!)
    await delete_last_menus(user_id)

    # Одно новое через show_menu!
    msg = await show_menu(
        user_id,
        "✏️ Введите текст объявления:",
        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]])
    )
    await state.update_data(announce_msg_id=msg.message_id)
    await state.set_state(AdminAnnounce.waiting_for_text)
    await callback.answer()



 
@dp.message(AdminAnnounce.waiting_for_text)
async def process_announce_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    announce_msg_id = data.get("announce_msg_id")

    # Сразу удаляем как пользовательское сообщение, так и форму
    try:
        await bot.delete_message(user_id, message.message_id)
        if announce_msg_id:
            await bot.delete_message(user_id, announce_msg_id)
    except Exception:
        pass

    text = message.text.strip()
    if text == "⬅️ Назад":
        # Очистили всё — теперь просто показываем главное меню через show_menu
        await state.clear()
        stats = get_server_info()
        await show_menu(user_id, stats + "\n<b>Главное меню:</b>", create_main_menu())
        return

    if not text:
        # если пустой ввод — заново показываем форму
        msg = await show_menu(
            user_id,
            "✏️ Текст не может быть пустым. Введите текст объявления:",
            InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]]
            )
        )
        await state.update_data(announce_msg_id=msg.message_id)
        return

    # иначе рассылаем
    sent, failed = await announce_all(text)
    await bot.send_message(user_id, f"✅ Отправлено: {sent}, не доставлено: {failed}")
    await state.clear()
    stats = get_server_info()
    await show_menu(user_id, stats + "\n<b>Главное меню:</b>", create_main_menu())



async def announce_all(text):
    if not os.path.exists(USERS_FILE):
        return 0, 0

    sent, failed = 0, 0
    with open(USERS_FILE) as f:
        users = [line.strip() for line in f if line.strip().isdigit()]
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 <b>Объявление:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Не удалось отправить {uid}: {e}")

    return sent, failed


@dp.callback_query(lambda c: c.data == "8")
async def backup_files(callback: types.CallbackQuery):
    await callback.message.edit_text("⏳ Создаю бэкап...")
    result = await execute_script("8")
    if result["returncode"] == 0:
        if await send_backup(callback.from_user.id):
            await callback.message.delete()
            # То же самое, меню со статистикой!
            if callback.from_user.id == ADMIN_ID:
                stats = get_server_info()
                menu_text = stats + "\n<b>Главное меню:</b>"
            else:
                menu_text = "Главное меню:"
            await bot.send_message(callback.from_user.id, menu_text, reply_markup=create_main_menu(), parse_mode="HTML")
        else:
            await callback.message.edit_text("❌ Не удалось отправить бэкап")
    else:
        await callback.message.edit_text(f"❌ Ошибка при создании бэкапа: {result['stderr']}")
    await callback.answer()



@dp.callback_query(lambda c: c.data == "del_user")
async def del_user_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await delete_last_menus(user_id)  # ← ОБЯЗАТЕЛЬНО сюда!
    clients = await get_clients("openvpn")
    if not clients:
        await show_menu(user_id, "❌ Нет пользователей для удаления.", create_main_menu())
        return
    keyboard = [
        [InlineKeyboardButton(text=client, callback_data=f"ask_del_{client}")]
        for client in clients
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="add_del_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    msg = await bot.send_message(user_id, "Выберите пользователя для удаления:", reply_markup=markup)
    set_last_menu_id(user_id, msg.message_id)
    await callback.answer()






@dp.callback_query(lambda c: c.data.startswith("ask_del_"))
async def ask_delete_user(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    client_name = callback.data.split("_", 2)[-1]
    await delete_last_menus(user_id)  # ← добавь это!
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_{client_name}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="del_user")]
        ]
    )
    await bot.send_message(user_id, f"Удалить пользователя <b>{client_name}</b>?", reply_markup=markup, parse_mode="HTML")
    await callback.answer()



@dp.callback_query(lambda c: c.data.startswith("confirm_del_"))
async def confirm_delete_user(callback: types.CallbackQuery):
    client_name = callback.data.split("_", 2)[-1]
    user_id = callback.from_user.id

    result = await execute_script("2", client_name)
    stats = get_server_info()
    # 1. Удаляем само сообщение с подтверждением
    try:
        await callback.message.delete()
    except Exception:
        pass

    # 2. Отправляем новое главное меню (одно)
    if result["returncode"] == 0:
        await show_menu(
            user_id,
            f"✅ Пользователь <b>{client_name}</b> удалён.\n\n{stats}\n<b>Главное меню:</b>",
            create_main_menu()
        )
    else:
        await show_menu(
            user_id,
            f"❌ Ошибка удаления: {result['stderr']}\n\n{stats}\n<b>Главное меню:</b>",
            create_main_menu()
        )
    await callback.answer()



def get_cert_expiry_days(cert_path):
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            return 30  # fallback, если не нашли сертификат
        not_after = result.stdout.strip().replace("notAfter=", "")
        dt = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        days_left = (dt - datetime.now(timezone.utc)).days
        return max(days_left, 1)
    except Exception as e:
        print(f"Ошибка чтения срока сертификата: {e}")
        return 30  # fallback

def create_openvpn_menu():
    """Создает меню OpenVPN в виде InlineKeyboardMarkup."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🆕 Создать клиента", callback_data="1"),
                InlineKeyboardButton(text="❌ Удалить клиента", callback_data="2"),
            ],
            [
                InlineKeyboardButton(text="📝 Список клиентов", callback_data="3"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"),
            ],
        ]
    )

@dp.callback_query(lambda c: c.data == "rename_cancel")
async def rename_cancel(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Сохраняем имя профиля до очистки состояния
    data = await state.get_data()
    client_name = data.get("old_username")

    await state.clear()
    await delete_last_menus(user_id)

    is_admin = (user_id == ADMIN_ID)
    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=is_admin)
    )

    await callback.answer()







@dp.callback_query(lambda c: c.data.startswith("rename_profile_"))
async def start_rename_profile(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    old_username = callback.data.split("_", 2)[-1]
    await state.update_data(old_username=old_username)
    # Удаляем все прошлые меню
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()  # ВАЖНО: удаляем меню управления пользователем!
    except Exception:
        pass

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="rename_cancel")]
        ]
    )
    msg = await bot.send_message(
        user_id,
        f"Введите новое имя для профиля (сейчас: <b>{old_username}</b>):",
        parse_mode="HTML",
        reply_markup=markup
    )
    set_last_menu_id(user_id, msg.message_id)
    await state.set_state(RenameProfile.waiting_for_new_name)
    await callback.answer()



async def show_menu(user_id, text, reply_markup, parse_mode="HTML"):
    await delete_last_menus(user_id)  # Удаляем все прошлые меню этого юзера
    msg = await bot.send_message(user_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    set_last_menu_id(user_id, msg.message_id)
    return msg


@dp.callback_query(lambda c: c.data.startswith("get_amnezia_"))
async def send_amnezia_config(callback: types.CallbackQuery):
    client_name = callback.data[len("get_amnezia_"):]
    user_id = callback.from_user.id
    # Всегда создавать/пересоздавать перед выдачей!
    await execute_script("4", client_name)
    file_path = find_conf("/root/antizapret/client/amneziawg", client_name)
    if not file_path:
        await callback.answer("❌ Файл Amnezia не найден", show_alert=True)
        return
    await bot.send_document(
        user_id,
        FSInputFile(file_path),
        caption=f"🔐 Amnezia: {os.path.basename(file_path)}"
    )
    await callback.answer("✅ Amnezia-конфиг отправлен.")



@dp.callback_query(lambda c: c.data.startswith("download_am_"))
async def download_amnezia_config(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    _, _, am_type, client_name = parts
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"

    if am_type == "vpn":
        file_path = f"/root/antizapret/client/amneziawg/vpn/${FILEVPN_NAME} - Обычный VPN -{client_name}.conf"
    else:
        file_path = f"/root/antizapret/client/amneziawg/antizapret/${FILEVPN_NAME} -{client_name}.conf"

    if not os.path.exists(file_path):
        subprocess.run(['/root/antizapret/client.sh', '4', client_name], check=True)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await delete_last_menus(user_id)

    if os.path.exists(file_path):
        await bot.send_document(user_id, FSInputFile(file_path), caption=f"🔐 {os.path.basename(file_path)}")
        await notify_admin_download(user_id, username, os.path.basename(file_path), "amnezia")
    else:
        await bot.send_message(user_id, "❌ Файл не найден")

    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID), user_id=user_id)
    )

    await callback.answer()




# Новые функции для создания меню выбора
def create_openvpn_config_menu(client_name: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="VPN", callback_data=f"openvpn_config_vpn_{client_name}"
                ),
                InlineKeyboardButton(
                    text="Antizapret",
                    callback_data=f"openvpn_config_antizapret_{client_name}",
                ),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_client_list")],
        ]
    )


def create_openvpn_protocol_menu(interface: str, client_name: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Стандартный (auto)",
                    callback_data=f"send_ovpn_{interface}_default_{client_name}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="TCP", callback_data=f"send_ovpn_{interface}_tcp_{client_name}"
                ),
                InlineKeyboardButton(
                    text="UDP", callback_data=f"send_ovpn_{interface}_udp_{client_name}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"back_to_interface_{interface}_{client_name}",
                )
            ],
        ]
    )

def create_client_list_keyboard(clients, page, total_pages, vpn_type, action):
    """Создает клавиатуру с клиентами VPN."""
    buttons = []
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE

    for client in clients[start_idx:end_idx]:
        prefix = "delete" if action == "delete" else "client"
        callback_data = f"{action}_{vpn_type}_{client}"

        if action == "delete":
            callback_data = f"delete_{vpn_type}_{client}"
        else:  # действие "client" (выдача конфигурационного файла)
            callback_data = f"client_{vpn_type}_{client}"

        buttons.append([InlineKeyboardButton(text=client, callback_data=callback_data)])

    pagination = []
    if page > 1:
        pagination.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущая", callback_data=f"page_{action}_{vpn_type}_{page-1}"
            )
        )
    if page < total_pages:
        pagination.append(
            InlineKeyboardButton(
                text="Следующая ➡️", callback_data=f"page_{action}_{vpn_type}_{page+1}"
            )
        )

    if pagination:
        buttons.append(pagination)

    buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{vpn_type}_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_confirmation_keyboard(client_name, vpn_type):
    """Создает клавиатуру подтверждения удаления клиента."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"confirm_{vpn_type}_{client_name}",
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"),
            ]
        ]
    )

def get_user_traffic(client_name):
    log_files = [
        "/etc/openvpn/server/logs/antizapret-tcp-status.log",
        "/etc/openvpn/server/logs/antizapret-udp-status.log",
        "/etc/openvpn/server/logs/vpn-tcp-status.log",
        "/etc/openvpn/server/logs/vpn-udp-status.log",
    ]
    total_received = 0
    total_sent = 0
    for log_path in log_files:
        try:
            if os.path.exists(log_path):
                with open(log_path) as f:
                    for line in f:
                        if line.startswith("CLIENT_LIST"):
                            parts = line.strip().split(",")
                            if len(parts) > 4 and parts[1] == client_name:
                                # parts[3]: Bytes received
                                # parts[4]: Bytes sent
                                try:
                                    total_received += int(parts[3])
                                    total_sent += int(parts[4])
                                except Exception:
                                    continue
        except Exception:
            continue
    # Переводим в Гб (1 Гб = 1024^3 байт)
    gb_received = total_received / (1024**3)
    gb_sent = total_sent / (1024**3)
    return round(gb_sent, 2), round(gb_received, 2)

@dp.callback_query(lambda c: c.data.startswith("renew_user_"))
async def renew_user_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return
    client_name = callback.data.split("_", 2)[-1]
    await state.update_data(client_name=client_name)  # <= обновили!
    await callback.message.delete()

    msg = await bot.send_message(
        callback.from_user.id,
        f"✏️ <b>Установить срок действия</b>\n\n"
        f"Введите новый срок действия <b>(в днях)</b> для пользователя <code>{client_name}</code>:\n"
        f"<b>⚠️ Текущий срок будет заменён новым!</b>\n"
        f"(после подтверждения)",
        parse_mode="HTML",
        reply_markup=cancel_markup
    )
    await state.update_data(renew_msg_ids=[msg.message_id])
    await state.set_state(VPNSetup.entering_days)
    await callback.answer()




from datetime import datetime, timezone

def get_cert_expiry_info(client_name):
    cert_path = f"/etc/openvpn/easyrsa3/pki/issued/{client_name}.crt"
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            return None
        not_after = result.stdout.strip().replace("notAfter=", "")
        date_to = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_left = (date_to - now).days

        # Теперь узнаём дату выпуска (startdate)
        result2 = subprocess.run(
            ["openssl", "x509", "-in", cert_path, "-noout", "-startdate"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        not_before = result2.stdout.strip().replace("notBefore=", "")
        date_from = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)

        return {
            "date_from": date_from,
            "date_to": date_to,
            "days_left": days_left
        }
    except Exception as e:
        print(f"Ошибка чтения срока сертификата: {e}")
        return None


@dp.message(VPNSetup.entering_days)
async def process_renew_days(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    renew_ids = data.get("renew_msg_ids", [])
    client_name = data.get("client_name")  # <-- тут всегда получаем имя!

    # Удаляем временные сообщения (например, "Введите срок" и ожидание)
    for mid in set(renew_ids):
        try:
            await bot.delete_message(user_id, mid)
        except Exception:
            pass
    await state.update_data(renew_msg_ids=[])

    text = message.text.strip()

    # Обработка отмены
    if text == "❌ Отмена":
        await state.clear()
        is_admin = (user_id == ADMIN_ID)
        await show_menu(
            user_id,
            f"Меню пользователя <b>{client_name}</b>:",
            create_user_menu(client_name, back_callback="users_menu", is_admin=is_admin)
        )
        return

    # Проверка на корректность ввода
    if not text.isdigit() or int(text) < 1:
        m1 = await message.answer("❌ Введи корректное количество дней (целое число)", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        try:
            await m1.delete()
        except Exception:
            pass
        # Возвращаемся в меню пользователя, а не в главное!
        is_admin = (user_id == ADMIN_ID)
        await show_menu(
            user_id,
            f"Меню пользователя <b>{client_name}</b>:",
            create_user_menu(client_name, back_callback="users_menu", is_admin=is_admin)
        )
        await state.clear()
        return

    days = int(text)

    msg_wait = await message.answer(
        f"⏳ Устанавливаю новый срок действия для <b>{client_name}</b> — {days} дней...",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.update_data(renew_msg_ids=[msg_wait.message_id])

    result = await execute_script("9", client_name, str(days))

    # Удаляем сообщение ожидания
    try:
        await bot.delete_message(user_id, msg_wait.message_id)
    except Exception:
        pass
    await state.update_data(renew_msg_ids=[])

    if result["returncode"] == 0:
        cert_info = get_cert_expiry_info(client_name)
        if cert_info:
            date_to_str = cert_info["date_to"].strftime('%d.%m.%Y')
            days_left = cert_info["days_left"]
            status = f"Сертификат действует до <b>{date_to_str}</b> (осталось <b>{days_left}</b> дней)."
        else:
            status = "Не удалось определить срок действия сертификата."
        msg_ok = await message.answer(
            f"✅ <b>Срок действия установлен!</b>\n{status}",
            parse_mode="HTML"
        )
        await asyncio.sleep(1)
        try:
            await msg_ok.delete()
        except Exception:
            pass

    else:
        await message.answer(
            f"❌ Ошибка установки срока: {result['stderr']}",
            parse_mode="HTML"
        )

    # В любом случае выводим одно меню пользователя
    is_admin = (user_id == ADMIN_ID)
    await show_menu(
        user_id,
        f"Меню пользователя <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=is_admin)
    )
    await state.clear()



# ==== Меню управления пользователем (с эмодзи и WG/Amnezia кнопками) ====
def create_user_menu(client_name, back_callback=None, is_admin=False, user_id=None):
    emoji = ""
    if user_id:
        emoji = get_user_emoji(user_id)
    menu_title = f"{emoji + ' ' if emoji else ''}{client_name}"
    keyboard = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data=f"user_stats_{client_name}")],
        [InlineKeyboardButton(text="📥 Получить конфиг OpenVPN", callback_data=f"select_openvpn_{client_name}")],
        [InlineKeyboardButton(text="🌐 Получить WireGuard", callback_data=f"get_wg_{client_name}")],
        [InlineKeyboardButton(text="🦄 Получить Amnezia", callback_data=f"get_amnezia_{client_name}")],
        [InlineKeyboardButton(text="📬 Получить VLESS", callback_data=f"get_vless_{client_name}")],
        [InlineKeyboardButton(text="✏️ Изменить имя профиля", callback_data=f"rename_profile_{client_name}")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🤡 Установить смайл", callback_data=f"set_emoji_{client_name}")])
        keyboard.append([InlineKeyboardButton(text="✏️ Установить срок действия", callback_data=f"renew_user_{client_name}")])
        keyboard.append([InlineKeyboardButton(text="❌ Удалить пользователя", callback_data=f"delete_user_{client_name}")])
        if back_callback:
            keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)])
    else:
        keyboard.append([InlineKeyboardButton(text="💬 Связь с поддержкой", url="https://www.google.com/")])
        keyboard.append([InlineKeyboardButton(text="ℹ️ Как пользоваться", url="=https://www.google.com/")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



@dp.callback_query(lambda c: c.data.startswith("delete_user_"))
async def delete_user_from_user_menu(callback: types.CallbackQuery, state: FSMContext):
    client_name = callback.data.split("_", 2)[-1]
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_{client_name}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"manage_user_{client_name}")]
        ]
    )
    await callback.message.edit_text(
        f"Удалить пользователя <b>{client_name}</b>?",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await callback.answer()



#Удаление пользователя
@dp.message(RenameProfile.waiting_for_new_name)
async def handle_new_username(message: types.Message, state: FSMContext):
    new_username = message.text.strip()
    data = await state.get_data()
    old_username = data.get("old_username")

    # Проверка нового имени
    if not re.match(r"^[a-zA-Z0-9_-]{1,32}$", new_username):
        await message.answer("❌ Некорректное имя! Используй только буквы, цифры, _ и -.")
        await state.clear()
        return

    # Получить user_id по старому имени
    user_id = None
    conn = sqlite3.connect("/root/vpn.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE profile_name=?", (old_username,))
    res = cur.fetchone()
    if res:
        user_id = res[0]
    conn.close()
    if not user_id:
        await message.answer("❌ Пользователь по старому имени не найден!")
        await state.clear()
        return

    # Узнаём сколько дней осталось у старого сертификата
    old_cert_path = f"/etc/openvpn/easyrsa3/pki/issued/{old_username}.crt"
    days_left = get_cert_expiry_days(old_cert_path)

    # Удаляем старый сертификат
    result_del = await execute_script("2", old_username)
    if result_del["returncode"] != 0:
        stderr = result_del.get("stderr", "")
        await message.answer(f"❌ Ошибка удаления старого профиля: {stderr}")
        await state.clear()
        return

    # Создаём новый сертификат
    result_add = await execute_script("1", new_username, str(days_left))
    if result_add["returncode"] != 0:
        await message.answer(f"❌ Ошибка создания нового профиля: {result_add['stderr']}")
        await state.clear()
        return

    # Универсально обновляем имя в базе
    save_profile_name(user_id, new_username)

    await delete_last_menus(message.from_user.id)
    await show_menu(
        message.from_user.id,
        "✅ Имя профиля успешно изменено!\n\nТеперь вы можете скачать новый конфиг через меню кнопкой 📥 <b>Получить конфиг OpenVPN</b>.",
        create_user_menu(new_username, back_callback="users_menu", is_admin=(message.from_user.id == ADMIN_ID))
    )
    await state.clear()









def get_cert_expiry_days_for_user(client_name):
    cert_path = f"/etc/openvpn/client/keys/{client_name}.crt"
    return get_cert_expiry_days(cert_path)

async def get_config_stats(client_name):
    days_left = get_cert_expiry_days_for_user(client_name)
    now = datetime.now()
    date_from = now
    date_to = now + timedelta(days=days_left)
    return {
        "date_from": date_from.strftime("%d.%m.%Y"),
        "date_to": date_to.strftime("%d.%m.%Y"),
        "days_left": days_left
    }

#Статистика пользователя
@dp.callback_query(lambda c: c.data.startswith("user_stats_"))
async def user_stats(callback: types.CallbackQuery):
    client_name = callback.data[len("user_stats_"):]
    user_id = callback.from_user.id

    # Собираем блок с информацией о сертификате
    cert_info = get_cert_expiry_info(client_name)
    if cert_info:
        date_from_str = cert_info["date_from"].strftime('%d.%m.%Y')
        date_to_str   = cert_info["date_to"].strftime('%d.%m.%Y')
        days_left     = cert_info["days_left"]
        cert_block = (
            f"<b>Срок действия:</b>\n"
            f"• С {date_from_str} по {date_to_str}\n"
            f"• Осталось <b>{days_left}</b> дней\n"
        )
    else:
        cert_block = "<b>Срок действия:</b> неизвестно\n"
    text = cert_block

    # 1) Удаляем текущее сообщение (например, окно «Выберите тип» или старый stats-экран)
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # 2) Показываем новое «Меню управления клиентом» через show_menu():
    if user_id == ADMIN_ID:
        # Админу — с кнопкой «⬅️ Назад» к списку пользователей
        await show_menu(
            user_id,
            text,
            create_user_menu(client_name, back_callback="users_menu", is_admin=True)
        )
    else:
        # Обычному юзеру — без кнопки «Назад»
        await show_menu(
            user_id,
            text,
            create_user_menu(client_name, is_admin=False)
        )

    await callback.answer()






async def execute_script(option: str, client_name: str = None, days: str = None):
    script_path = "/root/antizapret/client.sh"
    if not os.path.exists(script_path):
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"❌ Файл {script_path} не найден!",
        }
    command = f"{script_path} {option}"
    if option not in ["8", "7"] and client_name:
        command += f" {client_name}"
        if days and option == "1" or option == "9":
            command += f" {days}"
    try:
        env = os.environ.copy()
        env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        # Добавь эти строки для дебага!
        print("==[DEBUG EXEC]==")
        print("COMMAND:", command)
        print("RET:", process.returncode)
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        print("==[END DEBUG]==")
        return {
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"❌ Ошибка при выполнении скрипта: {str(e)}",
        }


async def send_single_config(chat_id: int, path: str, caption: str):
    if os.path.exists(path):
        await bot.send_document(
            chat_id, document=FSInputFile(path), caption=f"🔐 {caption}"
        )
        return True
    return False


#Кто онлайн
def get_online_users_from_log():
    log_files = [
        "/etc/openvpn/server/logs/antizapret-tcp-status.log",
        "/etc/openvpn/server/logs/antizapret-udp-status.log",
        "/etc/openvpn/server/logs/vpn-tcp-status.log",
        "/etc/openvpn/server/logs/vpn-udp-status.log",
    ]
    users = set()
    for log_path in log_files:
        print(f"Читаю лог: {log_path}")  # Для отладки
        try:
            if os.path.exists(log_path):
                with open(log_path) as f:
                    for line in f:
                        print(line.strip())  # Для отладки
                        if line.startswith("CLIENT_LIST"):
                            parts = line.strip().split(",")
                            if len(parts) > 1:
                                users.add(parts[1])
        except Exception as e:
            print(f"Ошибка чтения лога {log_path}: {e}")
    print(f"Обнаружены пользователи: {users}")  # Для отладки
    return sorted(users)

#Кто онлайн
@dp.callback_query(lambda c: c.data == "who_online")
async def who_online(callback: types.CallbackQuery):
    online = get_online_users_from_log()
    if online:
        try:
            await callback.message.delete()
        except:
            pass

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=f"• {u}", callback_data=f"manage_online_{u}")]
                for u in online
            ] + [[types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]]
        )
        msg = "🟢 <b>Кто в сети:</b>\n\nНажми на клиента для управления:"
        await bot.send_message(callback.from_user.id, msg, reply_markup=keyboard, parse_mode="HTML")
    else:
        try:
            await callback.message.delete()
        except:
            pass
        await bot.send_message(callback.from_user.id, "❌ Сейчас нет никого онлайн", reply_markup=create_main_menu())
    await callback.answer()




@dp.callback_query(lambda c: c.data.startswith("manage_online_"))
async def manage_online_user(callback: types.CallbackQuery):
    client_name = callback.data[len("manage_online_"):]
    user_id = callback.from_user.id

    # Удаляем все старые меню
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Везде используем единый create_user_menu, но с back_callback="who_online"
    await show_menu(
        user_id,
        f"Управление клиентом <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="who_online", is_admin=(user_id == ADMIN_ID))
    )
    await callback.answer()





@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await delete_last_menus(user_id)  # ← в самом начале

    # Удаляем ВСЕ последние свои меню (N штук)
    for mid in get_last_menu_ids(user_id):
        try:
            await bot.delete_message(user_id, mid)
        except Exception:
            pass

    # Дальше как обычно:
    if user_id == ADMIN_ID:
        info = get_server_info()
        msg = await message.answer(
            info + "\n<b>Главное меню администратора:</b>",
            reply_markup=create_main_menu(),
            parse_mode="HTML"
        )
        set_last_menu_id(user_id, msg.message_id)
        await state.set_state(VPNSetup.choosing_option)
        return

    if is_approved_user(user_id):
        save_user_id(user_id)
        client_name = get_profile_name(user_id)
        if not await client_exists("openvpn", client_name):
            result = await execute_script("1", client_name, "30")
            if result["returncode"] != 0:
                msg = await message.answer("❌ Ошибка при регистрации клиента. Свяжитесь с администратором.")
                set_last_menu_id(user_id, msg.message_id)
                return
        msg = await message.answer(
            f"Привет, <b>твой VPN-аккаунт активирован!</b>\n\n"
            "Выбери действие ниже:",
            reply_markup=create_user_menu(client_name, user_id=user_id)
        )
        set_last_menu_id(user_id, msg.message_id)
        return

    if is_pending(user_id):
        msg = await message.answer("Ваша заявка на доступ уже на рассмотрении.")
        set_last_menu_id(user_id, msg.message_id)
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Отправить заявку на доступ", callback_data="send_request")]
    ])
    msg = await message.answer(
        "У вас нет доступа к VPN. Чтобы получить доступ — отправьте заявку на одобрение администратором:", reply_markup=markup)
    set_last_menu_id(user_id, msg.message_id)





@dp.callback_query(lambda c: c.data == "send_request")
async def send_request(callback: types.CallbackQuery):
    print("[SEND_REQUEST] send_request вызван")
    user_id = callback.from_user.id
    if is_pending(user_id):
        await callback.answer("Ваша заявка уже на рассмотрении", show_alert=True)
        return
    add_pending(user_id, callback.from_user.username, callback.from_user.full_name)
    # Шлём админу уведомление с кнопками — принять/отклонить/принять с изменением имени
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="✏️ Одобрить с изменением имени", callback_data=f"approve_rename_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")]
    ])
    print(f"[DEBUG] Отправляю заявку админу {ADMIN_ID}")
    print(f"[DEBUG] markup: {markup}")
    print(f"[DEBUG] text: {f'🔔 <b>Новая заявка:</b>...'}")

    await safe_send_message(
        ADMIN_ID,
        f"🔔 <b>Новая заявка:</b>\nID: <code>{user_id}</code>\nUsername: @{callback.from_user.username or '-'}\nИмя: {callback.from_user.full_name or '-'}",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await callback.message.edit_text("Заявка отправлена, ждите одобрения администратора.")
    await callback.answer("Заявка отправлена!", show_alert=True)






@dp.callback_query(lambda c: c.data == "add_del_menu")
async def add_del_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await show_menu(
        user_id,
        "Выберите действие:",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user")],
            [InlineKeyboardButton(text="➖ Удалить пользователя", callback_data="del_user")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
        ])
    )
    await callback.answer()







async def client_exists(vpn_type: str, client_name: str) -> bool:
    clients = await get_clients(vpn_type)
    return client_name in clients


@dp.callback_query(lambda c: c.data == "main_menu")
async def handle_main_menu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Удаляем всё что есть у юзера
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.clear()
    stats = get_server_info()
    await show_menu(
        user_id,
        stats + "\n<b>Главное меню:</b>",
        create_main_menu()
    )
    await callback.answer()







# 2) Обработчик «Получить VLESS» — учитываем контекст: обычный юзер или админ
@dp.callback_query(lambda c: c.data.startswith("get_vless_"))
async def send_vless_link(callback: types.CallbackQuery):
    client_name = callback.data.split("_", 2)[-1]
    user_id = callback.from_user.id

    # Удаляем всё предыдущие меню
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    vless_link = (
        "ТУТ ВАША VLESS в кавычках главное чтоб была ссылка на VLESS"
    )

    # Текст инструкции с «крупными» заголовками и смайлами
    text = (
        f"🔐 <b>Ссылка для подключения VLESS:</b>\n\n"
        f"<code>{vless_link}</code>\n\n"
        f"<b>📱 🤖 ANDROID:</b>\n"
        f"• <a href=\"https://play.google.com/store/apps/details?id=com.v2ray.ang\">v2rayNG</a>  \n"
        f"  • Установка из Google Play → Открыть → «+» → «Вставить URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"• <a href=\"https://github.com/NeKoStudio/NeKoBox/releases\">NekoBox</a>  \n"
        f"  • Скачайте APK с GitHub Releases → Установите → Запустите → «Добавить» → «URL-профиль» → Вставить ссылку → Сохранить → «▶».  \n\n"
        f"• <a href=\"https://github.com/yanue/v2ray-tun/releases\">v2RayTun</a>  \n"
        f"  • Скачайте APK с GitHub Releases → Установите → «Конфигурации» → «Добавить» → «Из буфера» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"<b>📱 🍎 iOS:</b>\n"
        f"• <a href=\"https://apps.apple.com/app/streisand/id1480384826\">Streisand</a>  \n"
        f"  • Установка из App Store → Открыть → «Конфигурации» → «Добавить профиль по ссылке» → Вставить ссылку → Сохранить → «Connect».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/foxray-pro-v2ray-vpn/id1524976027\">FoXray</a>  \n"
        f"  • App Store → Установить → «+» → «Вставить URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/shadowrocket/id932747118\">Shadowrocket</a>  \n"
        f"  • App Store (платно) → «Профили» → «+» → «Добавить вручную» → «URL» → Вставить ссылку → Сохранить → Включить.  \n\n"
        f"• <a href=\"https://apps.apple.com/app/v2box-v2ray-client/id1509268488\">V2Box – V2ray Client</a>  \n"
        f"  • App Store → «Профиль» → «Добавить» → «Добавить из URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/v2raytun-app/id1601032123\">v2RayTun</a>  \n"
        f"  • App Store → Установить → «Конфигурации» → «Импортировать URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"<b>💻 🪟 WINDOWS:</b>\n"
        f"• <a href=\"https://github.com/V2rayXS/Furious/releases\">Furious</a>  \n"
        f"  • Скачайте .exe с GitHub Releases → Установите → «Profiles» → «Import URL» → Вставить ссылку → Сохранить → «Connect».  \n\n"
        f"• <a href=\"https://github.com/AloneGuid/InvisibleMan-XRayClient/releases\">InvisibleMan-XRayClient</a>  \n"
        f"  • Скачайте .zip → Распакуйте → Запустите .exe → «+» → «Import from URL» → Вставить ссылку → Сохранить → «▶».  \n\n"
        f"• <a href=\"https://github.com/Nekoray/Nekoray/releases\">Nekoray</a>  \n"
        f"  • Скачайте portable-версию .zip → Распакуйте → Запустите Nekoray.exe → «Profiles» → «Import URL» → Вставить ссылку → Сохранить → «Start».  \n\n"
        f"<b>💻 🍏 macOS:</b>\n"
        f"• <a href=\"https://apps.apple.com/app/v2box-v2ray-client/id1509268488\">V2Box – V2ray Client</a>  \n"
        f"  • App Store → Установить → «Профили» → «+» → «Добавить URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/foxray-pro-v2ray-vpn/id1524976027\">FoXray</a>  \n"
        f"  • Как на iOS: App Store → «+» → «Вставить URL» → Вставить ссылку → Сохранить → «Подключить».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/streisand/id1480384826\">Streisand</a>  \n"
        f"  • App Store → «Добавить конфигурацию по URL» → Вставить ссылку → Сохранить → «Connect».  \n\n"
        f"• <a href=\"https://apps.apple.com/app/v2rayxs/id1522326938\">V2RayXS</a>  \n"
        f"  • App Store → Установить → «Import» → «From URL» → Вставить ссылку → Сохранить → «Start».  \n\n"
        f"• <a href=\"https://github.com/NeKoray/NekoRay/releases\">NekoRay/NekoBox for macOS</a>  \n"
        f"  • Скачайте .dmg с GitHub Releases → Установите → Откройте → «+» → «Import URL» → Вставить ссылку → Сохранить → «Start».  \n\n"
        f"• <a href=\"https://github.com/V2rayXS/Furious/releases\">Furious</a>  \n"
        f"  • Скачайте .dmg → Установите → Запустите Furious.app → «Profiles» → «Import URL» → Вставить ссылку → «Connect».  \n"
    )

    # Кнопка «⬅️ Назад» для возврата в меню управления данного пользователя
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_user_menu_{client_name}")]
        ]
    )

    await bot.send_message(
        user_id,
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )
    await callback.answer()



@dp.callback_query(lambda c: c.data.startswith("back_to_user_menu_"))
async def back_to_user_menu(callback: types.CallbackQuery):
    client_name = callback.data[len("back_to_user_menu_"):]
    user_id = callback.from_user.id

    # Удаляем всё, что там было
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Возвращаемся в меню управления клиентом
    await show_menu(
        user_id,
        f"Управление клиентом <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID))
    )
    await callback.answer()


    

@dp.callback_query(lambda c: c.data.startswith("cancel_openvpn_") or c.data == "select_openvpn_back")
async def back_from_openvpn(callback: types.CallbackQuery, state: FSMContext):
    # Разбираем callback.data:
    # если data = "cancel_openvpn_config_<client_name>"
    if callback.data.startswith("cancel_openvpn_config_"):
        client_name = callback.data[len("cancel_openvpn_config_"):]
    # (редкий случай) если data = "cancel_openvpn_<client_name>"
    elif callback.data.startswith("cancel_openvpn_"):
        client_name = callback.data[len("cancel_openvpn_"):]
    else:
        # Вариант "select_openvpn_back"
        data = await state.get_data()
        client_name = data.get("client_name")
        if not client_name:
            stats = get_server_info()
            await show_menu(callback.from_user.id, stats + "\n<b>Главное меню:</b>", create_main_menu())
            await callback.answer()
            return

    user_id = callback.from_user.id

    # Удаляем текущее меню
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Возвращаемся в меню управления этим клиентом (заголовок без "config_")
    await show_menu(
        user_id,
        f"Управление клиентом <b>{client_name}</b>:",
        create_user_menu(client_name, back_callback="users_menu", is_admin=(user_id == ADMIN_ID))
    )
    await state.clear()
    await callback.answer()

 


@dp.callback_query(lambda c: c.data.startswith("client_"))
async def handle_client_selection(callback: types.CallbackQuery, state: FSMContext):
    _, vpn_type, client_name = callback.data.split("_", 2)
    await state.update_data(client_name=client_name, vpn_type=vpn_type)

    if vpn_type == "openvpn":
        await callback.message.delete()
        await bot.send_message(
            callback.from_user.id,
            "Выберите тип конфигурации OpenVPN:",
            reply_markup=create_openvpn_config_menu(client_name),
        )
        await state.set_state(VPNSetup.choosing_config_type)
    else:
        await callback.message.delete()
        await bot.send_message(
            callback.from_user.id,
            "Выберите тип конфигурации WireGuard:",
            reply_markup=create_wireguard_config_menu(client_name),
        )
        await state.set_state(VPNSetup.choosing_config_type)
        await callback.answer()

@dp.callback_query(lambda c: c.data == "openvpn_menu")
async def openvpn_menu(callback: types.CallbackQuery):
    await switch_menu(callback, "Меню OpenVPN:", reply_markup=create_openvpn_menu())
    await callback.answer()


@dp.callback_query(VPNSetup.choosing_config_type)
async def handle_interface_selection(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    client_name = user_data["client_name"]
    vpn_type = user_data["vpn_type"]
    user_id = callback.from_user.id

    # Обработка клавиши «⬅️ Назад» (в create_openvpn_config_menu прописан callback "cancel_openvpn_<client_name>")
    if callback.data == f"cancel_openvpn_config_{client_name}" or callback.data == f"cancel_openvpn_{client_name}":
        # Удаляем этот экран
        await delete_last_menus(user_id)
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Возвращаемся в меню управления клиентом
        if user_id == ADMIN_ID:
            await show_menu(
                user_id,
                f"Управление клиентом <b>{client_name}</b>:",
                create_user_menu(client_name, back_callback="users_menu", is_admin=True)
            )
        else:
            await show_menu(
                user_id,
                f"Меню пользователя <b>{client_name}</b>:",
                create_user_menu(client_name, is_admin=False)
            )
        await state.clear()
        await callback.answer()
        return


@dp.callback_query(VPNSetup.choosing_protocol)
async def handle_protocol_selection(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    client_name = user_data["client_name"]

    if callback.data.startswith("send_ovpn_"):
        _, _, interface, proto, _ = callback.data.split("_", 4)
        name_core = client_name.replace("antizapret-", "").replace("vpn-", "")

        if proto == "default":
            dir_path = f"/root/antizapret/client/openvpn/{interface}/"
        else:
            dir_path = f"/root/antizapret/client/openvpn/{interface}-{proto}/"

        matched_file = None
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                # Исправлено: ищем по вхождению name_core, не по паттерну!
                if name_core in file and file.endswith(".ovpn"):
                    matched_file = os.path.join(dir_path, file)
                    break

        if matched_file and await send_single_config(
            callback.from_user.id, matched_file, os.path.basename(matched_file)
        ):
            await callback.message.delete()
            await callback.message.answer(
                "Главное меню:", reply_markup=create_main_menu()
            )
            await state.clear()
        else:
            await callback.answer("❌ Файл не найден", show_alert=True)

    elif callback.data.startswith("back_to_interface_"):
        await handle_back_to_interface(callback, state)


async def handle_wg_type_selection(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    client_name = user_data["client_name"]

    # Обработка кнопки "Назад"
    if callback.data.startswith("back_to_interface_"):
        await handle_back_to_interface(callback, state)
        await callback.answer()
        return

    if callback.data.startswith("send_wg_"):
        _, _, interface, wg_type, _ = callback.data.split("_", 4)

        name_core = client_name.replace("antizapret-", "").replace("vpn-", "")
        dir_path = f"/root/antizapret/client/{'wireguard' if wg_type == 'wg' else 'amneziawg'}/{interface}/"

        matched_file = None
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                # Исправлено: ищем по вхождению name_core и типу wg/am, не по паттерну!
                if name_core in file and wg_type in file and file.endswith(".conf"):
                    matched_file = os.path.join(dir_path, file)
                    break

        if not matched_file:
            await callback.answer("❌ Файл конфигурации не найден", show_alert=True)
            await state.clear()
            return

        await state.update_data(
            {
                "file_path": matched_file,
                "original_name": os.path.basename(matched_file),
                "short_name": f"{name_core}-{wg_type}.conf",
            }
        )

        await callback.message.edit_text(
            "Android может не принимать файлы с длинными именами.\nХотите переименовать файл при отправке?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Да", callback_data="confirm_rename"),
                        InlineKeyboardButton(text="❌ Нет", callback_data="no_rename"),
                    ]
                ]
            ),
        )
        await state.set_state(VPNSetup.confirming_rename)


@dp.callback_query(VPNSetup.confirming_rename)
async def handle_rename_confirmation(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    file_path = user_data["file_path"]

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        await callback.answer("❌ Файл не найден", show_alert=True)
        await state.clear()
        return

    # Проверяем размер файла (не пустой и не слишком большой)
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        print(f"Файл пуст: {file_path}")
        await callback.answer("❌ Файл пуст", show_alert=True)
        await state.clear()
        return

    if file_size > 50 * 1024 * 1024:  # 50MB
        print(f"Файл слишком большой: {file_path} ({file_size} байт)")
        await callback.answer(
            "❌ Файл слишком большой для отправки в Telegram", show_alert=True
        )
        await state.clear()
        return

    try:
        if callback.data == "confirm_rename":
            file = FSInputFile(file_path, filename=user_data["short_name"])
            caption = f"🔐 {user_data['short_name']}"
        else:
            file = FSInputFile(file_path)
            caption = f"🔐 {user_data['original_name']}"

        await bot.send_document(
            chat_id=callback.from_user.id, document=file, caption=caption
        )

        await callback.message.delete()
        await callback.message.answer("Главное меню:", reply_markup=create_main_menu())

    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        await callback.answer("❌ Ошибка при отправке файла", show_alert=True)

    await state.clear()


async def handle_back_to_interface(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    client_name = user_data["client_name"]
    vpn_type = user_data["vpn_type"]

    if vpn_type == "openvpn":
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_message(
            callback.from_user.id,
            "Выберите тип конфигурации OpenVPN:",
            reply_markup=create_openvpn_config_menu(client_name),
        )
        await state.set_state(VPNSetup.choosing_config_type)
    else:
        await callback.message.edit_text(
            "Выберите тип конфигурации WireGuard:",
            reply_markup=create_wireguard_config_menu(client_name),
        )
        await state.set_state(VPNSetup.choosing_config_type)
    await callback.answer()



@dp.callback_query(lambda c: c.data.startswith("cancel_config_"))
async def handle_config_cancel(callback: types.CallbackQuery, state: FSMContext):
    client_name = callback.data.split("_")[-1]
    user_data = await state.get_data()
    vpn_type = user_data["vpn_type"]

    clients = await get_clients(vpn_type)
    total_pages = (len(clients) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    await callback.message.edit_text(
        "Список клиентов:",
        reply_markup=create_client_list_keyboard(
            clients, 1, total_pages, vpn_type, "list"
        ),
    )
    await state.clear()
    await callback.answer()

@dp.message(Command("announce"))
async def announce_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "⛔ Нет доступа!")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await bot.send_message(message.chat.id, "Напиши текст для рассылки после /announce!")
        return

    text = parts[1]
    sent, failed = await announce_all(text)
    await bot.send_message(message.chat.id, f"✅ Отправлено: {sent}, не доставлено: {failed}")



async def cleanup_openvpn_files(client_name: str):
    """Дополнительная очистка файлов OpenVPN после основного скрипта"""
    # Получаем имя файла без префиксов
    clean_name = client_name.replace("antizapret-", "").replace("vpn-", "")

    # Директории для проверки
    dirs_to_check = [
        "/root/antizapret/client/openvpn/antizapret/",
        "/root/antizapret/client/openvpn/antizapret-tcp/",
        "/root/antizapret/client/openvpn/antizapret-udp/",
        "/root/antizapret/client/openvpn/vpn/",
        "/root/antizapret/client/openvpn/vpn-tcp/",
        "/root/antizapret/client/openvpn/vpn-udp/",
    ]

    deleted_files = []

    for dir_path in dirs_to_check:
        if not os.path.exists(dir_path):
            continue

        for filename in os.listdir(dir_path):
            # Удаляем все файлы, содержащие имя клиента
            if clean_name in filename:
                try:
                    file_path = os.path.join(dir_path, filename)
                    os.remove(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"Ошибка удаления {file_path}: {e}")

    return deleted_files

@dp.callback_query(lambda c: c.data.startswith("select_openvpn_"))
async def select_openvpn_config(callback: types.CallbackQuery):
    client_name = callback.data.split("_")[-1]

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обычный VPN", callback_data=f"download_openvpn_vpn_{client_name}")],
        [InlineKeyboardButton(text="Antizapret (Рекомендуется)", callback_data=f"download_openvpn_antizapret_{client_name}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_user_menu_{client_name}")]
    ])

    # Удаляем предыдущие меню
    await delete_last_menus(callback.from_user.id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Добавляем ссылку на инструкцию перед кнопками
    text = (
        "Выберите тип конфигурации OpenVPN:\n\n"
        "📖 <a href=\"https://www.google.com/\">Инструкция по подключению для 🍎Apple, 🤖Android и 🖥PC</a>"
    )

    await bot.send_message(
        callback.from_user.id,
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=markup
    )
    await callback.answer()



def get_openvpn_filename(client_name, config_type):
    if config_type == "vpn":
        return f"${FILEVPN_NAME} - Обычный VPN - {client_name}.ovpn"
    elif config_type == "antizapret":
        return f"${FILEVPN_NAME} - {client_name}.ovpn"


# Вывод конфига для OpenVPN
@dp.callback_query(lambda c: c.data.startswith("download_openvpn_"))
async def download_openvpn_config(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    _, _, config_type, client_name = parts
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"

    # Удаляем прошлые inline-сообщения
    await delete_last_menus(user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Определяем пути
    if config_type == "vpn":
        file_name = f"${FILEVPN_NAME} - Обычный VPN - {client_name}.ovpn"
        base_path = "/root/antizapret/client/openvpn/vpn/"
    else:
        file_name = f"${FILEVPN_NAME} - {client_name}.ovpn"
        base_path = "/root/antizapret/client/openvpn/antizapret/"

    file_path = os.path.join(base_path, file_name)

    if os.path.exists(file_path):
        await bot.send_document(
            user_id,
            FSInputFile(file_path),
            caption=f"🔐 {os.path.basename(file_path)}"
        )
        await callback.answer("✅ Конфигурация отправлена.")

        # Уведомление админу
        await notify_admin_download(user_id, username, os.path.basename(file_path), "ovpn")

        # Кнопка назад
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cancel_openvpn_config_{client_name}")]
        ])
        await show_menu(user_id, "Вернуться к выбору типа конфига:", markup)
    else:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cancel_openvpn_config_{client_name}")]
        ])
        files_list = os.listdir(base_path) if os.path.exists(base_path) else []
        await show_menu(
            user_id,
            f"❌ Не найден файл {file_name} в папке {base_path}\n"
            f"Файлы в папке: {files_list}",
            markup
        )
        await callback.answer("❌ Файл конфигурации не найден.", show_alert=True)





@dp.message(VPNSetup.entering_client_name)
async def handle_client_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Удаляем сообщение "Введите имя нового пользователя:"
    msg_id = data.get("add_user_msg_id")
    if msg_id:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except Exception:
            pass

    # --- Вот здесь if, с правильным отступом ---
    if message.text == "❌ Отмена":
        await state.clear()
        await delete_last_menus(message.from_user.id)  # ← сразу после clear!
        stats = get_server_info()
        await show_menu(message.from_user.id, stats + "\n<b>Главное меню:</b>", create_main_menu())
        return

    client_name = message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{1,32}$", client_name):
        await message.answer("❌ Некорректное имя! Используйте буквы, цифры, _ и -", reply_markup=cancel_markup)
        return

    data = await state.get_data()

    # --- 1. Это создание профиля по заявке от админа
    if "approve_user_id" in data:
        user_id = data["approve_user_id"]
        result = await execute_script("1", client_name, "30")
        if result["returncode"] == 0:
            save_profile_name(user_id, client_name)
            remove_pending(user_id)
            await safe_send_message(
                user_id,
                f"✅ Ваша заявка одобрена!\n"
                f"Имя профиля: <b>{client_name}</b>\n"
                "Теперь вам доступны функции VPN.",
                parse_mode="HTML",
                reply_markup=create_user_menu(client_name)
            )
            await show_menu(message.from_user.id, "Пользователь активирован и уведомлен!", create_main_menu())
        else:
            await message.answer(f"❌ Ошибка: {result['stderr']}")
        await state.clear()
        return

    # --- 2. Обычное добавление/удаление пользователя через меню
    option = data.get("action")
    if option == "1":
        result = await execute_script("1", client_name, "30")
        if result["returncode"] == 0:
            msg = await message.answer("✅ Клиент создан на 30 дней!", reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            try:
                await msg.delete()
            except Exception:
                pass
            stats = get_server_info()
            await show_menu(message.from_user.id, stats + "\n<b>Главное меню:</b>", create_main_menu())
        else:
            await message.answer(f"❌ Ошибка: {result['stderr']}", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    elif option == "2":
        result = await execute_script(option, client_name)
        if result["returncode"] == 0:
            stats = get_server_info()
            await show_menu(message.from_user.id, stats + "\n<b>Главное меню:</b>", create_main_menu())
        else:
            await message.answer(f"❌ Ошибка: {result['stderr']}")
        await state.clear()
        return
    else:
        await message.answer("Ошибка: неизвестное действие")
        await state.clear()
        return




@dp.message(VPNSetup.deleting_client)
async def handle_delete_client(message: types.Message, state: FSMContext):
    """Обрабатывает запрос на удаление клиента в боте."""
    client_name = message.text.strip()
    data = await state.get_data()
    vpn_type = "openvpn" if data["action"] == "2" else "wireguard"

    await message.answer(
        f"Вы уверены, что хотите удалить клиента {client_name}?",
        reply_markup=create_confirmation_keyboard(client_name, vpn_type),
    )   
    await state.clear()


async def get_clients(vpn_type: str):
    option = "3" if vpn_type == "openvpn" else "6"
    result = await execute_script(option)

    if result["returncode"] == 0:
        # Фильтруем строки, убирая заголовки и пустые строки
        clients = [
            c.strip()
            for c in result["stdout"].split("\n")
            if c.strip()  # Убираем пустые строки
            and not c.startswith("OpenVPN client names:")  # Убираем заголовок OpenVPN
            and not c.startswith(
                "WireGuard/AmneziaWG client names:"
            )  # Убираем заголовок WireGuard
            and not c.startswith(
                "OpenVPN - List clients"
            )  # Убираем строку "OpenVPN - List clients"
            and not c.startswith(
                "WireGuard/AmneziaWG - List clients"
            )  # Убираем строку "WireGuard/AmneziaWG - List clients"
        ]
        return clients
    return []


async def send_config(chat_id: int, client_name: str, option: str) -> bool:
    try:
        files_found = []
        # Для WireGuard/AmneziaWG
        if option == "4":
            base_dir = "/root/antizapret/client/amneziawg/"
            ext = ".conf"
            prefix = f"amneziawg-{client_name}-"
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file.startswith(prefix) and file.endswith(ext):
                        files_found.append(os.path.join(root, file))
        # Для OpenVPN — ищем по обоим вариантам
        else:
            base_dir = "/root/antizapret/client/openvpn/"
            ext = ".ovpn"
            prefix_vpn = f"vpn-{client_name}-"
            prefix_antizapret = f"antizapret-{client_name}-"
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if (
                        (file.startswith(prefix_vpn) or file.startswith(prefix_antizapret))
                        and file.endswith(ext)
                    ):
                        files_found.append(os.path.join(root, file))

        for file_path in files_found:
            await bot.send_document(
                chat_id, FSInputFile(file_path), caption=f"🔐 {os.path.basename(file_path)}"
            )
        return bool(files_found)
    except Exception as e:
        print(f"Ошибка отправки конфигураций: {e}")
        return False


# Добавляем функцию send_backup здесь
async def send_backup(chat_id: int) -> bool:
    """Функция отправки резервной копии"""

    paths_to_check = [
        f"/root/antizapret/backup-{SERVER_IP}.tar.gz",
        "/root/antizapret/backup.tar.gz",
    ]

    for backup_path in paths_to_check:
        try:
            if os.path.exists(backup_path):
                await bot.send_document(
                    chat_id=chat_id,
                    document=FSInputFile(backup_path),
                    caption="📦 Бэкап клиентов",
                )
                return True
        except Exception as e:
            print(f"Ошибка отправки бэкапа ({backup_path}): {e}")
            return False

    return False  # Если ни один файл не найден

#@dp.callback_query()
async def handle_callback_query(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает нажатия на кнопки в Telegram боте и выполняет соответствующие действия."""
    data = callback.data
    user_id = callback.from_user.id

    try:
        if user_id != ADMIN_ID and user_id not in AUTHORIZED_USERS:
            await callback.answer("Доступ запрещен!")
            return

        # Пагинация
        if data.startswith("page_"):
            _, action, vpn_type, page = data.split("_", 3)
            page = int(page)
            clients = await get_clients(vpn_type)
            total_pages = (len(clients) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            await callback.message.edit_text(
                "Список клиентов:",
                reply_markup=create_client_list_keyboard(
                    clients, page, total_pages, vpn_type, action
                ),
            )
            await callback.answer()
            return

        # Обработка удаления (начальная кнопка удалить)
        if data.startswith("delete_"):
            _, vpn_type, client_name = data.split("_", 2)
            await callback.message.edit_text(
                f"❓ Удалить клиента {client_name} ({vpn_type})?",
                reply_markup=create_confirmation_keyboard(client_name, vpn_type),
            )
            await callback.answer()
            return

        # Обработка пагинации для удаления
        if data.startswith("page_delete_"):
            _, _, vpn_type, page = data.split("_")
            page = int(page)
            clients = await get_clients(vpn_type)
            total_pages = (len(clients) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

            await callback.message.edit_text(
                "Выберите клиента для удаления:",
                reply_markup=create_client_list_keyboard(
                    clients, page, total_pages, vpn_type, "delete"
                ),
            )
            await callback.answer()
            return

        # Инициализация удаления через главное меню (цифровые callback: 2 и 5)
        if data in ["2", "5"]:
            vpn_type = "openvpn" if data == "2" else "wireguard"
            clients = await get_clients(vpn_type)
            if not clients:
                await callback.message.edit_text("❌ Нет клиентов для удаления")
                await callback.answer()
                return
            total_pages = (len(clients) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            await callback.message.edit_text(
                "Выберите клиента для удаления:",
                reply_markup=create_client_list_keyboard(
                    clients, 1, total_pages, vpn_type, "delete"
                ),
            )
            await state.set_state(VPNSetup.list_for_delete)
            await callback.answer()
            return

        # Подтверждение удаления (confirm_openvpn_имя или confirm_wireguard_имя)
        if data.startswith("confirm_"):
            _, vpn_type, client_name = data.split("_", 2)
            option = "2" if vpn_type == "openvpn" else "5"
            try:
                result = await execute_script(option, client_name)
                # Дополнительная очистка для OpenVPN
                if vpn_type == "openvpn" and result["returncode"] == 0:
                    deleted_files = await cleanup_openvpn_files(client_name)
                    if deleted_files:
                        result["additional_deleted"] = deleted_files

                if result["returncode"] == 0:
                    msg = f"✅ Клиент {client_name} удален!"
                    if vpn_type == "openvpn" and result.get("additional_deleted"):
                        msg += f"\nДополнительно удалено файлов: {len(result['additional_deleted'])}"
                    await callback.message.edit_text(msg)
                    await callback.message.answer("Главное меню:", reply_markup=create_main_menu())
                else:
                    await callback.message.edit_text(f"❌ Ошибка: {result['stderr']}")
            except Exception as e:
                print(f"Ошибка при удалении клиента: {e}")
            finally:
                await callback.answer()
                await state.clear()
            return

        # Отмена удаления
        if data == "cancel_delete":
            await callback.message.edit_text("❌ Удаление отменено", reply_markup=create_main_menu())
            await callback.answer()
            return

        # Список клиентов (цифровые callback: 3 и 6)
        if data in ["3", "6"]:
            vpn_type = "openvpn" if data == "3" else "wireguard"
            clients = await get_clients(vpn_type)
            total_pages = (len(clients) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            await callback.message.edit_text(
                "Список клиентов:",
                reply_markup=create_client_list_keyboard(
                    clients, 1, total_pages, vpn_type, "list"
                ),
            )
            await callback.answer()
            return

        # Создание клиента (цифровые callback: 1 и 4)
        if data in ["1", "4"]:
            await state.update_data(action=1)
            await callback.message.edit_text("Введите имя нового клиента:")
            await state.set_state(VPNSetup.entering_client_name)
            await callback.answer()
            return

        # Пересоздание файлов
        if data == "7":
            await callback.message.edit_text("⏳ Идет пересоздание файлов...")
            result = await execute_script("7")
            if result["returncode"] == 0:
                await callback.message.edit_text("✅ Файлы успешно пересозданы!")
                await callback.message.answer("Главное меню:", reply_markup=create_main_menu())
            else:
                await callback.message.edit_text(f"❌ Ошибка: {result['stderr']}")
            await callback.answer()
            return

        # Создание бэкапа
        if data == "8":
            await callback.message.edit_text("⏳ Создаю бэкап...")
            result = await execute_script("8")
            if result["returncode"] == 0:
                if await send_backup(callback.from_user.id):
                    await callback.message.delete()
                    await callback.message.answer("Главное меню:", reply_markup=create_main_menu())
                else:
                    await callback.message.edit_text("❌ Не удалось отправить бэкап")
            else:
                await callback.message.edit_text(
                    f"❌ Ошибка при создании бэкапа: {result['stderr']}"
                )
            await callback.answer()
            return

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("⚠️ Произошла ошибка!")


async def notify_admin_download(user_id, username, file_name, vpn_type):
    vpn_emoji = "📥"
    vpn_text = {
        "wg": "WireGuard",
        "amnezia": "Amnezia",
        "ovpn": "OpenVPN"
    }
    text = (
        f"{vpn_emoji} Скачивание конфига\n"
        f"Пользователь: <code>{user_id}</code> (@{username})\n"
        f"Файл: {file_name}"
    )
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке уведомления админу: {e}")


@dp.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def process_application(callback: types.CallbackQuery, state: FSMContext):
    action, user_id = callback.data.split("_", 1)
    user_id = int(user_id)
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет прав!", show_alert=True)
        return

    if action == "approve":
        user_obj = await bot.get_chat(user_id)
        client_name = user_obj.username or f"user{user_id}"
        client_name = str(client_name)[:32]

        result = await execute_script("1", client_name, "30")
        if result["returncode"] == 0:
            save_profile_name(user_id, client_name)
            approve_user(user_id)
            remove_pending(user_id)
            save_user_id(user_id)  # <--- ДОБАВИТЬ В users.txt сразу!
            await safe_send_message(
                user_id,
                f"✅ Ваша заявка одобрена!\nИмя профиля: <b>{client_name}</b>\nТеперь вам доступны функции VPN.",
                parse_mode="HTML",
                reply_markup=create_user_menu(client_name)
            )
            stats = get_server_info()
            await show_menu(callback.from_user.id, stats + "\n<b>Главное меню:</b>", create_main_menu())
        else:
            await callback.message.edit_text(f"❌ Ошибка: {result['stderr']}")
        await callback.answer()
        return

    else:  # Отклонить
        remove_pending(user_id)
        await safe_send_message(user_id, "❌ Ваша заявка отклонена. Обратитесь к администратору.")
        await callback.message.edit_text("❌ Заявка отклонена.")
        await callback.answer()


# ==== Старт бота ====
async def main():
    print("✅ Бот успешно запущен!")
    # ... update_bot_description(), update_bot_about(), set_bot_commands()
    await dp.start_polling(bot)



async def notify_expiring_users():
    while True:
        try:
            # Пройдемся по всем одобренным пользователям
            if not os.path.exists(APPROVED_FILE):
                await asyncio.sleep(12 * 3600)
                continue

            with open(APPROVED_FILE, "r") as f:
                approved_users = [line.strip() for line in f if line.strip().isdigit()]

            for user_id in approved_users:
                user_id_int = int(user_id)
                client_name = get_profile_name(user_id_int)
                if not client_name:
                    continue

                cert_info = get_cert_expiry_info(client_name)
                if not cert_info:
                    continue

                days_left = cert_info.get("days_left", 0)
                notified_flag_file = f".notified_{user_id}.flag"
                if days_left == 5 and not os.path.exists(notified_flag_file):
                    # Уведомление юзеру
                    try:
                        await bot.send_message(
                            user_id_int,
                            "⚠️ <b>Где бабосы? Месяц прошёл почти)</b>\n\n"
                            "Осталось 5 дней до окончания действия VPN.",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                    # Уведомление админу
                    try:
                        await bot.send_message(
                            ADMIN_ID,
                            f"⚠️ Пользователю <code>{user_id}</code> отправлено напоминание о продлении:\n"
                            "<b>Где бабосы? Месяц прошёл почти)</b>",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Не удалось отправить уведомление админу: {e}")
                    # Ставим флаг, чтобы не слать повторно
                    with open(notified_flag_file, "w") as f:
                        f.write("notified")
                # Снимаем флаг, если продлил (например, осталось больше 5 дней)
                elif days_left > 5 and os.path.exists(notified_flag_file):
                    try:
                        os.remove(notified_flag_file)
                    except Exception:
                        pass

        except Exception as e:
            print(f"[notify_expiring_users] Ошибка: {e}")
        await asyncio.sleep(12 * 3600)  # Проверять 2 раза в сутки (можешь изменить)



if __name__ == "__main__":
    asyncio.run(main())
