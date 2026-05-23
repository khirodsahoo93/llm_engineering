import os
import glob
import pickle
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi


from dotenv import load_dotenv

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")
BM25_INDEX_PATH = str(Path(__file__).parent.parent / "bm25_index.pkl")
DOCUMENTS_CACHE_PATH = str(Path(__file__).parent.parent / "documents_cache.pkl")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

load_dotenv(override=True)

# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


def fetch_documents():
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)
    return documents


def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


def create_bm25_index(chunks):
    """
    Create BM25 index for keyword/lexical search.
    """
    # Tokenize documents for BM25
    tokenized_docs = [doc.page_content.lower().split() for doc in chunks]
    
    # Create BM25 index
    bm25_index = BM25Okapi(tokenized_docs)
    
    # Save BM25 index and document cache
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump(bm25_index, f)
    
    with open(DOCUMENTS_CACHE_PATH, "wb") as f:
        pickle.dump(chunks, f)
    
    print(f"Created BM25 index with {len(chunks)} documents")
    print(f"BM25 index saved to {BM25_INDEX_PATH}")
    print(f"Document cache saved to {DOCUMENTS_CACHE_PATH}")
    
    return bm25_index


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    
    # Create vector embeddings
    vectorstore = create_embeddings(chunks)
    
    # Create BM25 index for keyword search
    bm25_index = create_bm25_index(chunks)
    
    print("Ingestion complete - both vector and BM25 indices created")
