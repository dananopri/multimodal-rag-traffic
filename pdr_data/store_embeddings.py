import json
import chromadb
from pathlib import Path

def store_embeddings_in_chromadb():
    """
    Store embeddings in ChromaDB (local vector database)
    """
    script_dir = Path(__file__).parent

    # Load embeddings
    embeddings_path = script_dir / 'embeddings.json'
    with open(embeddings_path, 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)

    # Remove duplicates (keep first occurrence)
    seen_ids = set()
    unique_embeddings = []
    duplicates = 0

    for item in embeddings_data:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_embeddings.append(item)
        else:
            duplicates += 1

    print(f"Found {duplicates} duplicates, using {len(unique_embeddings)} unique embeddings")

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")

    # Delete existing collection if it exists
    try:
        client.delete_collection("traffic_rules")
        print("Deleted existing collection")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name="traffic_rules",
        metadata={"description": "Ukrainian traffic rules and signs"}
    )

    # Prepare data for ChromaDB
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for item in unique_embeddings:
        # Get text from metadata
        text = item['metadata'].get('text', '')

        ids.append(item['id'])
        embeddings.append(item['embedding'])
        documents.append(text)  # Store full text
        metadatas.append({
            'type': item['metadata'].get('type', ''),
            'category': item['metadata'].get('category', ''),
            'section_title': item['metadata'].get('section_title', ''),
            'rule_number': item['metadata'].get('rule_number', ''),
            'image_url': item['metadata'].get('source_url', '')
        })

    # Add to collection in batches (ChromaDB has limits)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        print(f"Added batch {i//batch_size + 1}: {batch_end}/{len(ids)}")

    print(f"\n✅ Stored {len(ids)} embeddings in ChromaDB")
    print(f"   - Collection: traffic_rules")
    print(f"   - Location: ./chroma_db")

    return collection

if __name__ == "__main__":
    store_embeddings_in_chromadb()
    