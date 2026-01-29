import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import re

class PDRScraper:
    """Скрейпер для збору даних Правил Дорожнього Руху України"""

    def __init__(self, base_url: str = "https://dai.eu.com", output_dir: str = "pdr_data"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.data_dir = self.output_dir / "data"

        # Створюємо директорії
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Заголовки для запитів
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Розділи ПДР (34 + світлофори)
        self.sections = [
            {"id": 1, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/1-zagalni-polozhennja", "title": "Загальні положення"},
            {"id": 2, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/2-obovjazky-i-prava-vodijiv-mehanichnyh-transportnyh-zasobiv", "title": "Обов'язки і права водіїв"},
            {"id": 3, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/3-ruh-transportnyh-zasobiv-iz-specialnymy-sygnalamy", "title": "Рух транспортних засобів із спеціальними сигналами"},
            {"id": 4, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/4-obovjazky-i-prava-pishohodiv", "title": "Обов'язки і права пішоходів"},
            {"id": 5, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/5-obovjazky-i-prava-pasazhyriv", "title": "Обов'язки і права пасажирів"},
            {"id": 6, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/6-vymogy-do-vodijiv-mopediv-i-velosypediv", "title": "Вимоги до велосипедистів"},
            {"id": 7, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/7-vymogy-do-osib-jaki-kerujut-guzhovym-transportom-i-pogonychiv-tvaryn", "title": "Вимоги до осіб, які керують гужовим транспортом"},
            {"id": 8, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/8-reguljuvannja-dorozhnogo-ruhu", "title": "Регулювання дорожнього руху"},
            {"id": 9, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/9-poperedzhuvalni-sygnaly", "title": "Попереджувальні сигнали"},
            {"id": 10, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/10-pochatok-ruhu-ta-zmina-jogo-naprjamku", "title": "Початок руху та зміна напрямку"},
            {"id": 11, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/11-roztashuvannja-transportnyh-zasobiv-na-dorozi", "title": "Розташування транспортних засобів"},
            {"id": 12, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/12-shvydkist-ruhu", "title": "Швидкість руху"},
            {"id": 13, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/13-dystancija-interval-zustrichnyj-rozjizd", "title": "Дистанція, інтервал, зустрічний роз'їзд"},
            {"id": 14, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/14-obgin", "title": "Обгін"},
            {"id": 15, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/15-zupynka-i-stojanka", "title": "Зупинка і стоянка"},
            {"id": 16, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/16-projizd-perehrest", "title": "Проїзд перехресть"},
            {"id": 17, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/17-perevagy-marshrutnyh-transportnyh-zasobiv", "title": "Переваги маршрутних транспортних засобів"},
            {"id": 18, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/18-prozd-pshoxdnix-perexodv-zupinok-transportnix-zasobv", "title": "Проїзд пішохідних переходів"},
            {"id": 19, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/19-korystuvannja-zovnishnimy-svitlovymy-pryladamy", "title": "Користування світловими приладами"},
            {"id": 20, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/20-ruh-cherez-zaliznychni-perejizdy", "title": "Рух через залізничні переїзди"},
            {"id": 21, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/21-perevezennja-ljudej", "title": "Перевезення пасажирів"},
            {"id": 22, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/22-perevezennja-vantazhu", "title": "Перевезення вантажу"},
            {"id": 23, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/23-buksyruvannja-i-ekspluatacija-transportnyh-sostaviv", "title": "Буксирування"},
            {"id": 24, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/24-navchalna-jizda", "title": "Навчальна їзда"},
            {"id": 25, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/25-ruh-transportnyh-zasobiv-u-kolonah", "title": "Рух у колонах"},
            {"id": 26, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/26-ruh-u-zhytlovij-ta-pishohidnij-zoni", "title": "Рух у житловій зоні"},
            {"id": 27, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/27-ruh-po-avtomagistraljah-i-dorogah-dlja-avtomobiliv", "title": "Рух по автомагістралях"},
            {"id": 28, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/28-ruh-po-girskyh-dorogah-i-na-krutyh-spuskah", "title": "Рух по гірських дорогах"},
            {"id": 29, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/29-mizhnarodnyj-ruh", "title": "Міжнародний рух"},
            {"id": 30, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/30-nomerni-rozpiznavalni-znaky-napysy-i-poznachennja", "title": "Номерні знаки"},
            {"id": 31, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/31-tehnichnyj-stan-i-obladnannja-transportnyh-zasobiv", "title": "Технічний стан"},
            {"id": 32, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/32-okremi-pytannja-organizaciji-dorozhnogo-ruhu-shcho-potrebujut-uzgodzhennja-z-derzhavtoinspekcijeju", "title": "Окремі питання"},
            {"id": 33, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/dorozhni-znaky-dodatok-1", "title": "Дорожні знаки"},
            {"id": 34, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/dorozhnja-rozmitka-dodatok-2", "title": "Дорожня розмітка"},
            {"id": 35, "url": "pravila-dorozhnogo-ruxu-ukrani-2010/svitlofory-dodatok-3", "title": "Світлофори"}
        ]

    def extract_rules_from_text(self, full_text: str, section_id: int) -> List[Dict]:
        """
        Витягує правила з повного тексту.
        Працює з текстом, де номер і текст можуть бути на різних рядках.
        """
        rules = []
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]

        # Пропускаємо заголовок розділу
        start_idx = 0
        for i, line in enumerate(lines):
            if re.match(r'^\d+\.\s+', line):  # "1. Загальні положення"
                start_idx = i + 1
                break

        i = start_idx
        while i < len(lines):
            line = lines[i]

            # Шукаємо номер правила (формат: "1.1." або "1.1")
            rule_number_match = re.match(r'^(\d+\.\d+\.?)$', line)

            if rule_number_match:
                rule_number = rule_number_match.group(1).rstrip('.')

                # Збираємо текст правила (наступні рядки до наступного номера)
                rule_text_parts = []
                i += 1

                while i < len(lines):
                    next_line = lines[i]

                    # Перевіряємо чи це не наступний номер правила
                    if re.match(r'^(\d+\.\d+\.?)$', next_line):
                        break

                    # Додаємо текст
                    rule_text_parts.append(next_line)
                    i += 1

                # Об'єднуємо текст
                rule_text = ' '.join(rule_text_parts).strip()

                if rule_text:  # Зберігаємо тільки якщо є текст
                    rules.append({
                        "rule_number": rule_number,
                        "text": rule_text,
                        "section_id": section_id
                    })
            else:
                i += 1

        return rules

    def scrape_section(self, section: Dict) -> Dict:
        """Скрейпить один розділ"""
        print(f"Обробка розділу {section['id']}: {section['title']}")

        try:
            # Формуємо повний URL
            url = urljoin(self.base_url + '/', section['url'])

            # Отримуємо сторінку
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Витягуємо весь текст
            content_div = (
                soup.find('div', class_='pdd-text') or
                soup.find('div', class_='content') or
                soup.find('article') or
                soup.find('main')
            )

            if not content_div:
                print(f"  ⚠ Не знайдено контент для розділу {section['id']}")
                return None

            full_text = content_div.get_text(separator='\n', strip=True)

            # Витягуємо правила
            rules = self.extract_rules_from_text(full_text, section['id'])

            section_data = {
                "section_id": section['id'],
                "title": section['title'],
                "url": url,
                "full_text": full_text,
                "rules": rules,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Зберігаємо дані розділу
            output_file = self.data_dir / f"section_{section['id']:02d}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, ensure_ascii=False, indent=2)

            print(f"✓ Розділ {section['id']} оброблено:")
            print(f"  - Правил: {len(rules)}")
            if len(rules) > 0:
                print(f"  - Перше правило: {rules[0]['rule_number']}")
                print(f"  - Останнє правило: {rules[-1]['rule_number']}")

            return section_data

        except Exception as e:
            print(f"✗ Помилка обробки розділу {section['id']}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def scrape_all(self):
        """Скрейпить всі розділи"""
        print("Початок скрейпінгу ПДР України")
        print(f"Всього розділів: {len(self.sections)}")
        print("-" * 70)

        all_data = []

        for section in self.sections:
            section_data = self.scrape_section(section)
            if section_data:
                all_data.append(section_data)

            # Пауза між запитами
            time.sleep(1.5)

        # Зберігаємо загальний файл
        summary_file = self.output_dir / "all_sections_summary.json"

        total_rules = sum(len(s.get('rules', [])) for s in all_data)

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_sections": len(all_data),
                "total_rules": total_rules,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "sections": all_data
            }, f, ensure_ascii=False, indent=2)

        print("-" * 70)
        print(f"✓ Скрейпінг завершено!")
        print(f"Оброблено розділів: {len(all_data)}")
        print(f"Всього правил: {total_rules}")
        print(f"Дані збережено в: {self.output_dir}")

        # Детальна статистика
        print("\n" + "=" * 70)
        print("ДЕТАЛЬНА СТАТИСТИКА ПО РОЗДІЛАХ")
        print("=" * 70)
        for s in all_data:
            print(f"Розділ {s['section_id']:2d}: {s['title']:45s} - {len(s['rules']):3d} правил")

        return all_data

    def create_rag_dataset(self):
        """Створює датасет для RAG системи"""
        print("\nСтворення датасету для RAG...")

        rag_entries = []

        # Читаємо всі файли розділів
        for json_file in sorted(self.data_dir.glob("section_*.json")):
            with open(json_file, 'r', encoding='utf-8') as f:
                section = json.load(f)

            # Для кожного правила створюємо окремий запис
            for rule in section.get('rules', []):
                entry = {
                    "id": f"section_{section['section_id']}_rule_{rule['rule_number'].replace('.', '_')}",
                    "section_id": section['section_id'],
                    "section_title": section['title'],
                    "rule_number": rule['rule_number'],
                    "text": rule['text'],
                    "metadata": {
                        "source": "ПДР України 2026",
                        "section": section['title'],
                        "url": section['url']
                    }
                }
                rag_entries.append(entry)

            # Також додаємо повний текст розділу для загального контексту
            if section.get('full_text'):
                entry = {
                    "id": f"section_{section['section_id']}_full_text",
                    "section_id": section['section_id'],
                    "section_title": section['title'],
                    "rule_number": None,
                    "text": section['full_text'],
                    "metadata": {
                        "source": "ПДР України 2026",
                        "section": section['title'],
                        "url": section['url'],
                        "content_type": "full_section_text"
                    }
                }
                rag_entries.append(entry)

        # Зберігаємо датасет
        rag_file = self.output_dir / "rag_dataset.json"
        with open(rag_file, 'w', encoding='utf-8') as f:
            json.dump(rag_entries, f, ensure_ascii=False, indent=2)

        print(f"✓ RAG датасет створено: {len(rag_entries)} записів")
        print(f"Збережено в: {rag_file}")

        return rag_entries


def main():
    # Ініціалізуємо скрейпер
    scraper = PDRScraper(
        base_url="https://dai.eu.com",
        output_dir="pdr_data"
    )

    # Скрейпимо всі дані
    scraper.scrape_all()

    # Створюємо датасет для RAG
    scraper.create_rag_dataset()


if __name__ == "__main__":
    main()