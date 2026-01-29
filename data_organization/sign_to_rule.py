"""
Script for linking EVERY traffic sign to traffic rules
Approach: for each sign, find the most relevant rules
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import shutil
from collections import defaultdict

class SignToRulesMatcher:
    """Links each traffic sign to relevant traffic rules"""

    def __init__(
        self,
        pdr_dataset_path: str = "pdr_data/rag_dataset.json",
        signs_jsonl_path: str = "traffic_signs_data/signs.jsonl",
        output_dir: str = "multimodal_dataset"
    ):
        # Determine base directory (where the script is located)
        script_dir = Path(__file__).parent

        self.pdr_dataset_path = script_dir / pdr_dataset_path if not Path(pdr_dataset_path).is_absolute() else Path(pdr_dataset_path)
        self.signs_jsonl_path = script_dir / signs_jsonl_path if not Path(signs_jsonl_path).is_absolute() else Path(signs_jsonl_path)
        self.output_dir = script_dir / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)

        # Create output directories
        self.output_images_dir = self.output_dir / "images"
        self.output_images_dir.mkdir(parents=True, exist_ok=True)

        # File validation
        print("Loading data...")
        print(f"Looking for files in: {script_dir}")

        if not self.pdr_dataset_path.exists():
            print(f"\n✗ ERROR: File not found: {self.pdr_dataset_path}")
            print(f"\nCheck directory structure:")
            print(f"Current directory: {Path.cwd()}")
            print(f"Script directory: {script_dir}")
            print(f"\nExpected structure:")
            print(f"{script_dir}/")
            print(f"  ├── pdr_data/")
            print(f"  │   └── rag_dataset.json")
            print(f"  ├── traffic_signs.jsonl")
            print(f"  └── sign_to_rule.py")
            raise FileNotFoundError(f"File not found: {self.pdr_dataset_path}")

        if not self.signs_jsonl_path.exists():
            print(f"\n✗ ERROR: File not found: {self.signs_jsonl_path}")
            raise FileNotFoundError(f"File not found: {self.signs_jsonl_path}")

        # Load data
        with open(self.pdr_dataset_path, 'r', encoding='utf-8') as f:
            self.pdr_data = json.load(f)

        self.signs_data = self.load_signs_metadata()

        print(f"✓ Loaded {len(self.pdr_data)} traffic rules")
        print(f"✓ Loaded {len(self.signs_data)} traffic signs")

    def load_signs_metadata(self) -> List[Dict]:
        """Load sign metadata from JSONL file"""
        signs = []
        with open(self.signs_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    signs.append(json.loads(line))
        return signs

    def get_comprehensive_keyword_mapping(self) -> Dict[str, List[str]]:
        """
        Comprehensive mapping for all sign types
        English sign name → Ukrainian keywords
        """
        return {
            # === WARNING SIGNS ===
            'crossroad': ['перехрестя', 'перехресть', 'розгалуження доріг'],
            'intersection': ['перехрестя', 'перехресть', 'примикання'],
            'railroad': ['залізничний переїзд', 'залізнич', 'колія'],
            'railway': ['залізничний переїзд', 'залізнич', 'колія'],
            'pedestrian': ['пішохід', 'пішохідний перехід', 'пішохідна доріжка'],
            'crossing': ['перехід', 'переїзд', 'перехрестя'],
            'children': ['діти', 'дитина', 'школа'],
            'school': ['школа', 'діти', 'навчальний заклад'],
            'cyclist': ['велосипед', 'велосипедист', 'велодоріжка'],
            'bike': ['велосипед', 'велосипедист', 'велодоріжка'],
            'slippery': ['слизька дорога', 'ожеледиця', 'ковзка'],
            'narrow': ['звуження', 'звужується', 'вужча'],
            'narrowing': ['звуження', 'звужується дорога'],
            'steep': ['крутий', 'підйом', 'спуск'],
            'ascent': ['підйом', 'гора', 'схил'],
            'descent': ['спуск', 'схил вниз'],
            'curve': ['поворот', 'закруглення', 'вигин'],
            'bend': ['поворот', 'закруглення'],
            'double curve': ['зигзаг', 'подвійний поворот', 'криві'],
            'two-way': ['двосторонній рух', 'зустрічний рух'],
            'traffic light': ['світлофор', 'сигнал'],
            'roadworks': ['дорожні роботи', 'ремонт', 'будівництво'],
            'tunnel': ['тунель', 'підземний перехід'],
            'bridge': ['міст', 'естакада', 'шляхопровід'],
            'movable bridge': ['розвідний міст'],
            'tram': ['трамвай', 'рейковий'],
            'cattle': ['тварини', 'худоба', 'корови'],
            'deer': ['олені', 'звірі', 'дикі тварини'],
            'animal': ['тварини', 'звірі'],
            'falling rocks': ['камені', 'каменепад', 'обвал'],
            'rocks': ['камені', 'скелі'],
            'crosswind': ['бічний вітер', 'вітер'],
            'uneven': ['нерівна дорога', 'яма'],
            'bad road': ['погана дорога', 'нерівність'],
            'surface': ['покриття', 'поверхня дороги'],
            'unpaved': ['ґрунтова дорога', 'без покриття'],
            'roundabout': ['круговий рух', 'кільце'],
            'side road': ['бічна дорога', 'примикання'],
            'dip': ['западина', 'улоговина', 'яма'],
            'soft verge': ['м\'яке узбіччя', 'узбіччя'],
            'speed bump': ['лежачий поліцейський', 'нерівність'],
            'traffic jam': ['затор', 'пробка', 'заторування'],
            'quayside': ['набережна', 'берег'],
            'riverbank': ['берег', 'річка'],
            'aircraft': ['літак', 'аеропорт', 'низький політ'],
            'give way': ['поступитися', 'дати дорогу', 'перевага'],
            'stop': ['зупинка', 'стоп', 'зупинитися'],
            'priority': ['пріоритет', 'перевага', 'головна дорога'],
            'danger': ['небезпека', 'обережно'],

            # === PROHIBITORY SIGNS ===
            'entry prohibited': ['в\'їзд заборонено', 'рух заборонено'],
            'no entry': ['в\'їзд заборонено', 'заборонено'],
            'prohibited': ['заборонено', 'заборонений', 'забороняється'],
            'overtaking': ['обгін', 'випередження'],
            'speed limit': ['обмеження швидкості', 'швидкість', 'максимальна швидкість'],
            'parking': ['стоянка', 'паркування'],
            'stopping': ['зупинка', 'зупинятися'],
            'no parking': ['стоянка заборонена', 'паркування заборонене'],
            'turn': ['поворот', 'повертати'],
            'turning left': ['поворот ліворуч', 'ліворуч'],
            'turning right': ['поворот праворуч', 'праворуч'],
            'u-turn': ['розворот', 'розвертання'],
            'truck': ['вантажівка', 'вантажний', 'автомобіль вантажний'],
            'lorry': ['вантажівка', 'вантажний автомобіль'],
            'motorcycle': ['мотоцикл', 'мото'],
            'car': ['легковий автомобіль', 'автомобіль'],
            'vehicle': ['транспортний засіб', 'засіб'],
            'tractor': ['трактор', 'сільськогосподарська техніка'],
            'moped': ['мопед'],
            'pedestrian prohibited': ['пішоходам заборонено', 'пішохід'],
            'cyclist prohibited': ['велосипедистам заборонено', 'велосипед'],
            'weight': ['вага', 'маса', 'навантаження'],
            'heavier': ['важче', 'вага', 'маса'],
            'height': ['висота', 'габарит'],
            'width': ['ширина', 'габарит'],
            'length': ['довжина', 'габарит'],
            'axle': ['вісь', 'осьове навантаження'],
            'dangerous goods': ['небезпечний вантаж', 'небезпечні вантажі'],
            'explosive': ['вибухові матеріали', 'вибухонебезпечні'],
            'polluted': ['забруднюючі речовини'],
            'horn': ['звуковий сигнал', 'гудок', 'сигналізація'],
            'distance': ['дистанція', 'відстань'],
            'zone': ['зона', 'ділянка'],
            'checkpoint': ['контрольний пункт', 'пост'],
            'trailer': ['причіп', 'напівпричіп'],
            'handcart': ['ручний візок', 'візок'],
            'horse cart': ['гужовий транспорт', 'віз'],

            # === MANDATORY SIGNS ===
            'straight': ['прямо', 'рух прямо'],
            'ahead': ['вперед', 'прямо'],
            'mandatory': ['обов\'язковий', 'наказовий'],
            'compulsory': ['обов\'язковий', 'необхідний'],
            'turning': ['поворот', 'повертати'],
            'passing left': ['об\'їзд зліва', 'об\'їхати зліва'],
            'passing right': ['об\'їзд справа', 'об\'їхати справа'],
            'path': ['доріжка', 'смуга'],
            'lane': ['смуга руху', 'доріжка'],
            'minimum speed': ['мінімальна швидкість', 'не менше'],
            'roundabout': ['круговий рух', 'об\'їзд'],
            'shared path': ['спільна доріжка', 'суміщена'],
            'equestrian': ['вершники', 'кінний'],

            # === INFORMATION SIGNS ===
            'motorway': ['автомагістраль', 'швидкісна дорога'],
            'expressway': ['швидкісна дорога', 'дорога для автомобілів'],
            'built-up area': ['населений пункт', 'місто', 'село'],
            'residential': ['житлова зона', 'двір'],
            'pedestrian zone': ['пішохідна зона', 'пішохідна вулиця'],
            'one-way': ['односторонній рух', 'одностороння'],
            'priority road': ['головна дорога', 'пріоритет'],
            'end of priority': ['кінець головної дороги'],
            'new lane': ['додаткова смуга', 'нова смуга'],
            'end of lane': ['закінчення смуги', 'звуження'],
            'parking zone': ['зона стоянки', 'парковка'],
            'national speed': ['загальні обмеження', 'швидкість'],
            'recommended': ['рекомендована', 'бажана'],
            'direction': ['напрямок', 'напрямок руху'],
            'ramp': ['з\'їзд', 'під\'їзд'],
            'destination': ['напрямок', 'пункт призначення'],

            # === PRIORITY SIGNS ===
            'give way': ['поступитися', 'дати дорогу'],
            'yield': ['поступитися дорогою'],
            'main road': ['головна дорога', 'пріоритетна'],
            'priority': ['пріоритет', 'перевага'],
            'uncontrolled': ['нерегульоване', 'без регулювання'],
        }

    def calculate_relevance_score(self, sign: Dict, pdr_entry: Dict) -> Tuple[float, List[str]]:
        """
        Calculate relevance of a sign to a traffic rule
        Returns: (score, list of matched keywords)
        """
        sign_desc = sign['description'].lower()
        pdr_text = pdr_entry['text'].lower()

        keyword_map = self.get_comprehensive_keyword_mapping()

        score = 0.0
        matched_keywords = []

        # Extract words from sign description
        sign_words = set(re.findall(r'\w+', sign_desc))

        # Check each word
        for eng_word in sign_words:
            if eng_word in keyword_map:
                ua_keywords = keyword_map[eng_word]

                # Check if Ukrainian keywords are in the rule text
                for ua_keyword in ua_keywords:
                    if ua_keyword in pdr_text:
                        # Base score for keyword match
                        score += 10.0
                        matched_keywords.append(f"{eng_word} → {ua_keyword}")

                        # Bonus if keyword is in term name
                        if pdr_entry.get('type') == 'term':
                            term_name = pdr_entry.get('term_name', '').lower()
                            if ua_keyword in term_name:
                                score += 5.0

        # Category-based bonus
        category_bonus = {
            'warning': {
                'section_ids': [1, 8, 16, 20],  # General, Regulation, Intersections, Railroad crossings
                'bonus': 2.0
            },
            'prohibitory': {
                'section_ids': [1, 14, 15, 33],  # General, Overtaking, Parking, Signs
                'bonus': 2.0
            },
            'mandatory': {
                'section_ids': [1, 10, 11, 16, 33],  # Starting movement, Positioning, Intersections
                'bonus': 2.0
            },
            'information': {
                'section_ids': [1, 27, 33],  # General, Motorways, Signs
                'bonus': 2.0
            },
            'priority': {
                'section_ids': [1, 16, 33],  # General, Intersections, Signs
                'bonus': 2.0
            }
        }

        category = sign['category']
        section_id = pdr_entry['section_id']

        if category in category_bonus:
            if section_id in category_bonus[category]['section_ids']:
                score += category_bonus[category]['bonus']

        # Section 33 (Road Signs) - higher priority for all signs
        if section_id == 33:
            score += 15.0

        return score, matched_keywords

    def find_best_rules_for_sign(self, sign: Dict, top_k: int = 5) -> List[Dict]:
        """
        Find best rules for a specific sign

        Args:
            sign: Traffic sign
            top_k: How many rules to return

        Returns:
            List of most relevant rules with scores
        """
        scored_entries = []

        for entry in self.pdr_data:
            score, keywords = self.calculate_relevance_score(sign, entry)

            if score > 0:  # Only if there's any match
                scored_entries.append({
                    'entry': entry,
                    'score': score,
                    'matched_keywords': keywords
                })

        # Sort by score
        scored_entries.sort(key=lambda x: x['score'], reverse=True)

        # Return top-K
        return scored_entries[:top_k]

    def copy_sign_image(self, sign: Dict) -> Optional[str]:
        """Copy sign image to output directory"""
        try:
            source_path = Path(sign['local_image_path'])

            if not source_path.exists():
                return None

            category = sign['category']
            sign_id = sign['sign_id']
            extension = source_path.suffix

            new_filename = f"{category}_{sign_id}{extension}"
            dest_path = self.output_images_dir / new_filename

            if not dest_path.exists():
                shutil.copy2(source_path, dest_path)

            return new_filename

        except Exception as e:
            print(f"  ✗ Error copying {sign.get('sign_id')}: {e}")
            return None

    def create_sign_centric_dataset(self) -> Dict:
        """
        Create dataset centered on signs
        Each sign is linked to rules
        """
        print("\n" + "="*70)
        print("LINKING SIGNS TO RULES")
        print("="*70)

        sign_dataset = []

        for i, sign in enumerate(self.signs_data):
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(self.signs_data)} signs...")

            # Find best rules for this sign
            best_matches = self.find_best_rules_for_sign(sign, top_k=5)

            # Copy image
            filename = self.copy_sign_image(sign)

            # Create entry
            sign_entry = {
                "sign_id": sign['sign_id'],
                "category": sign['category'],
                "description": sign['description'],
                "image_filename": filename,
                "image_path": str(self.output_images_dir / filename) if filename else None,
                "source_url": sign.get('image_url', ''),
                "related_rules": []
            }

            # Add related rules
            for match in best_matches:
                entry = match['entry']
                sign_entry['related_rules'].append({
                    "rule_id": entry['id'],
                    "rule_number": entry.get('rule_number'),
                    "section_id": entry['section_id'],
                    "section_title": entry['section_title'],
                    "text_preview": entry['text'][:150] + "...",
                    "relevance_score": match['score'],
                    "matched_keywords": match['matched_keywords']
                })

            sign_dataset.append(sign_entry)

        print(f"\n✓ Processing complete")

        # Statistics
        signs_with_rules = sum(1 for s in sign_dataset if len(s['related_rules']) > 0)
        signs_without_rules = len(sign_dataset) - signs_with_rules

        print(f"\nStatistics:")
        print(f"  Signs with rules: {signs_with_rules}/{len(sign_dataset)}")
        print(f"  Signs without rules: {signs_without_rules}")

        return {
            "total_signs": len(sign_dataset),
            "signs_with_rules": signs_with_rules,
            "signs_without_rules": signs_without_rules,
            "signs": sign_dataset
        }

    def create_rule_centric_dataset(self, sign_dataset: Dict) -> List[Dict]:
        """
        Create dataset centered on rules
        Add sign images to each rule
        """
        print("\n" + "="*70)
        print("ADDING SIGNS TO RULES")
        print("="*70)

        # Create map: rule_id → list of signs
        rule_to_signs = defaultdict(list)

        for sign_entry in sign_dataset['signs']:
            for rule in sign_entry['related_rules']:
                rule_id = rule['rule_id']

                rule_to_signs[rule_id].append({
                    "sign_id": sign_entry['sign_id'],
                    "category": sign_entry['category'],
                    "description": sign_entry['description'],
                    "filename": sign_entry['image_filename'],
                    "local_path": sign_entry['image_path'],
                    "relevance_score": rule['relevance_score']
                })

        # Add signs to rules
        enhanced_pdr = []
        for entry in self.pdr_data:
            enhanced_entry = entry.copy()

            rule_id = entry['id']
            if rule_id in rule_to_signs:
                # Sort by relevance
                signs = sorted(
                    rule_to_signs[rule_id],
                    key=lambda x: x['relevance_score'],
                    reverse=True
                )
                enhanced_entry['images'] = signs
                enhanced_entry['has_images'] = True
            else:
                enhanced_entry['images'] = []
                enhanced_entry['has_images'] = False

            enhanced_pdr.append(enhanced_entry)

        rules_with_signs = sum(1 for e in enhanced_pdr if e['has_images'])

        print(f"✓ Rules with images: {rules_with_signs}/{len(enhanced_pdr)}")

        return enhanced_pdr

    def save_datasets(self, sign_dataset: Dict, rule_dataset: List[Dict]):
        """Save both datasets"""

        print("\n" + "="*70)
        print("SAVING DATASETS")
        print("="*70)

        # 1. Sign-centric dataset
        sign_path = self.output_dir / "signs_to_rules.json"
        with open(sign_path, 'w', encoding='utf-8') as f:
            json.dump(sign_dataset, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Signs → Rules: {sign_path}")
        print(f"  {sign_dataset['total_signs']} signs")
        print(f"  {sign_dataset['signs_with_rules']} linked to rules")

        # 2. Rule-centric dataset
        rule_path = self.output_dir / "multimodal_rag_dataset.json"
        with open(rule_path, 'w', encoding='utf-8') as f:
            json.dump(rule_dataset, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Rules + Signs: {rule_path}")
        print(f"  {len(rule_dataset)} rules")

        # 3. Statistics
        stats = {
            "total_signs": sign_dataset['total_signs'],
            "signs_with_rules": sign_dataset['signs_with_rules'],
            "signs_without_rules": sign_dataset['signs_without_rules'],
            "total_rules": len(rule_dataset),
            "rules_with_images": sum(1 for r in rule_dataset if r['has_images']),
            "by_category": {}
        }

        for sign in sign_dataset['signs']:
            category = sign['category']
            if category not in stats['by_category']:
                stats['by_category'][category] = {
                    "total": 0,
                    "with_rules": 0
                }
            stats['by_category'][category]['total'] += 1
            if len(sign['related_rules']) > 0:
                stats['by_category'][category]['with_rules'] += 1

        stats_path = self.output_dir / "matching_statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Statistics: {stats_path}")


def main():
    """Main function"""

    matcher = SignToRulesMatcher(
        pdr_dataset_path="pdr_data/rag_dataset.json",
        signs_jsonl_path="traffic_signs_data/signs.jsonl",
        output_dir="multimodal_dataset"
    )

    # 1. Create sign-centric dataset
    sign_dataset = matcher.create_sign_centric_dataset()

    # 2. Create rule-centric dataset
    rule_dataset = matcher.create_rule_centric_dataset(sign_dataset)

    # 3. Save both
    matcher.save_datasets(sign_dataset, rule_dataset)


if __name__ == "__main__":
    main()