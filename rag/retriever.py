import chromadb
from vertexai.vision_models import MultiModalEmbeddingModel
from google.cloud import aiplatform

class TrafficRulesRetriever:
    def __init__(self, chroma_db_path="./chroma_db", project_id="multimodal-rag-traffic"):
        """Initialize retriever with ChromaDB and Vertex AI model"""
        self.client = chromadb.PersistentClient(path=chroma_db_path)
        self.collection = self.client.get_collection("traffic_rules")

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location="us-central1")
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    def retrieve(self, query: str, top_k: int = 5):
        """
        Retrieve top_k most relevant documents for a query
        """
        # Embed the query with Vertex AI
        embeddings = self.model.get_embeddings(contextual_text=query)
        query_embedding = embeddings.text_embedding

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['metadatas', 'distances']  # Don't include documents from query
        )

        # Get the IDs and fetch documents separately (workaround for ChromaDB bug)
        retrieved_ids = results['ids'][0]

        # Fetch full documents using IDs
        full_docs = self.collection.get(
            ids=retrieved_ids,
            include=['documents', 'metadatas']
        )

        return {
            'documents': full_docs['documents'],
            'metadatas': full_docs['metadatas'],
            'distances': results['distances'][0],
            'ids': retrieved_ids
        }

if __name__ == "__main__":
    # Test retrieval
    retriever = TrafficRulesRetriever()

    test_queries = [
         "Які правила для пішохідних переходів?",
    "Покажи попереджувальні знаки",
    "Обмеження швидкості"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 Query: {query}")
        print('='*80)

        results = retriever.retrieve(query, top_k=3)

        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        )):
            print(f"\n{i+1}. [{meta['type']}] Distance: {dist:.3f}")

            # Show full document (truncate at 300 chars for readability)
            if len(doc) > 300:
                print(f"   {doc[:300]}...")
            else:
                print(f"   {doc}")

            # Show metadata
            if meta.get('rule_number'):
                print(f"   Rule: {meta['rule_number']}")
            if meta.get('section_title'):
                print(f"   Section: {meta['section_title']}")
            if meta.get('image_url'):
                print(f"   🖼️  Image: {meta['image_url']}")