import grpc
import demo_pb2
import demo_pb2_grpc
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import ollama
import os

# --- 1. Get User Input for Embedding Provider ---
def get_provider_choice():
    """Presents a menu to the user and gets their choice."""
    print("Please choose an embedding provider:")
    print("1. Ollama (locally hosted)")
    print("2. Gemini (cloud-based)")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == '1':
        return 'OLLAMA'
    elif choice == '2':
        return 'GEMINI'
    else:
        print("Invalid choice. Please run the script again and enter 1 or 2.")
        exit()

# Get the user's choice from the terminal
EMBEDDING_PROVIDER = get_provider_choice()

# --- 2. Fetch Product Data from gRPC API ---
PRODUCT_CATALOG_SERVICE_HOST = os.getenv('PRODUCT_CATALOG_SERVICE_HOST', 'localhost')
PRODUCT_CATALOG_SERVICE_PORT = os.getenv('PRODUCT_CATALOG_SERVICE_PORT', '3550')

def fetch_products():
    """Fetches all products from the Product Catalog Service."""
    try:
        channel = grpc.insecure_channel(f'{PRODUCT_CATALOG_SERVICE_HOST}:{PRODUCT_CATALOG_SERVICE_PORT}')
        stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)
        response = stub.ListProducts(demo_pb2.Empty())
        return response.products
    except grpc.RpcError as e:
        print(f"Failed to connect to productcatalogservice: {e}")
        return []

products = fetch_products()
if not products:
    print("No products found. Exiting.")
    exit()

# --- 3. Unified Embedding Function ---
if EMBEDDING_PROVIDER == 'GEMINI':
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found. Please set the environment variable.")
        exit()
    genai.configure(api_key=GEMINI_API_KEY)
    embedding_model = 'models/embedding-001'

    def get_embedding(text):
        """Generates a text embedding using the Gemini API."""
        return genai.embed_content(
            model=embedding_model,
            content=text,
            task_type="RETRIEVAL_DOCUMENT"
        )["embedding"]

elif EMBEDDING_PROVIDER == 'OLLAMA':
    # Ollama does not need a key, just a running server and a pulled model.
    def get_embedding(text):
        """Generates a text embedding using a locally hosted Ollama model."""
        try:
            response = ollama.embeddings(
                model='nomic-embed-text', 
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating embedding with Ollama: {e}")
            return None

# --- 4. Store in Pinecone ---
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
INDEX_NAME = 'online-boutique-products'

if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
    print("Pinecone API key or environment not found. Please set environment variables.")
    exit()

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index '{INDEX_NAME}'...")
    # Get dimension from a sample call
    dimension = len(get_embedding("sample text"))
    pc.create_index(
    name=INDEX_NAME,
    dimension=dimension,
    metric='cosine',
    spec=ServerlessSpec(cloud='aws', region='us-east-1') # Use your Pinecone region
)
    print("Index created.")

index = pc.Index(INDEX_NAME)

vectors_to_upsert = []
for product in products:
    combined_text = f"{product.name}. {product.description}"
    embedding = get_embedding(combined_text)
    
    if embedding is not None:
        vectors_to_upsert.append({
            "id": product.id,
            "values": embedding,
            "metadata": {
                "name": product.name,
                "description": product.description,
                "price_units": product.price_usd.units,
            }
        })

# ... (rest of upserting logic)
BATCH_SIZE = 100
for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
    batch = vectors_to_upsert[i:i + BATCH_SIZE]
    index.upsert(vectors=batch)
    print(f"Upserted {len(batch)} vectors.")

print(f"Finished upserting all {len(vectors_to_upsert)} product vectors.")