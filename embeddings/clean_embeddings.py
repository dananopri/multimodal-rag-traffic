import json

# Load embeddings
with open('pdr_data/embeddings.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Original: {len(data)} embeddings")

# Remove duplicates and bad documents
seen_ids = {}
clean_data = []
removed_bad = 0
removed_duplicates = 0

for item in data:
    item_id = item['id']
    text = item['metadata'].get('text', '')

    # Skip documents with only 'і' or empty text
    if len(text.strip()) <= 1:
        print(f"Removing bad document: {item_id} (text: '{text}')")
        removed_bad += 1
        continue

    # Handle duplicates - keep the one with longer text
    if item_id in seen_ids:
        existing_text = seen_ids[item_id]['metadata'].get('text', '')
        if len(text) > len(existing_text):
            # Replace with longer version
            for i, existing_item in enumerate(clean_data):
                if existing_item['id'] == item_id:
                    clean_data[i] = item
                    seen_ids[item_id] = item
                    print(f"Replaced duplicate {item_id} with longer version")
                    break
        removed_duplicates += 1
        continue

    seen_ids[item_id] = item
    clean_data.append(item)

print(f"\nCleaned: {len(clean_data)} embeddings")
print(f"Removed {removed_bad} bad documents")
print(f"Removed {removed_duplicates} duplicates")

# Save cleaned embeddings
with open('pdr_data/embeddings_clean.json', 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved to embeddings_clean.json")

# Backup and replace
import shutil
shutil.copy('pdr_data/embeddings.json', 'pdr_data/embeddings_backup.json')
shutil.copy('pdr_data/embeddings_clean.json', 'pdr_data/embeddings.json')

print("✅ Replaced embeddings.json with clean version (backup saved)")