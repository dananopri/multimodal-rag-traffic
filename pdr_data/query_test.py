# query_test.py
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("traffic_rules")

# Test query
results = collection.query(
    query_texts=["What are the rules for pedestrian crossings?"],
    n_results=5
)

print("Top 5 results:")
for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"\n{i+1}. {metadata['type']}: {doc[:100]}...")