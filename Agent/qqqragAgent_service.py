# ragAgent_service.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import ollama
from pinecone import Pinecone

load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

# Auto-detect embedding provider (fallback to GEMINI)
EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'GEMINI').upper()
print(f"🔧 Using embedding provider: {EMBEDDING_PROVIDER}")

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
INDEX_NAME = 'online-boutique-products'

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
index = pc.Index(INDEX_NAME)

# ---- Embedding function ----
if EMBEDDING_PROVIDER == 'GEMINI':
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    embedding_model = 'gemini-embedding-001'

    def get_embedding(text: str):
        return genai.embed_content(
            model=embedding_model,
            content=text,
            task_type="RETRIEVAL_QUERY"
        )["embedding"]

elif EMBEDDING_PROVIDER == 'OLLAMA':
    def get_embedding(text: str):
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text,
            host=OLLAMA_API_URL
        )
        return response["embedding"]
else:
    raise ValueError("Unknown embedding provider")

# ---- RAG Logic ----
def retrieve_products(user_query: str, top_k: int = 5):
    query_vector = get_embedding(user_query)
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    return results["matches"]

def recommend_products(user_query: str, matches):
    retrieved_products = []
    db_results = []

    for match in matches:
        m = match["metadata"]
        product_info = {
            "id": match["id"],
            "name": m.get("name"),
            "description": m.get("description"),
            "price_units": m.get("price_units"),
        }
        db_results.append(product_info)
        retrieved_products.append(
            f"{product_info['name']} - {product_info['description']} (${product_info['price_units']})"
        )

    context = "\n".join(retrieved_products)
    prompt = f"""
    The user said: "{user_query}"

    Here are some products from our catalog that might be relevant:
    {context}

    Please recommend the best products in a friendly, engaging way. Also score each of the products according to the relevance to the user given scenario/context.
    """

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    recommendation_text = response.text

    # if EMBEDDING_PROVIDER == 'GEMINI':
    #     model = genai.GenerativeModel("gemini-1.5-flash")
    #     response = model.generate_content(prompt)
    #     recommendation_text = response.text
    # else:
    #     response = ollama.chat(
    #         model="llama3.2:latest",
    #         messages=[
    #             {"role": "system", "content": "You are a helpful shopping assistant."},
    #             {"role": "user", "content": prompt}
    #         ]
    #     )
    #     recommendation_text = response["message"]["content"]

    return recommendation_text, db_results

# ---- API Server ----
app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/search")
def search_endpoint(request: QueryRequest):
    matches = retrieve_products(request.query)
    recommendation, db_results = recommend_products(request.query, matches)
    return {
        "recommendation": recommendation,
        "products": db_results
    }
