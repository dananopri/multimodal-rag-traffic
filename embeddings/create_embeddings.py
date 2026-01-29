import json
from pathlib import Path
from google.cloud import aiplatform
from vertexai.vision_models import MultiModalEmbeddingModel

PROJECT_ID = "multimodal-rag-traffic"
LOCATION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=LOCATION)

def create_embeddings(documents: list):
    """
    Create embeddings for text documents (rules and signs)
    """
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    embeddings_data = []
    skipped_long = 0

    for i, doc in enumerate(documents):
        print(f"Processing {i+1}/{len(documents)}: {doc['id']}")

        # Skip texts longer than 1000 characters (Vertex AI limit is 1024)
        if len(doc['text']) > 1000:
            print(f"⚠️  Skipping {doc['id']} - text too long ({len(doc['text'])} chars)")
            skipped_long += 1
            continue

        try:
            embeddings = model.get_embeddings(
                contextual_text=doc['text']
            )
            embedding_vector = embeddings.text_embedding

            embeddings_data.append({
                'id': doc['id'],
                'embedding': embedding_vector,
                'metadata': {
                    'type': doc['type'],
                    'text': doc['text'],
                    **doc.get('metadata', {})
                }
            })

        except Exception as e:
            print(f"❌ Error processing {doc['id']}: {e}")
            continue

    output_path = Path(__file__).parent.parent / 'pdr_data/embeddings.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Created {len(embeddings_data)} embeddings")
    print(f"⚠️  Skipped {skipped_long} long texts")
    print(f"   Saved to: {output_path}")

    return embeddings_data

if __name__ == "__main__":
    dataset_path = Path(__file__).parent.parent / 'pdr_data/embedding_dataset.json'
    with open(dataset_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    print(f"Loaded {len(documents)} documents")
    create_embeddings(documents)