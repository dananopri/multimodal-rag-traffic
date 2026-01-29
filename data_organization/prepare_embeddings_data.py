import json
from pathlib import Path

def prepare_data_for_embeddings():
    """
    Combines traffic rules, signs, and their mappings into a unified dataset for embedding generation.

    Returns:
        list: Document dictionaries with id, type, text, image_path, and metadata

    Output:
        Saves to 'pdr_data/embedding_dataset.json'
    """

    script_dir = Path(__file__).parent

    # Load data
    rules_path = script_dir / 'rag_dataset.json'
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    signs_path = script_dir / 'signs_to_rules.json'
    with open(signs_path, 'r', encoding='utf-8') as f:
        signs_data = json.load(f)

    documents = []

    # Add traffic rules
    for rule in rules:
        doc = {
            'id': rule['id'],
            'type': 'rule',
            'text': rule['text'],
            'metadata': {
                'rule_number': rule.get('rule_number'),
                'section_id': rule.get('section_id'),
                'section_title': rule.get('section_title'),
                'source': rule.get('metadata', {}).get('source'),
                'url': rule.get('metadata', {}).get('url')
            }
        }
        documents.append(doc)

    # Add traffic signs (extract from "signs" key)
    signs_list = signs_data.get('signs', [])
    for sign in signs_list:
        related_rule_ids = []
        if sign.get('related_rules'):
            sorted_rules = sorted(
                sign['related_rules'],
                key=lambda x: x.get('relevance_score', 0),
                reverse=True
            )[:3]
            related_rule_ids = [rule['rule_id'] for rule in sorted_rules]

        doc = {
            'id': sign['sign_id'],
            'type': 'sign',
            'text': sign.get('description', ''),
            'image_path': sign.get('image_path'),
            'image_url': sign.get('source_url'),
            'metadata': {
                'category': sign.get('category'),
                'related_rules': related_rule_ids,
                'image_filename': sign.get('image_filename'),
                'source_url': sign.get('source_url')
            }
        }
        documents.append(doc)

    # Save dataset
    output_path = script_dir / 'embedding_dataset.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    rules_count = len([d for d in documents if d['type'] == 'rule'])
    signs_count = len([d for d in documents if d['type'] == 'sign'])

    print(f"✅ Created {len(documents)} documents for embedding")
    print(f"   - Rules: {rules_count}")
    print(f"   - Signs: {signs_count}")
    print(f"   - Output: {output_path}")

    return documents

if __name__ == "__main__":
    prepare_data_for_embeddings()