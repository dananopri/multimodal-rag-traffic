import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import time

# Налаштування
BASE_URL = "https://www.rhinocarhire.com/Drive-Smart-Blog/Drive-Smart-Ukraine/Ukraine-Road-Signs.aspx"
OUTPUT_DIR = "traffic_signs_data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
JSONL_FILE = os.path.join(OUTPUT_DIR, "signs.jsonl")

# Створення директорій
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Категорії знаків
CATEGORIES = {
    "Warning-Signs": "warning",
    "Information-Sign": "information",
    "Mandatory-Signs": "mandatory",
    "Priority-Signs": "priority",
    "Prohibitory-Signs": "prohibitory"
}

# Створюємо сесію для повторного використання з'єднань
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/png,image/webp,image/apng,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
})

def generate_sign_id(image_url):
    """Генерує унікальний ID на основі URL зображення"""
    return hashlib.md5(image_url.encode()).hexdigest()[:12]

def download_image(url, filepath, max_retries=5):
    """Завантажує зображення з повторними спробами і exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Перевіряємо що це дійсно зображення
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"\n⚠️  Не зображення: {url}")
                return False

            # Записуємо по частинах
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Перевіряємо що файл не порожній
            if os.path.getsize(filepath) > 0:
                return True
            else:
                os.remove(filepath)
                return False

        except requests.exceptions.Timeout:
            wait_time = (2 ** attempt) + 1
            print(f"\n⏱️  Timeout {url}. Спроба {attempt+1}/{max_retries}. Чекаємо {wait_time}с...")
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError:
            wait_time = (2 ** attempt) + 2
            print(f"\n🔌 Connection error {url}. Спроба {attempt+1}/{max_retries}. Чекаємо {wait_time}с...")
            time.sleep(wait_time)

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1
                print(f"\n❌ Помилка {url}: {e}. Спроба {attempt+1}/{max_retries}. Чекаємо {wait_time}с...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Не вдалось завантажити після {max_retries} спроб: {url}")
                return False

    return False

def extract_category_from_url(img_url):
    """Визначає категорію знаку з URL"""
    for folder_name, category in CATEGORIES.items():
        if folder_name in img_url:
            return category
    return "unknown"

def load_existing_signs():
    """Завантажує вже існуючі записи щоб продовжити з місця зупинки"""
    existing = set()
    if os.path.exists(JSONL_FILE):
        with open(JSONL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                existing.add(record['sign_id'])
        print(f"✓ Знайдено {len(existing)} вже завантажених знаків")
    return existing

def scrape_traffic_signs():
    """Основна функція скрейпінгу"""
    print(f"📡 Завантаження сторінки: {BASE_URL}")

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Помилка завантаження сторінки: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Знаходимо всі посилання на зображення знаків
    sign_items = soup.find_all('a', href=lambda x: x and '.png' in x.lower())

    print(f"✓ Знайдено {len(sign_items)} дорожніх знаків")

    # Завантажуємо існуючі записи
    existing_ids = load_existing_signs()

    # Створюємо папки для кожної категорії
    for category in set(CATEGORIES.values()):
        os.makedirs(os.path.join(IMAGES_DIR, category), exist_ok=True)

    # Лічильники
    downloaded = 0
    skipped = 0
    failed = 0

    # Обробка кожного знаку
    for item in tqdm(sign_items, desc="⬇️  Завантаження знаків"):
        try:
            # Отримуємо URL зображення
            img_url = urljoin(BASE_URL, item['href'])

            # Генеруємо ID
            sign_id = generate_sign_id(img_url)

            # Пропускаємо якщо вже є
            if sign_id in existing_ids:
                skipped += 1
                continue

            # Отримуємо опис знаку
            description = item.get_text(strip=True)

            # Визначаємо категорію
            category = extract_category_from_url(img_url)

            # Визначаємо локальний шлях до файлу
            filename = f"{sign_id}.png"
            local_path = os.path.join(IMAGES_DIR, category, filename)
            relative_path = os.path.join("images", category, filename)

            # Завантажуємо зображення
            if download_image(img_url, local_path):
                # Зберігаємо метадані одразу
                sign_record = {
                    "sign_id": sign_id,
                    "category": category,
                    "description": description,
                    "image_url": img_url,
                    "local_image_path": relative_path,
                    "source": BASE_URL
                }

                # Дописуємо в файл одразу (щоб не втратити прогрес)
                with open(JSONL_FILE, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(sign_record, ensure_ascii=False) + '\n')

                downloaded += 1
                existing_ids.add(sign_id)
            else:
                failed += 1

            # Пауза між запитами
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n⚠️  Переривання користувача. Зберігаємо прогрес...")
            break
        except Exception as e:
            print(f"\n❌ Помилка обробки знаку: {e}")
            failed += 1
            continue

    # Статистика
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА ЗАВАНТАЖЕННЯ")
    print("="*60)
    print(f"✅ Завантажено нових: {downloaded}")
    print(f"⏭️  Пропущено (вже є): {skipped}")
    print(f"❌ Помилок: {failed}")
    print(f"📝 Всього записів: {len(existing_ids)}")

    # Читаємо фінальну статистику по категоріям
    category_counts = {}
    with open(JSONL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            cat = record['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\n📂 За категоріями:")
    for category, count in sorted(category_counts.items()):
        print(f"   {category.capitalize()}: {count}")

    print(f"\n💾 Дані збережено в: {OUTPUT_DIR}/")
    print(f"   🖼️  Зображення: {IMAGES_DIR}/")
    print(f"   📄 Метадані: {JSONL_FILE}")

if __name__ == "__main__":
    print("="*60)
    print("🚗 СКРЕЙПЕР ДОРОЖНІХ ЗНАКІВ УКРАЇНИ")
    print("="*60)
    print("💡 Підказка: Можна перервати (Ctrl+C) і продовжити пізніше\n")

    try:
        scrape_traffic_signs()
        print("\n✅ Завершено успішно!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Скрипт перервано. Прогрес збережено!")
    finally:
        session.close()