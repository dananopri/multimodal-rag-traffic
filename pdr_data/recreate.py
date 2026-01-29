# pdr_data/recreate_chromadb.py
import json
import chromadb
from pathlib import Path
import shutil

def recreate_chromadb():
    """
    Recreate ChromaDB collection with proper document storage
    """
    # Load embeddings
    with open('pdr_data/embeddings.json', 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)

    print(f"Loaded {len(embeddings_data)} embeddings")

    # Count by type
    types = {}
    for item in embeddings_data:
        doc_type = item['metadata'].get('type', 'unknown')
        types[doc_type] = types.get(doc_type, 0) + 1

    print(f"By type: {types}")

    # Remove duplicates
    seen_ids = set()
    unique_embeddings = []

    for item in embeddings_data:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_embeddings.append(item)

    print(f"Using {len(unique_embeddings)} unique embeddings")

    # Delete old database
    if Path('./chroma_db').exists():
        shutil.rmtree('./chroma_db')
        print("Deleted old ChromaDB")

    # Create fresh client and collection
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.create_collection(
        name="traffic_rules",
        metadata={"description": "Ukrainian traffic rules and signs"}
    )

    # Prepare data
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for item in unique_embeddings:
        text = item['metadata'].get('text', '')

        # Don't skip empty - just use description or id
        if not text or len(text.strip()) == 0:
            text = item['metadata'].get('description', item['id'])

        ids.append(item['id'])
        embeddings.append(item['embedding'])
        documents.append(text)
        metadatas.append({
            'type': item['metadata'].get('type', ''),
            'category': item['metadata'].get('category', ''),
            'section_title': item['metadata'].get('section_title', ''),
            'rule_number': item['metadata'].get('rule_number', ''),
            'image_url': item['metadata'].get('source_url', '')
        })

    print(f"\nAdding {len(ids)} items to ChromaDB...")

    # Add in batches
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))

        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )

        print(f"Added {end}/{len(ids)}")

    print(f"\n✅ Successfully created ChromaDB with {len(ids)} items")

    # Verify by type
    verify = collection.get(include=['metadatas'])
    verify_types = {}
    for meta in verify['metadatas']:
        doc_type = meta.get('type', 'unknown')
        verify_types[doc_type] = verify_types.get(doc_type, 0) + 1

    print(f"\nVerification - documents by type:")
    for doc_type, count in verify_types.items():
        print(f"  {doc_type}: {count}")

if __name__ == "__main__":
    recreate_chromadb()