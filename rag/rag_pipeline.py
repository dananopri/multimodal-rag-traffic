import google.generativeai as genai
from retriever import TrafficRulesRetriever

class TrafficRulesRAG:
    def __init__(self, api_key: str):
        """Initialize RAG pipeline"""
        self.retriever = TrafficRulesRetriever()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def answer(self, query: str, top_k: int = 5):
        """
        Answer query using RAG

        Returns:
            dict with answer, sources, and images
        """
        # Retrieve relevant context
        results = self.retriever.retrieve(query, top_k=top_k)

        # Build context
        context_parts = []
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            context_parts.append(f"Source {i+1} [{meta['type']}]:\n{doc}\n")

        context = "\n".join(context_parts)

        # Generate answer
        prompt = f"""Based on Ukrainian traffic rules and signs, answer the question.

Context:
{context}

Question: {query}

Provide a clear answer in Ukrainian if the query is in Ukrainian, or in English if the query is in English.

Answer:"""

        response = self.model.generate_content(prompt)

        # Collect images
        images = [
            meta['image_url']
            for meta in results['metadatas']
            if meta['type'] == 'sign' and meta.get('image_url')
        ]

        return {
            'answer': response.text,
            'sources': results['documents'],
            'images': images,
            'metadata': results['metadatas']
        }

if __name__ == "__main__":

    API_KEY = "multimodal-rag-traffic"
    rag = TrafficRulesRAG(api_key=API_KEY)

    query = "Які правила для пішохідних переходів?"
    result = rag.answer(query)

    print(f"Query: {query}\n")
    print(f"Answer: {result['answer']}\n")
    print(f"Images: {len(result['images'])} sign(s)")