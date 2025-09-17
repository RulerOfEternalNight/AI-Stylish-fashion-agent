import os
from dotenv import load_dotenv
import google.generativeai as genai
import ollama
from pinecone import Pinecone

load_dotenv()

# --- 1. Ask user which embedding provider to use ---
def get_provider_choice():
    print("Please choose an embedding provider:")
    print("1. Ollama (locally hosted)")
    print("2. Gemini (cloud-based)")
    choice = input("Enter your choice (1 or 2): ")
    if choice == '1':
        return 'OLLAMA'
    elif choice == '2':
        return 'GEMINI'
    else:
        print("Invalid choice. Exiting.")
        exit()

EMBEDDING_PROVIDER = get_provider_choice()

# --- 2. Connect to Pinecone ---
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
INDEX_NAME = 'online-boutique-products'

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
index = pc.Index(INDEX_NAME)

# --- 3. Embedding setup ---
if EMBEDDING_PROVIDER == 'GEMINI':
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found. Exiting.")
        exit()
    genai.configure(api_key=GEMINI_API_KEY)
    embedding_model = 'models/embedding-001'

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
            prompt=text
        )
        return response["embedding"]

else:
    raise ValueError("Unknown embedding provider")

# --- 4. Query Pinecone ---
def retrieve_products(user_query: str, top_k: int = 5):
    query_vector = get_embedding(user_query)
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    return results["matches"]

# --- 5. Generate Recommendations ---
def recommend_products(user_query: str, matches):
    retrieved_products = []
    for match in matches:
        m = match["metadata"]
        retrieved_products.append(
            f"{m['name']} - {m['description']} (${m['price_units']})"
        )

    context = "\n".join(retrieved_products)
    prompt = f"""
    The user said: "{user_query}"

    Here are some products from our catalog that might be relevant:
    {context}

    Please recommend the best products in a friendly, engaging way.
    """

    if EMBEDDING_PROVIDER == 'GEMINI':
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    else:
        response = ollama.chat(
            model="llama3.2:latest",
            # model="llama2",
            messages=[
                {"role": "system", "content": "You are a helpful shopping assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["message"]["content"]

# --- 6. Agent loop ---
if __name__ == "__main__":
    print("🛍️ Welcome to the Shopping Agent!")
    while True:
        user_query = input("\nWhat are you feeling or looking for? (type 'exit' to quit)\n> ")
        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye! 👋")
            break

        matches = retrieve_products(user_query, top_k=5)
        if not matches:
            print("No relevant products found.")
            continue

        recommendation = recommend_products(user_query, matches)
        print("\n✨ Recommendation ✨")
        print(recommendation)
