import os
import requests
import hashlib
import asyncio
import imgkit

from aiogram import Bot
from aiogram.types import FSInputFile

# ========================
# Настройки Telegram
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ID девушки

# ========================
# Адреса для проверки
# ========================
ADDRESSES = [
    {"city": "смт. Чернівці (Чернівецький Район/Смт Чернівці)", "street": "вулиця Павлівська", "house": "37"},
    {"city": "м.. Могилів-Подільський (Вінницька Область/М.Вінниця)", "street": "вулиця Коцюбинського", "house": "48"},
]

# ========================
# Функция для получения HTML с сайта
# ========================
def get_data(city, street, house):
    url = "https://voe.com.ua/disconnection/detailed"
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }

    # GET-запрос для получения csrf_token и cookies
    r = session.get(url, headers=headers)

    if 'name="csrf_token"' not in r.text:
        print("Не удалось найти csrf_token. Возвращаем пустую страницу.")
        return "<html><body><h1>Ошибка получения данных</h1></body></html>"

    csrf_token = r.text.split('name="csrf_token" value="')[1].split('"')[0]

    # POST-запрос для получения таблицы графика
    payload = {
        "city": city,
        "street": street,
        "house": house,
        "csrf_token": csrf_token,
        "op": "Пошук"
    }

    resp = session.post(url, data=payload, headers=headers)
    return resp.text

# ========================
# Генерация скриншота HTML
# ========================
def html_to_image(html, filename):
    options = {
        "format": "png",
        "width": 1000,
        "encoding": "UTF-8",
    }
    imgkit.from_string(html, filename, options=options)

# ========================
# Вычисление hash для проверки изменений
# ========================
def get_hash(filename):
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# ========================
# Главная асинхронная функция
# ========================
async def main():
    bot = Bot(token=BOT_TOKEN)

    for i, addr in enumerate(ADDRESSES):
        filename = f"result_{i}.png"
        hashfile = f"hash_{i}.txt"

        html = get_data(addr["city"], addr["street"], addr["house"])
        html_to_image(html, filename)
        new_hash = get_hash(filename)

        old_hash = None
        if os.path.exists(hashfile):
            with open(hashfile, "r") as f:
                old_hash = f.read()

        # Отправка в Telegram только если график изменился
        if new_hash != old_hash:
            photo = FSInputFile(filename)
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo,
                caption=f"⚡ Обновление графика\n📍 {addr['city']} {addr['street']} {addr['house']}"
            )
            with open(hashfile, "w") as f:
                f.write(new_hash)

        # Удаляем скриншот, чтобы не засорять репозиторий
        os.remove(filename)

    await bot.session.close()

# ========================
# Запуск
# ========================
if __name__ == "__main__":
    asyncio.run(main())
