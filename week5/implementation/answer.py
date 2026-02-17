from pathlib import Path
import pickle
import os
from typing import List, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import numpy as np

from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")
BM25_INDEX_PATH = str(Path(__file__).parent.parent / "bm25_index.pkl")
DOCUMENTS_CACHE_PATH = str(Path(__file__).parent.parent / "documents_cache.pkl")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
RETRIEVAL_K = 3  # Retrieve more initially for re-ranking
FINAL_K = 10  # Final number of documents after re-ranking

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""

QUERY_REWRITE_PROMPT = """
Given the following conversation history and current question, rewrite the question to be more effective for information retrieval.
The rewritten query should:
1. Be clear and specific
2. Include relevant context from the conversation
3. Expand abbreviations or clarify ambiguous terms
4. Focus on the key information being sought

Conversation history:
{history}

Current question: {question}

Rewritten query (just the query, no explanation):
"""

vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
llm = ChatOpenAI(temperature=0, model_name=MODEL)

# Initialize re-ranker (cross-encoder for better accuracy)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Load BM25 index and document cache
bm25_index = None
documents_cache = []


def load_bm25_index():
    """Load BM25 index and document cache if they exist."""
    global bm25_index, documents_cache
    if os.path.exists(BM25_INDEX_PATH) and os.path.exists(DOCUMENTS_CACHE_PATH):
        with open(BM25_INDEX_PATH, "rb") as f:
            bm25_index = pickle.load(f)
        with open(DOCUMENTS_CACHE_PATH, "rb") as f:
            documents_cache = pickle.load(f)
        print(f"Loaded BM25 index with {len(documents_cache)} documents")
    else:
        print("BM25 index not found. Run ingest.py first to create it.")


def rewrite_query(question: str, history: list[dict] = []) -> str:
    """
    Rewrite the query using LLM to make it more effective for retrieval.
    """
    # Format conversation history
    history_text = "\n".join([
        f"User: {m['content']}" if m['role'] == 'user' else f"Assistant: {m['content']}"
        for m in history[-5:]  # Use last 5 messages for context
    ])
    
    if not history_text:
        history_text = "No previous conversation."
    
    # Create prompt for query rewriting
    prompt = QUERY_REWRITE_PROMPT.format(history=history_text, question=question)
    
    # Use LLM to rewrite query
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    rewritten_query = response.content.strip()
    
    # Fallback to original if rewriting fails
    if not rewritten_query or len(rewritten_query) < 5:
        rewritten_query = question
    
    return rewritten_query


def semantic_search(query: str, k: int = RETRIEVAL_K) -> List[Document]:
    """
    Perform semantic search using vector embeddings.
    """
    docs = retriever.invoke(query, k=k)
    return docs


def keyword_search(query: str, k: int = RETRIEVAL_K) -> List[Document]:
    """
    Perform keyword/lexical search using BM25.
    """
    if bm25_index is None or len(documents_cache) == 0:
        # Fallback to semantic search if BM25 not available
        return semantic_search(query, k)
    
    # Tokenize query
    tokenized_query = query.lower().split()
    
    # Get BM25 scores
    scores = bm25_index.get_scores(tokenized_query)
    
    # Get top k indices
    top_indices = np.argsort(scores)[::-1][:k]
    
    # Return documents with scores > 0
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append(documents_cache[idx])
    
    return results


def hybrid_search(query: str, k: int = RETRIEVAL_K, alpha: float = 0.5) -> List[Document]:
    """
    Perform hybrid search combining semantic and keyword search.
    
    Args:
        query: Search query
        k: Number of documents to retrieve
        alpha: Weight for semantic search (1-alpha for keyword search)
    """
    # Perform both searches
    semantic_docs = semantic_search(query, k=k)
    keyword_docs = keyword_search(query, k=k)
    
    # Create document ID to document mapping
    doc_dict = {}
    doc_scores = {}
    
    # Process semantic results
    for i, doc in enumerate(semantic_docs):
        doc_id = id(doc)  # Use object ID as unique identifier
        doc_dict[doc_id] = doc
        # Normalize semantic score (inverse rank, higher is better)
        semantic_score = (len(semantic_docs) - i) / len(semantic_docs)
        doc_scores[doc_id] = alpha * semantic_score
    
    # Process keyword results
    for i, doc in enumerate(keyword_docs):
        doc_id = id(doc)
        if doc_id not in doc_dict:
            doc_dict[doc_id] = doc
            doc_scores[doc_id] = 0
        
        # Normalize BM25 score (inverse rank, higher is better)
        keyword_score = (len(keyword_docs) - i) / len(keyword_docs)
        doc_scores[doc_id] += (1 - alpha) * keyword_score
    
    # Sort by combined score
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top k documents
    results = [doc_dict[doc_id] for doc_id, _ in sorted_docs[:k]]
    
    return results


def rerank_documents(query: str, documents: List[Document], top_k: int = FINAL_K) -> List[Document]:
    """
    Re-rank documents using a cross-encoder model.
    
    Args:
        query: Search query
        documents: List of documents to re-rank
        top_k: Number of top documents to return
    """
    if not documents:
        return []
    
    # Prepare pairs for cross-encoder
    pairs = [[query, doc.page_content] for doc in documents]
    
    # Get relevance scores
    scores = reranker.predict(pairs)
    
    # Sort documents by score
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top k documents
    return [doc for doc, score in scored_docs[:top_k]]


def fetch_context(question: str, use_rewriting: bool = True, use_hybrid: bool = True, use_reranking: bool = True) -> list[Document]:
    """
    Retrieve relevant context documents using enhanced RAG pipeline.
    
    Args:
        question: User question
        use_rewriting: Whether to use query rewriting
        use_hybrid: Whether to use hybrid search (semantic + keyword)
        use_reranking: Whether to use re-ranking
    """
    # Step 1: Query rewriting
    if use_rewriting:
        rewritten_query = rewrite_query(question)
    else:
        rewritten_query = question
    
    # Step 2: Hybrid search
    if use_hybrid:
        docs = hybrid_search(rewritten_query, k=RETRIEVAL_K)
    else:
        docs = semantic_search(rewritten_query, k=RETRIEVAL_K)
    
    # Step 3: Re-ranking
    if use_reranking and len(docs) > 1:
        docs = rerank_documents(rewritten_query, docs, top_k=FINAL_K)
    
    return docs


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question


def answer_question(question: str, history: list[dict] = [], use_rewriting: bool = True, use_hybrid: bool = True, use_reranking: bool = True) -> tuple[str, list[Document]]:
    """
    Answer the given question with enhanced RAG; return the answer and the context documents.
    
    Args:
        question: User question
        history: Conversation history
        use_rewriting: Whether to use query rewriting
        use_hybrid: Whether to use hybrid search
        use_reranking: Whether to use re-ranking
    """
    # Use enhanced retrieval pipeline
    docs = fetch_context(question, use_rewriting, use_hybrid, use_reranking)
    
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content, docs


# Load BM25 index on module import
load_bm25_index()
