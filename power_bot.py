import asyncio
import time
import os
import hashlib

from aiogram import Bot
from aiogram.types import FSInputFile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ADDRESSES = [
    {"city": "м.. Могилів-Подільський (Вінницька Область/М.Вінниця)", "street": "вулиця Коцюбинського", "house": "48"},
    {"city": "смт.. Чернівці (Чернівецький Район/Смт Чернівці)", "street": "вулиця Павлівська", "house": "37"},
]


def get_screenshot(city, street, house, filename):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,2200")

    driver = webdriver.Chrome(options=options)
    driver.get("https://voe.com.ua/disconnection/detailed")

    wait = WebDriverWait(driver, 20)

    city_input = wait.until(
        EC.presence_of_element_located((By.NAME, "city"))
    )

    street_input = wait.until(
        EC.presence_of_element_located((By.NAME, "street"))
    )

    house_input = wait.until(
        EC.presence_of_element_located((By.NAME, "house"))
    )

    # Очищаем поля
    city_input.clear()
    street_input.clear()
    house_input.clear()

    # Вводим данные
    city_input.send_keys(city)
    time.sleep(1)

    street_input.send_keys(street)
    time.sleep(1)

    house_input.send_keys(house)
    time.sleep(1)

    house_input.send_keys(Keys.RETURN)

    # Ждём загрузку результата
    time.sleep(6)

    driver.save_screenshot(filename)
    driver.quit()


def get_hash(filename):
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


async def main():
    bot = Bot(token=BOT_TOKEN)

    for i, address in enumerate(ADDRESSES):
        filename = f"result_{i}.png"
        hashfile = f"hash_{i}.txt"

        get_screenshot(address["city"], address["street"], address["house"], filename)

        new_hash = get_hash(filename)
        old_hash = None

        if os.path.exists(hashfile):
            with open(hashfile, "r") as f:
                old_hash = f.read()

        if new_hash != old_hash:
            photo = FSInputFile(filename)
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo,
                caption=f"⚡ Обновление графика\n📍 {address['city']} {address['street']} {address['house']}"
            )

            with open(hashfile, "w") as f:
                f.write(new_hash)

        os.remove(filename)

    await bot.session.close()


asyncio.run(main())
