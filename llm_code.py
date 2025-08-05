# 1. Setup: Import necessary libraries
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import os

# Import the Google Generative AI library for LLM calls
import google.generativeai as genai

# Import Google Generative AI Embeddings for vector store creation
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables from .env file (if present)
from dotenv import load_dotenv
load_dotenv()

# --- API Key Configuration ---
# The API key is loaded from an environment variable.
# It's recommended to set this as GOOGLE_API_KEY or GEMINI_API_KEY
# in your environment or a .env file.
# Example: GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    print("Please set the GOOGLE_API_KEY environment variable with your Google AI Studio API key.")
    exit()

# Configure the Google Generative AI client with the API key for both LLM and Embeddings
genai.configure(api_key=GOOGLE_API_KEY)
print("Google Generative AI client configured.")


def ragging(document_url_or_path):
    """
    Loads a PDF document, splits it into chunks, creates embeddings using Google's API,
    and stores them in a Chroma vector database.
    """
    document_path = document_url_or_path
    print(f"Loading document: {document_path}")
    try:
        loader = PyPDFLoader(document_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages.")
    except FileNotFoundError:
        print(f"Error: Document not found at {document_path}")
        exit()
    except Exception as e:
        print(f"Error loading document: {e}")
        exit()

    # Split documents into smaller chunks for better retrieval
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split document into {len(chunks)} chunks.")

    # Initialize Google Generative AI Embeddings model for API-based embedding generation
    # 'models/text-embedding-004' is Google's latest and recommended embedding model.
    # It uses the GOOGLE_API_KEY configured globally.
    print("Initializing Google Generative AI Embeddings model: models/text-embedding-004")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        print("Google Generative AI Embeddings loaded.")
    except Exception as e:
        print(f"Error initializing Google Generative AI Embeddings: {e}")
        print("Ensure 'langchain-google-genai' is installed and your GOOGLE_API_KEY is valid and has access to embedding models.")
        exit()

    # Create or load the Chroma vector store
    vector_db_dir = "chroma_db"
    print(f"Creating/loading Chroma vector store at: {vector_db_dir}")
    try:
        vector_store = Chroma.from_documents(
            chunks,
            embeddings,
            persist_directory=vector_db_dir
        )
        vector_store.persist() # Save the database to disk for future use
        print("Document indexed and vector store created/loaded.")
    except Exception as e:
        print(f"Error creating/loading Chroma DB: {e}")
        exit()

    # Set up the retriever for similarity search
    retriever = vector_store.as_retriever()
    return retriever

def query_rag(query_text: str, retriever):
    """
    Retrieves relevant documents based on the query and uses a Google Generative AI model
    (e.g., Gemini) to generate an answer based on the retrieved context.
    """
    print(f"\nRetrieving documents for query: '{query_text}'")
    
    # Retrieve relevant documents from the vector store
    relevant_docs = retriever.get_relevant_documents(query_text)
    
    if not relevant_docs:
        return "I could not find any relevant information in the document for your query."

    # Format the retrieved documents into a single context string
    context = "\n".join([doc.page_content for doc in relevant_docs])

    # Construct the prompt for the LLM
    # This prompt instructs the LLM to answer based *only* on the provided context.
    rag_prompt = f"""Use the following pieces of context to answer the question at the end. Answer the question by taking the given context as the only, one and only source of information.
    Observe the whole context keenly and answer the questions. Let the answer be in a one or two medium to long sentences.
    Read the whole context for a few times before answering the question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {query_text}

Answer:"""

    # Initialize the Google Generative AI model (e.g., Gemini 1.5 Flash)
    # 'gemini-1.5-flash' is a good choice for speed and cost-efficiency.
    # The API key is already configured globally via genai.configure()
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        # Generate content using the model
        response = model.generate_content(rag_prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "Received an unexpected response format from the Google Generative AI model."
    except Exception as e:
        print(f"Error during Google Generative AI query: {e}")
        return f"An error occurred while trying to get an answer from the model: {e}"
