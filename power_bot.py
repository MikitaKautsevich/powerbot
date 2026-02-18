import os
import requests
import hashlib
import asyncio
import imgkit

from aiogram import Bot
from aiogram.types import FSInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ID девушки

# Адреса для проверки
ADDRESSES = [
    {"city": "смт. Чернівці (Чернівецький Район/Смт Чернівці)", "street": "вулиця Павлівська", "house": "37"},
    {"city": "м.. Могилів-Подільський (Вінницька Область/М.Вінниця)", "street": "вулиця Коцюбинського", "house": "48"},
]

# Функция для получения данных графика с сайта
def get_data(city, street, house):
    url = "https://voe.com.ua/disconnection/detailed"
    session = requests.Session()

    # Получаем csrf-token и cookies
    r = session.get(url)
    csrf_token = r.text.split('name="csrf_token" value="')[1].split('"')[0]

    # Отправляем POST-запрос
    payload = {
        "city": city,
        "street": street,
        "house": house,
        "csrf_token": csrf_token,
        "op": "Пошук"
    }
    headers = {"Referer": url}
    resp = session.post(url, data=payload, headers=headers)
    return resp.text  # возвращаем HTML с таблицей графика

# Функция для генерации скриншота таблицы через imgkit
def html_to_image(html, filename):
    options = {
        "format": "png",
        "width": 1000,
        "encoding": "UTF-8",
    }
    imgkit.from_string(html, filename, options=options)

# Функция для вычисления hash
def get_hash(filename):
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# Главная асинхронная функция
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

        # Если изменилось — отправляем в Telegram
        if new_hash != old_hash:
            photo = FSInputFile(filename)
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo,
                caption=f"⚡ Обновление графика\n📍 {addr['city']} {addr['street']} {addr['house']}"
            )
            with open(hashfile, "w") as f:
                f.write(new_hash)

        os.remove(filename)

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

