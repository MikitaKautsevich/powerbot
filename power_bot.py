import os
import time
import hashlib
import asyncio

from aiogram import Bot
from aiogram.types import FSInputFile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ========================
# Настройки Telegram
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ID девушки

# ========================
# Адреса для проверки
# ========================
ADDRESSES = [
    {"city": "смт. Чернівець (Чернівецький Район/Смт Чернівці)", "street": "вулиця Павлівська", "house": "37"},
    {"city": "м.. Могилів-Подільський (Вінницька Область/М.Вінниця)", "street": "вулиця Коцюбинського", "house": "48"},
]

# ========================
# Функция для скриншота страницы с графиком
# ========================
def get_screenshot(city, street, house, filename):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,2200")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://voe.com.ua/disconnection/detailed")

    wait = WebDriverWait(driver, 120)  # увеличили таймаут до 120 секунд

    # Ждём форму целиком
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#disconnection-detailed-form")))
    form = driver.find_element(By.CSS_SELECTOR, "form#disconnection-detailed-form")

    # Находим поля внутри формы
    city_input = form.find_element(By.CSS_SELECTOR, "input[data-drupal-selector='edit-city']")
    street_input = form.find_element(By.CSS_SELECTOR, "input[data-drupal-selector='edit-street']")
    house_input = form.find_element(By.CSS_SELECTOR, "input[data-drupal-selector='edit-house']")

    # Вводим данные с небольшими паузами
    city_input.clear()
    city_input.send_keys(city)
    time.sleep(2)
    city_input.send_keys(Keys.ARROW_DOWN)
    city_input.send_keys(Keys.RETURN)

    street_input.clear()
    street_input.send_keys(street)
    time.sleep(2)
    street_input.send_keys(Keys.ARROW_DOWN)
    street_input.send_keys(Keys.RETURN)

    house_input.clear()
    house_input.send_keys(house)
    time.sleep(1)
    house_input.send_keys(Keys.RETURN)

    # Ждём загрузки результатов
    time.sleep(6)
    driver.save_screenshot(filename)
    driver.quit()

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

        # Делаем скриншот
        get_screenshot(addr["city"], addr["street"], addr["house"], filename)

        # Проверяем изменения
        new_hash = get_hash(filename)
        old_hash = None
        if os.path.exists(hashfile):
            with open(hashfile, "r") as f:
                old_hash = f.read()

        # Отправляем фото сразу после запуска
        photo = FSInputFile(filename)
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo,
            caption=f"⚡ График для {addr['city']} {addr['street']} {addr['house']}"
        )

        # Сохраняем hash, чтобы при следующих запусках проверять изменения
        with open(hashfile, "w") as f:
            f.write(new_hash)

        os.remove(filename)

    await bot.session.close()

# ========================
# Запуск
# ========================
if __name__ == "__main__":
    asyncio.run(main())
