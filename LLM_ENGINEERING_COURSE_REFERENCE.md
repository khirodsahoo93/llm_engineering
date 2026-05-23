# LLM Engineering Course — Interview & Reference Guide

A single reference for everything covered in this course: libraries, tools, models, architecture, techniques, and how to answer interview questions.

---

## Table of Contents

1. [Course Overview & Objectives](#1-course-overview--objectives)
2. [Project Structure (Weeks 1–8)](#2-project-structure-weeks-18)
3. [Key Libraries & Tools](#3-key-libraries--tools)
4. [Models Used](#4-models-used)
5. [Core Techniques](#5-core-techniques)
6. [Architecture: "The Price Is Right" Capstone](#6-architecture-the-price-is-right-capstone)
7. [RAG (Retrieval-Augmented Generation)](#7-rag-retrieval-augmented-generation)
8. [Fine-Tuning (Frontier vs Open-Source)](#8-fine-tuning-frontier-vs-open-source)
9. [Deployment: Modal](#9-deployment-modal)
10. [Multi-Agent System](#10-multi-agent-system)
11. [Pros, Cons & Trade-offs](#11-pros-cons--trade-offs)
12. [Interview Q&A](#12-interview-qa)
13. [Quick Reference Cheat Sheet](#13-quick-reference-cheat-sheet)

---

## 1. Course Overview & Objectives

- **Goal:** Build an end-to-end **agentic** system that uses multiple LLMs and agents to solve a real problem.
- **Capstone:** "The Price Is Right" — find deals from RSS feeds, estimate product prices with multiple models (fine-tuned, frontier, neural network), and surface opportunities where estimated price >> deal price.
- **Skills covered:** Frontier APIs, RAG, embeddings, chunking, retrieval evaluation, fine-tuning (OpenAI + open-source QLoRA), deployment on Modal, and multi-agent orchestration.

---

## 2. Project Structure (Weeks 1–8)

| Week | Focus | Key Deliverables |
|------|--------|-------------------|
| **1** | First frontier LLM project | Web summarizer, intro to APIs |
| **2** | Frontier Model APIs | OpenAI, Anthropic, Google (Gemini), DeepSeek; streaming; multi-model chat |
| **3** | Colab, Hugging Face, synthetic data | Pipelines, data generation |
| **4** | Code generator | Python → C++ with frontier models; Gradio; docstrings |
| **5** | **RAG** | Ingest (loaders, splitters, Chroma, BM25), answer (hybrid search, reranking, query rewrite), evaluation (MRR, nDCG, LLM-as-judge) |
| **6** | **"The Price Is Right"** (part 1) | Data curation → preprocessor (LiteLLM) → evaluator → DNN + **OpenAI fine-tuning** (GPT-4.1-nano) |
| **7** | **Open-source fine-tuning** | QLoRA/PEFT on LLaMA 3.2-3B; prompt data; train & eval |
| **8** | **Agentic AI & deployment** | Modal (hello, Llama, pricer); SpecialistAgent, FrontierAgent, EnsembleAgent, ScannerAgent, MessagingAgent, PlanningAgent; DealAgentFramework; Gradio UI |

**Important folders:**
- `week5/implementation/` — LangChain RAG (ingest, answer), Chroma, BM25
- `week5/pro_implementation/` — RAG with reranking, query rewrite, LiteLLM
- `week5/evaluation/` — retrieval + answer evals
- `week6/pricer/` — Parser, Preprocessor (LiteLLM), DNN, Evaluator, batch
- `week7/pricer/` — Fine-tuning (PEFT/QLoRA), datasets, evaluator
- `week8/agents/` — All agents (base, specialist, frontier, ensemble, scanner, messaging, planning, etc.)
- `week8/` — Modal apps (hello.py, llama.py, pricer_ephemeral.py, pricer_service2.py), deal_agent_framework.py, price_is_right.py (Gradio)

---

## 3. Key Libraries & Tools

### APIs & LLM clients
- **openai** — OpenAI API (chat, embeddings, fine-tuning)
- **anthropic** — Claude API
- **google-generativeai** / **google-genai** — Gemini
- **litellm** — Unified completion API across OpenAI, Anthropic, Groq, etc.; `completion(messages=..., model="groq/openai/gpt-oss-20b")`
- **ollama** — Local models
- **groq** — Fast inference for open models

### LangChain (RAG, chains)
- **langchain**, **langchain-core**, **langchain-text-splitters** — Loaders, splitters, prompts, chains
- **langchain-openai** — ChatOpenAI, OpenAIEmbeddings
- **langchain-chroma** — Chroma vector store integration
- **langchain-huggingface** — HuggingFaceEmbeddings
- **langchain-community** — DirectoryLoader, TextLoader, etc.
- **langchain-experimental** — Experimental features

### Embeddings & retrieval
- **chromadb** — Vector DB; `PersistentClient`, `get_or_create_collection`, `query(query_embeddings=..., n_results=k)`
- **sentence_transformers** — Local embeddings (e.g. `all-MiniLM-L6-v2`) and **CrossEncoder** for reranking
- **rank_bm25** — BM25Okapi for keyword/lexical search

### ML / training
- **torch** — PyTorch (DNN, training loops)
- **transformers** — AutoTokenizer, AutoModelForCausalLM, from_pretrained
- **peft** — PeftModel (LoRA/QLoRA adapters)
- **bitsandbytes** — 4-bit quantization (BitsAndBytesConfig)
- **accelerate** — Device map, training utilities
- **datasets** — Hugging Face datasets
- **scikit-learn** — HashingVectorizer, metrics, TSNE (visualization)

### Deployment
- **modal** — Serverless GPU/CPU; `App`, `Image`, `Volume`, `Secret`, `@app.function`, `@app.cls`, `@modal.enter()`, `@modal.method()`, `modal.Cls.from_name()`, `modal.Function.from_name()`

### App / UI
- **gradio** — Web UI for demos (RAG app, Price Is Right, code generator)
- **plotly**, **jupyter-dash** — Visualizations

### Config & env
- **python-dotenv** — `load_dotenv(override=True)`, then `os.getenv("OPENAI_API_KEY")` etc.
- **.env** — OPENAI_API_KEY, ANTHROPIC_API_KEY, HF_TOKEN, GROQ_API_KEY, MODAL_TOKEN_ID/MODAL_TOKEN_SECRET

### Other
- **pydantic** — BaseModel, Field (structured outputs, deal/opportunity schemas)
- **feedparser** — RSS feeds (deals)
- **beautifulsoup4**, **requests** — Scraping deal pages
- **wandb** — Experiment tracking (optional)
- **tiktoken** — Token counting (optional)

---

## 4. Models Used

| Model | Use case | Where |
|-------|----------|--------|
| **gpt-4o-mini**, **gpt-4o**, **gpt-4.1-nano**, **gpt-5.1**, **gpt-5-mini** | Chat, RAG answer, pricer (frontier), scanner (structured output), evals | Weeks 2, 4, 5, 6, 8 |
| **claude-3-5-sonnet**, **claude-haiku**, **claude-opus-4-5** | Alternative frontier chat/code gen | Weeks 2, 4 |
| **gemini-2.0-flash-exp** | Google frontier | Week 2 |
| **meta-llama/Llama-3.2-3B** | Base for fine-tuning; raw generation (week8 llama.py) | Weeks 7, 8 |
| **ed-donner/price-2025-11-28_18.47.07** (PEFT) | Fine-tuned pricer on Modal | Week 8 |
| **text-embedding-3-large** (OpenAI) | Optional RAG embeddings | Week 5 |
| **all-MiniLM-L6-v2**, **all-mpnet-base-v2** | HuggingFace embeddings (RAG, FrontierAgent context) | Weeks 5, 8 |
| **cross-encoder/ms-marco-MiniLM-L-6-v2** | Reranking in RAG | Week 5 |
| **groq/openai/gpt-oss-20b** | Preprocessor (product title/category/brand); fast, cheap | Weeks 6, 8 |

---

## 5. Core Techniques

- **Structured outputs** — Pydantic models + `response_format=DealSelection` (OpenAI) or `parse()` for reliable JSON.
- **Query rewriting** — LLM rewrites user question for better retrieval (conversation history + current question).
- **Chunking** — RecursiveCharacterTextSplitter (e.g. 2000 chars, 200 overlap); Markdown/Python splitters where relevant.
- **Embeddings** — Encode docs and query; store in Chroma; search by similarity.
- **Hybrid search** — Combine semantic (vector) + lexical (BM25); merge and rank (e.g. weighted score).
- **Reranking** — Retrieve more (e.g. 20), then cross-encoder or LLM rerank to top-k (e.g. 10).
- **RAG prompt** — System message with `{context}` (retrieved chunks) + user question; answer with ChatOpenAI/LiteLLM.
- **Preprocessing** — Use a small/fast LLM (e.g. Groq) to normalize product text (title, category, brand, description) before pricing.
- **Ensemble** — Combine multiple pricers (e.g. specialist 0.1, frontier 0.8, neural network 0.1) with fixed or learned weights.
- **Quantization** — 4-bit (BitsAndBytesConfig) to run LLaMA on a single T4; QLoRA trains low-rank adapters on top.
- **Secrets** — Never hardcode API keys; use `.env` locally and Modal Secrets (e.g. `huggingface-secret` with HF_TOKEN) in cloud.

---

## 6. Architecture: "The Price Is Right" Capstone

High-level flow:

1. **Data (week6)**  
   - Curate product data → **Parser** (Item from JSON/raw) → **Preprocessor** (LiteLLM/Groq for title, category, brand, description) → **Evaluator** (train/val split, metrics).

2. **Baselines (week6)**  
   - **Deep Neural Network**: HashingVectorizer + residual MLP; train/eval.  
   - **Frontier LLM**: Prompt with product description; parse price from completion.

3. **Fine-tuning (weeks 6 & 7)**  
   - **Week 6:** OpenAI fine-tuning (e.g. GPT-4.1-nano) on JSONL prompt/completion pairs.  
   - **Week 7:** Open-source (LLaMA 3.2-3B) with QLoRA/PEFT; train in Colab; push adapter to Hugging Face.

4. **Deployment (week8)**  
   - **Modal**: Ephemeral pricer (load model per call) or **class-based** `Pricer` with `@modal.enter()` (load once), optional **Volume** for HF cache, `min_containers` for warm instances.  
   - **SpecialistAgent** calls Modal pricer via `modal.Cls.from_name("pricer-service", "Pricer")` and `pricer.price.remote(description)`.

5. **Agents (week8)**  
   - **ScannerAgent**: RSS → fetch deals → OpenAI with structured output → DealSelection (5 deals with product_description, price, url).  
   - **EnsembleAgent**: Preprocessor (LiteLLM) → SpecialistAgent (Modal) + FrontierAgent (RAG + GPT) + NeuralNetworkAgent (DNN) → weighted average (e.g. 0.8 frontier, 0.1 specialist, 0.1 DNN).  
   - **FrontierAgent**: Embed description with SentenceTransformer, query Chroma (products collection) for similar products + prices, build context, call GPT for price.  
   - **PlanningAgent**: Orchestrates scanner → ensemble pricing for each deal → sort by discount → MessagingAgent if discount > threshold.  
   - **DealAgentFramework**: Chroma products DB, PlanningAgent, memory (JSON of opportunities), `run()` → scan, price, notify, persist.

6. **UI**  
   - **price_is_right.py** (Gradio): Deal discovery, specialist + RAG flows, optional push notifications.

---

## 7. RAG (Retrieval-Augmented Generation)

### Ingest (week5)
- **Load**: DirectoryLoader + TextLoader (e.g. `**/*.md`), optional encoding.
- **Split**: RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200).
- **Embed**: HuggingFaceEmbeddings (e.g. all-MiniLM-L6-v2) or OpenAIEmbeddings (text-embedding-3-large).
- **Store**: Chroma.from_documents(chunks, embeddings, persist_directory=DB_NAME).
- **BM25**: Tokenize chunks (e.g. lower().split()), BM25Okapi(tokenized_docs), pickle index + document cache.

### Retrieve & answer
- **Query rewrite** (optional): LLM rewrites question using conversation history for better retrieval.
- **Semantic**: vectorstore.as_retriever(search_kwargs={"k": k}).invoke(query).
- **Keyword**: BM25.get_scores(tokenized_query), argsort, map back to documents.
- **Hybrid**: Combine semantic + BM25 scores (e.g. alpha * semantic + (1-alpha) * keyword), dedupe, take top-k.
- **Rerank**: CrossEncoder(query, doc) for top candidates, sort by score, take final top-k.
- **Prompt**: System message with `{context}` = concatenated reranked chunks; append user question; ChatOpenAI/LiteLLM.

### Evaluation (week5)
- **Retrieval**: MRR (mean reciprocal rank), nDCG (normalized DCG), keyword coverage (e.g. % of gold keywords in top-k).
- **Answer**: LLM-as-judge — accuracy, completeness, relevance (e.g. 1–5) + feedback vs reference answer.

---

## 8. Fine-Tuning (Frontier vs Open-Source)

### Frontier (OpenAI, week6)
- **Data**: JSONL with "messages" (role + content) or prompt/completion pairs.
- **API**: openai.files.create(), openai.fine_tuning.jobs.create().
- **Model**: e.g. gpt-4.1-nano.
- **Pros**: No GPU management, fast to iterate, good quality.  
- **Cons**: Lock-in, cost, less control over data and training.

### Open-source (week7)
- **Base**: meta-llama/Llama-3.2-3B (or similar).
- **Method**: QLoRA — 4-bit quantized base + LoRA adapters (PEFT); train only adapters.
- **Libraries**: transformers, peft, bitsandbytes, accelerate, datasets.
- **Data**: Prompt format consistent with inference (e.g. "What does this cost...\n\n{description}\n\nPrice is $" → "123").
- **Deployment**: Load base + PeftModel.from_pretrained(adapter); same prompt at inference.
- **Pros**: Full control, private data, no per-token vendor lock-in.  
- **Cons**: Need GPU (Colab/Modal), longer training, you own eval and ops.

---

## 9. Deployment: Modal

- **App**: `app = modal.App("pricer-service")`.
- **Image**: `Image.debian_slim().pip_install("torch", "transformers", "peft", ...)`; optional `.env({"HF_HUB_CACHE": "/cache"})`.
- **Secrets**: `modal.Secret.from_name("huggingface-secret")` (HF_TOKEN for gated models).
- **GPU**: `gpu="T4"`, `timeout=1800`.
- **Function**: `@app.function(...)` for stateless; load model inside function (ephemeral) or use a class.
- **Class**: `@app.cls(...)`, `@modal.enter()` for one-time setup (load model), `@modal.method()` for `price(description)`.
- **Volume**: `Volume.from_name("hf-hub-cache")`, mount at `/cache` so model is cached across cold starts.
- **Scaling**: `min_containers=1` keeps one warm; `0` allows scale-to-zero.
- **Client**: From another app or notebook: `Pricer = modal.Cls.from_name("pricer-service", "Pricer")`, then `pricer = Pricer()`, `pricer.price.remote(description)`.
- **CLI**: `uv run modal token set ...` or `uv run modal deploy` to deploy.

---

## 10. Multi-Agent System

- **Base**: `Agent` in `agents/agent.py` — name, color, `log(message)` for consistent logging.
- **SpecialistAgent**: Calls Modal-deployed fine-tuned pricer (remote).
- **FrontierAgent**: SentenceTransformer + Chroma (similar products) → context → OpenAI/GPT for price.
- **NeuralNetworkAgent**: Loads saved DNN weights (HashingVectorizer + PyTorch model), inference only.
- **EnsembleAgent**: Preprocessor (LiteLLM) → specialist + frontier + neural_network → weighted average.
- **ScannerAgent**: RSS → ScrapedDeal → OpenAI with structured output (DealSelection) → 5 deals with product_description, price, url.
- **MessagingAgent**: Sends notification (e.g. push) when a good opportunity is found.
- **PlanningAgent**: Holds scanner, ensemble, messenger; `plan(memory)` → scan, price top deals, sort by discount, alert if above threshold, return best Opportunity.
- **DealAgentFramework**: Chroma products collection, PlanningAgent, memory (list of Opportunity), `run()` → planner.plan(memory), append result, write memory to JSON.
- **Data models** (Pydantic): ScrapedDeal, Deal, DealSelection, Opportunity (deal, estimate, discount).

---

## 11. Pros, Cons & Trade-offs

| Topic | Pros | Cons |
|------|-----|------|
| **RAG vs fine-tuning** | RAG: no training, easy to update knowledge, interpretable (chunks). Fine-tuning: better at specific format/task, lower latency per query. | RAG: retrieval can miss or over-retrieve; context window limit. Fine-tuning: data and training cost; harder to update knowledge. |
| **Hybrid search** | Better recall for both semantic and keyword queries; handles typos and exact terms. | More moving parts; need to tune alpha and k. |
| **Reranking** | Improves precision (retrieve more, then rerank to top-k). | Extra compute (cross-encoder or LLM). |
| **OpenAI fine-tuning** | No GPU, fast, good UX. | Cost, vendor lock-in, black box. |
| **QLoRA** | Train big models on one GPU; small adapter size. | Slower than full fine-tune; slight quality trade-off. |
| **Modal** | Serverless GPU, scale-to-zero, good DX. | Cold starts unless min_containers; vendor. |
| **Ensemble** | Robust; combines strengths of different models. | More infra (multiple models/APIs), need to tune weights. |
| **Chroma** | Simple, local/persistent, good for prototypes. | Not distributed; scale limits for huge corpora. |

---

## 12. Interview Q&A

**Q: What is RAG and when would you use it vs fine-tuning?**  
RAG retrieves relevant documents and passes them as context to an LLM so it can answer using that knowledge. Use RAG when knowledge changes often or you need traceability; use fine-tuning when the task is narrow and format-specific (e.g. pricing from description) and you want fewer tokens per call.

**Q: How would you improve retrieval quality?**  
Use hybrid search (semantic + BM25), query rewriting with conversation history, reranking (cross-encoder or LLM), and tune chunk size/overlap. Evaluate with MRR, nDCG, and keyword coverage.

**Q: What is QLoRA?**  
QLoRA trains low-rank (LoRA) adapters on a 4-bit quantized base model. It reduces memory so you can fine-tune a 3B/7B model on a single consumer GPU while keeping most of the quality.

**Q: How does the SpecialistAgent get its price?**  
It calls a Modal-deployed class: `Pricer = modal.Cls.from_name("pricer-service", "Pricer")`, then `pricer.price.remote(description)`. The Modal app loads a 4-bit LLaMA base + PEFT adapter and runs inference on GPU.

**Q: What is the role of the Preprocessor in the pricer pipeline?**  
The Preprocessor uses a fast LLM (e.g. Groq) to normalize raw product text into a structured format (title, category, brand, description). This gives the pricing models cleaner, consistent input and better accuracy.

**Q: How is the EnsembleAgent weighted?**  
In the code it’s fixed: e.g. frontier 0.8, specialist 0.1, neural_network 0.1. In practice you could learn weights on a validation set or use a meta-model.

**Q: What’s the difference between pricer_ephemeral and pricer_service2?**  
Ephemeral loads the model inside every function call (simpler, higher latency). Service2 uses a class with `@modal.enter()` to load once per container and a Volume to cache the HF model, with optional `min_containers` for warm instances.

**Q: How do you evaluate RAG?**  
Retrieval: MRR, nDCG, keyword coverage over test queries. Answer: LLM-as-judge scoring accuracy, completeness, relevance against a reference, plus free-form feedback.

**Q: Why Chroma and BM25 together?**  
Chroma gives semantic similarity; BM25 gives lexical/keyword match. Together they cover paraphrases and exact terms (e.g. product codes); hybrid score merges the two rankings.

**Q: What is Modal’s Volume for?**  
To persist data across container restarts (e.g. Hugging Face model cache at `/cache`). Without it, each cold start re-downloads the model.

**Q: What is LiteLLM used for here?**  
Unified completion API: one `completion(messages=..., model="groq/openai/gpt-oss-20b")` call works across OpenAI, Anthropic, Groq, etc. Used in Preprocessor and some RAG/pro implementations.

**Q: Why use a cross-encoder for reranking instead of the same bi-encoder used for retrieval?**  
Bi-encoder encodes query and doc separately (fast, good for large-scale retrieval). Cross-encoder takes (query, doc) together and outputs a relevance score — more accurate but too slow to run on every doc; so we retrieve with bi-encoder (or hybrid) then rerank top candidates with cross-encoder.

**Q: What’s the flow from RSS to “opportunity”?**  
ScannerAgent fetches RSS → ScrapedDeal list → filter by memory (already seen URLs) → prompt GPT with structured output → DealSelection (5 deals). For each deal, PlanningAgent runs EnsembleAgent.price(description) → estimate; discount = estimate - deal.price. Sort by discount; if best > threshold, MessagingAgent.alert(best). Opportunity = (deal, estimate, discount).

**Q: Where is the products Chroma collection populated?**  
DealAgentFramework uses it for FrontierAgent’s RAG (similar products + prices). Population is typically a separate ingest step (e.g. product catalog with descriptions and prices embedded and stored with metadata).

---

## 13. Quick Reference Cheat Sheet

- **RAG pipeline**: Load → Split → Embed → Store (Chroma + optional BM25) → Query rewrite → Hybrid retrieve → Rerank → Prompt with context → LLM.
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2` (free) or OpenAI `text-embedding-3-large` (paid, often better).
- **Chunking**: RecursiveCharacterTextSplitter(2000, 200) common; adjust by doc type.
- **Fine-tuning**: OpenAI = JSONL + API. Open-source = base model + QLoRA (PEFT) + prompt-format data.
- **Modal**: App, Image, Secret, Volume; @app.function vs @app.cls + @modal.enter + @modal.method; from_name() to call from outside.
- **Agents**: Base Agent (logging) → Specialist (Modal), Frontier (RAG + GPT), DNN (local weights) → Ensemble (preprocess + weighted sum) → Scanner (RSS + structured output) → Planning (orchestrate) → DealAgentFramework (Chroma + memory + run).
- **Env**: .env + load_dotenv; Modal Secrets for HF_TOKEN and other keys in cloud.
- **Structured output**: Pydantic model + OpenAI `response_format=DealSelection` or `.parse()`.

---

### Where to find what (file map)

| What | Where |
|------|--------|
| RAG ingest (load, split, Chroma, BM25) | `week5/implementation/ingest.py` |
| RAG answer (rewrite, hybrid, rerank, prompt) | `week5/implementation/answer.py` |
| RAG evaluation (MRR, nDCG, LLM judge) | `week5/evaluation/eval.py` |
| Product preprocessor (LiteLLM) | `week6/pricer/preprocessor.py` |
| DNN pricer (PyTorch) | `week6/pricer/deep_neural_network.py` |
| Modal hello / Llama / pricer | `week8/hello.py`, `llama.py`, `pricer_ephemeral.py`, `pricer_service2.py` |
| All agents | `week8/agents/*.py` (agent.py base, specialist_agent, frontier_agent, ensemble_agent, scanner_agent, planning_agent, deals.py) |
| Deal framework + Chroma | `week8/deal_agent_framework.py` |
| Gradio Price Is Right UI | `week8/price_is_right.py` |
| Dependencies | `requirements.txt`, `pyproject.toml` |

---

*Use this doc to review before interviews and to quickly recall how each week and component fits into the full LLM engineering pipeline.*
