import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from rag.retriever import TrafficRulesRetriever
import google.generativeai as genai
import os

st.set_page_config(page_title="🚦 Traffic Rules Assistant", layout="wide")

# Initialize retriever
@st.cache_resource
def get_retriever():
    return TrafficRulesRetriever()

retriever = get_retriever()

# Configure Gemini
GEMINI_API_KEY = "multimodal-rag-traffic"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_answer(query: str, context: str):
    """Generate answer using Gemini"""
    prompt = f"""Based on Ukrainian traffic rules and signs, answer the question.

Context:
{context}

Question: {query}

Provide a clear, accurate answer. Answer in Ukrainian if the query is in Ukrainian, or in English if in English.

Answer:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error generating answer: {e}"

# Title
st.title("🚦 Ukrainian Traffic Rules Assistant")
st.markdown("Ask questions about Ukrainian traffic rules and signs")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Number of results", 3, 10, 5)
    use_llm = st.checkbox("Generate AI answer", value=True)

# Search input
query = st.text_input("Enter your question:",
                      placeholder="e.g., Які правила для пішохідних переходів?")

if query:
    with st.spinner("Searching..."):
        results = retriever.retrieve(query, top_k=top_k)

    # Generate answer if enabled
    if use_llm:
        st.subheader("💡 Answer")
        context = "\n\n".join([f"[{meta['type']}] {doc}"
                               for doc, meta in zip(results['documents'], results['metadatas'])])

        with st.spinner("Generating answer..."):
            answer = generate_answer(query, context)

        st.markdown(answer)
        st.divider()

    # Show retrieved sources
    st.subheader("📚 Sources")
    st.caption(f"Found {len(results['documents'])} relevant documents")

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results['distances']
    )):
        with st.expander(f"Source {i+1} - {meta['type'].upper()} (Relevance: {1-dist:.2%})", expanded=(i==0)):
            st.write(doc)

            col1, col2 = st.columns(2)
            with col1:
                if meta.get('rule_number'):
                    st.caption(f"📋 Rule: {meta['rule_number']}")
                if meta.get('section_title'):
                    st.caption(f"📖 Section: {meta['section_title']}")

            with col2:
                if meta.get('category'):
                    st.caption(f"🏷️ Category: {meta['category']}")

            if meta['type'] == 'sign' and meta.get('image_url'):
                st.image(meta['image_url'], width=200)