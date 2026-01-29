import json
from pathlib import Path

def update_image_paths():
    """
    Update embedding_dataset.json with correct local image paths
    """
    # Load current dataset
    with open('pdr_data/embedding_dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Image directories
    image_base = Path('pdr_data/traffic_signs_data/images')
    categories = {
        'warning': image_base / 'warning',
        'mandatory': image_base / 'mandatory',
        'prohibitory': image_base / 'prohibitory',
        'information': image_base / 'information',
        'priority': image_base / 'priority'
    }

    # Update sign documents
    signs_updated = 0
    signs_not_found = 0

    for doc in data:
        if doc['type'] == 'sign':
            category = doc.get('metadata', {}).get('category', '')
            image_url = doc.get('image_url', '')

            if category and image_url:
                # Extract filename from URL
                filename = image_url.split('/')[-1]

                # Build local path
                if category in categories:
                    local_path = categories[category] / filename

                    # Check if file exists
                    if local_path.exists():
                        doc['image_path'] = str(local_path)
                        signs_updated += 1
                    else:
                        print(f"⚠️  Image not found: {local_path}")
                        signs_not_found += 1

    # Save updated dataset
    with open('pdr_data/embedding_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Updated {signs_updated} sign image paths")
    if signs_not_found > 0:
        print(f"⚠️  {signs_not_found} images not found")
    print(f"   Saved to: pdr_data/embedding_dataset.json")

if __name__ == "__main__":
    update_image_paths()
    