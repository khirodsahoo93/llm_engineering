# LLM Engineering — Project Structure & Code Walkthrough (Step by Step)

This document walks through **each week’s code** with key snippets so you can **remember and explain** the implementation in interviews. Use it together with `LLM_ENGINEERING_COURSE_REFERENCE.md`.

---

## Week 1: First Frontier LLM — Web Scraper + Summarizer

**Objective:** Fetch a webpage, clean its text, and send it to an LLM for a summary. Foundation for “content → LLM” pipelines.

### 1.1 Scraper — Fetch and clean HTML

**File:** `week1/scraper.py`

- Use **requests** + **BeautifulSoup** to get HTML and extract text.
- Strip scripts, styles, images; get `body` text; truncate to a limit (e.g. 2000 chars) to stay within context.

```python
def fetch_website_contents(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]
```

**Interview takeaway:** Always clean HTML (remove script/style) and cap length; use a realistic User-Agent header.

### 1.2 Build messages and call the LLM

**File:** `week1/solution.py` (or similar)

- **Message format:** `[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]`.
- Use **OpenAI client** (or `base_url` + `api_key='ollama'` for local Ollama).

```python
def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website}
    ]

def summarize(url):
    ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
    website = fetch_website_contents(url)
    response = ollama.chat.completions.create(
        model=MODEL,
        messages=messages_for(website)
    )
    return response.choices[0].message.content
```

**Interview takeaway:** System prompt sets behavior; user message holds the actual content (e.g. webpage). Same pattern everywhere: build `messages`, then `create()`.

---

## Week 2: Frontier Model APIs — Multi-Provider, Streaming, Structured Output

**Objective:** Use multiple providers (OpenAI, Anthropic, Google), streaming, and (later) structured outputs.

### 2.1 Same scraper, different backends

- Week 2 reuses `scraper.py` (same `fetch_website_contents`). The change is **which client** you call (OpenAI, Anthropic, etc.).

### 2.2 Message shape is universal

- All frontier APIs use a **messages** array: `system`, `user`, `assistant`.
- You swap the client; the prompt design stays the same.

### 2.3 What to remember for interviews

- **OpenAI:** `OpenAI().chat.completions.create(model=..., messages=...)`.
- **Anthropic:** `anthropic.Anthropic().messages.create(model=..., messages=..., max_tokens=...)`.
- **Streaming:** Use `.stream()` or `stream=True` and iterate over chunks.
- **Structured output:** In Week 8 we use `response_format=PydanticModel` or `.parse()`; the idea is “LLM returns JSON matching this schema.”

---

## Week 3: Colab, Hugging Face Pipelines, Synthetic Data

**Objective:** Run in Colab, use Hugging Face `pipeline()` for local/simple models, generate synthetic data for later training.

### 3.1 What you do

- **Hugging Face:** `pipeline("text-generation", model="...")` or similar; load datasets with `datasets.load_dataset()`.
- **Synthetic data:** Use an LLM to generate training examples (e.g. question/answer pairs or product descriptions) and save as JSON/Parquet for Week 6/7.

### 3.2 Interview takeaway

- `transformers` pipelines are for quick inference; for fine-tuning you use `AutoTokenizer`, `AutoModelForCausalLM`, and a `Trainer` or `SFTTrainer`.
- Synthetic data = LLM-generated examples to augment or create training data; quality depends on prompts and filtering.

---

## Week 4: Code Generator — Python → C++, Multi-Model, Gradio

**Objective:** Build an app that takes Python code, calls one of several LLMs (OpenAI, Claude, etc.), gets C++ (or similar), and optionally compiles/runs it. Learn **multi-model** and **Gradio** wiring.

### 4.1 Lazy client init and env

**File:** `week4/app.py`

- API keys from **env**; use **lazy** client creation so Gradio doesn’t break if a key is missing at import.

```python
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found...")
    return OpenAI(api_key=api_key, http_client=httpx.Client(...))
```

### 4.2 Model choice and prompt

- One UI, multiple models: e.g. `OPENAI_MODEL = "gpt-4o"`, `CLAUDE_MODEL = "claude-3-5-sonnet-..."`.
- **System prompt** describes the task (e.g. “Convert Python to C++, explain briefly”); **user prompt** = the code.
- Optional: run `subprocess` to compile/execute generated code (security warning in app).

### 4.3 Interview takeaway

- **Gradio:** `gr.Blocks()`, `gr.Chatbot` / `gr.Textbox`, `.submit(fn, inputs=[...], outputs=[...]).then(...)` to chain: user input → LLM → display.
- **Multi-model:** Same messages, different `model` and client; keep keys in `.env` and load with `load_dotenv()`.

---

## Week 5: RAG — Ingest, Retrieve, Answer, Evaluate

**Objective:** Build a RAG pipeline: load docs → chunk → embed → store in Chroma (+ BM25) → at query time: rewrite query → hybrid search → rerank → prompt LLM with context → return answer. Then evaluate retrieval and answer quality.

### 5.1 Ingest — Load, split, embed, store

**File:** `week5/implementation/ingest.py`

**Step 1 — Load documents:**

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def fetch_documents():
    for folder in folders:
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        # add metadata e.g. doc_type
```

**Step 2 — Chunk:**

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)
```

**Step 3 — Embed and store in Chroma:**

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks, embedding=embeddings, persist_directory=DB_NAME
)
```

**Step 4 — BM25 for keyword search:**

```python
from rank_bm25 import BM25Okapi

tokenized_docs = [doc.page_content.lower().split() for doc in chunks]
bm25_index = BM25Okapi(tokenized_docs)
# pickle bm25_index and chunks for answer.py
```

**Interview takeaway:** Ingest = Load → Split (RecursiveCharacterTextSplitter) → Embed → Chroma; optionally BM25 and save so **answer** can do hybrid search.

### 5.2 Answer — Query rewrite, hybrid search, rerank, prompt

**File:** `week5/implementation/answer.py`

**Step 1 — Optional query rewrite (better retrieval):**

```python
def rewrite_query(question: str, history: list[dict]) -> str:
    # Format last N turns of history + current question
    prompt = QUERY_REWRITE_PROMPT.format(history=history_text, question=question)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
```

**Step 2 — Hybrid search (semantic + BM25):**

```python
# Semantic: retriever.invoke(query, k=k)
# Keyword: bm25_index.get_scores(tokenized_query), argsort, map to docs
# Merge: e.g. alpha * semantic_rank_score + (1-alpha) * keyword_rank_score, sort, top-k
def hybrid_search(query, k, alpha=0.5):
    semantic_docs = semantic_search(query, k=k)
    keyword_docs = keyword_search(query, k=k)
    # merge by score, dedupe, return top k
```

**Step 3 — Rerank with cross-encoder:**

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [[query, doc.page_content] for doc in documents]
scores = reranker.predict(pairs)
# sort docs by scores, return top FINAL_K
```

**Step 4 — Build prompt and call LLM:**

```python
context = "\n\n".join(doc.page_content for doc in docs)
system_prompt = SYSTEM_PROMPT.format(context=context)
messages = [SystemMessage(content=system_prompt)] + convert_to_messages(history) + [HumanMessage(content=question)]
response = llm.invoke(messages)
return response.content, docs
```

**Interview takeaway:** RAG answer = (optional) rewrite → hybrid (vector + BM25) → rerank (cross-encoder) → concatenate context in system message → LLM. Same context window and message format as Week 1, but context is **retrieved**, not the whole doc.

### 5.3 Evaluation — Retrieval and LLM-as-judge

**File:** `week5/evaluation/eval.py`

**Retrieval metrics:**

```python
# MRR: for each keyword, 1/rank of first doc containing it; average
def calculate_mrr(keyword, retrieved_docs):
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword.lower() in doc.page_content.lower():
            return 1.0 / rank
    return 0.0

# nDCG: DCG / ideal DCG (binary relevance: keyword in doc or not)
# Keyword coverage: % of gold keywords that appear in top-k docs
```

**Answer quality (LLM-as-judge):**

```python
# Get RAG answer, then:
judge_messages = [
    {"role": "system", "content": "You are an expert evaluator..."},
    {"role": "user", "content": f"Question: {q}\nGenerated: {ans}\nReference: {ref}\nScore 1-5 on accuracy, completeness, relevance."}
]
judge_response = completion(model=MODEL, messages=judge_messages, response_format=AnswerEval)
```

**Interview takeaway:** Retrieval = MRR, nDCG, keyword coverage. Answer = LLM judge with a **structured output** (Pydantic) for scores and feedback.

### 5.4 Gradio app

**File:** `week5/app.py`

- `answer_question(last_message, prior)` returns `(answer, context_docs)`.
- Chatbot state = `history`; each submit: append user message → call `answer_question` → append assistant message; show `context_docs` in a second column.

```python
def chat(history):
    last_message = history[-1]["content"]
    answer, context = answer_question(last_message, history[:-1])
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context)

message.submit(put_message_in_chatbot, ...).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])
```

---

## Week 6: “The Price Is Right” — Data, Preprocess, Evaluate, Fine-Tune (OpenAI)

**Objective:** Curate product data, normalize with an LLM (preprocessor), evaluate baselines (DNN, frontier LLM), then **fine-tune a frontier model** (e.g. GPT-4.1-nano) on prompt/completion pairs.

### 6.1 Data model — Item

**File:** `week6/pricer/items.py`

- **Pydantic** model for one product: title, category, price, optional `full` (raw text), `prompt` (for training).

```python
class Item(BaseModel):
    title: str
    category: str
    price: float
    full: Optional[str] = None
    prompt: Optional[str] = None
    # ...

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.price)}.00"

    @classmethod
    def from_hub(cls, dataset_name: str):
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )
```

**Interview takeaway:** Training format is fixed: same `QUESTION` and `PREFIX` at train and inference. Data lives on Hugging Face Hub; `from_hub` loads train/val/test.

### 6.2 Parser — Raw JSON → Item, scrub

**File:** `week6/pricer/parser.py`

- Parse raw product JSON; **scrub** (remove part numbers, limit length); filter by `MIN_CHARS`, `MIN_PRICE`, `MAX_PRICE`.
- Output: list of `Item` with `full` text and `make_prompt(full)` for training.

```python
def scrub(title, description, features, details) -> str:
    # Remove REMOVALS keys from details, concatenate title + description + features + details
    # Regex to drop long alphanumeric codes, truncate to MAX_TEXT_TOTAL
```

### 6.3 Preprocessor — LLM normalizes product text

**File:** `week6/pricer/preprocessor.py`

- Use **LiteLLM** (e.g. Groq) to turn raw product text into a **structured short description** (title, category, brand, description). Same idea as Week 1: messages → completion.

```python
from litellm import completion

SYSTEM_PROMPT = """Create a concise description of a product. Respond only in this format.
Title: ...
Category: ...
Brand: ...
Description: ...
Details: ..."""

def preprocess(self, text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]
    response = completion(messages=messages, model=self.model_name, reasoning_effort=self.reasoning_effort)
    return response.choices[0].message.content
```

**Interview takeaway:** Preprocessor = cheap/fast LLM call to normalize input so the pricer model sees consistent format; reduces noise and improves accuracy.

### 6.4 Evaluator — Tester class

**File:** `week6/pricer/evaluator.py`

- **Tester** runs a `predictor(item)` over a dataset; post-process (regex to extract number); compare to `item.price`; color by error; chart (e.g. Plotly).

```python
def run_datapoint(self, i):
    datapoint = self.data[i]
    value = self.predictor(datapoint)
    guess = self.post_process(value)  # regex float from string
    truth = datapoint.price
    error = abs(guess - truth)
    return title, guess, truth, error, color
```

**Interview takeaway:** Same evaluation pattern for DNN, frontier prompt, and fine-tuned model: predictor returns string or float → post_process → compare to ground truth.

### 6.5 Batch / OpenAI fine-tuning

**File:** `week6/pricer/batch.py`

- Build **JSONL** for OpenAI batch/fine-tuning: each line = `{"custom_id": ..., "method": "POST", "url": "/v1/chat/completions", "body": {"model": ..., "messages": [...]}}`.
- Preprocessor-style messages (system + user with product text); completion = normalized description or price (depending on pipeline).
- Use **OpenAI Files API** + **Fine-tuning Jobs API** (e.g. `openai.files.create`, `openai.fine_tuning.jobs.create`).

**Interview takeaway:** Frontier fine-tuning = JSONL of messages (or prompt/completion); upload file, create job, poll until done; then use the new model name in API calls.

---

## Week 7: Fine-Tune Open-Source (QLoRA) — LLaMA + PEFT

**Objective:** Fine-tune **LLaMA 3.2-3B** (or similar) with **QLoRA**: 4-bit base + LoRA adapters; train in Colab; push adapter to Hub; load at inference with `PeftModel.from_pretrained(base_model, adapter_name)`.

### 7.1 Data

- Same **Item** and prompt format as Week 6: `QUESTION + "\n\n" + text + "\n\n" + PREFIX"` → completion = price (e.g. `"123"`).
- Data from Hub: `Item.from_hub(dataset_name)` → train/val/test; then convert to Hugging Face `Dataset` with a `text` or `messages` column for SFTTrainer.

### 7.2 Quantization and base model

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=quant_config,
    device_map="auto"
)
```

**Interview takeaway:** 4-bit = small GPU memory; `device_map="auto"` spreads layers; pad_token = eos_token for generation.

### 7.3 LoRA + SFTTrainer

```python
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

lora_config = LoraConfig(
    r=8, lora_alpha=32, target_modules=["q_proj", "v_proj"], ...
)

trainer = SFTTrainer(
    model=base_model,
    train_dataset=train_data,
    eval_dataset=val_data,
    args=sft_config,
    peft_config=lora_config,
    dataset_text_field="text",  # or formatting_func
)
trainer.train()
trainer.save_model(...)
trainer.push_to_hub(...)
```

**Interview takeaway:** QLoRA = quantized base + LoRA; only adapters are trained; SFTTrainer expects a text field (or formatting function) that matches your prompt format.

### 7.4 Inference — Load base + adapter

```python
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=quant_config, device_map="auto")
model = PeftModel.from_pretrained(base_model, f"{HF_USER}/{RUN_NAME}", revision=REVISION)
# tokenizer.encode(prompt) -> generate(max_new_tokens=5) -> decode -> parse price with regex
```

**Interview takeaway:** At inference you always load **base + PEFT adapter**; same prompt format as training; parse the first few tokens as the price.

---

## Week 8: Deployment (Modal) + Multi-Agent “Price Is Right”

**Objective:** Run the fine-tuned pricer (and optional Llama raw generation) on **Modal**; build **agents** (Specialist, Frontier, DNN, Ensemble, Scanner, Planning, Messaging) and **DealAgentFramework** that scans RSS, prices deals, and alerts on big discounts.

### 8.1 Modal — Hello world

**File:** `week8/hello.py`

- **App** and **Image**; **@app.function** for stateless work.

```python
import modal
app = modal.App("hello")
image = Image.debian_slim().pip_install("requests")

@app.function(image=image)
def hello() -> str:
    import requests
    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    return f"Hello from {data['city']}, {data['region']}, {data['country']}!!"

@app.function(image=image, region="eu")
def hello_europe() -> str:
    # same, runs in EU
```

**Interview takeaway:** Modal = define image (deps), decorate function; run with `with app.run(): hello.local()` or `hello.remote()`; `region=` for geography.

### 8.2 Modal — Llama generation (ephemeral)

**File:** `week8/llama.py`

- **Secrets** for HF token (gated model); **GPU**; load model **inside** the function (cold start each time).

```python
secrets = [modal.Secret.from_name("huggingface-secret")]
@app.function(image=image, secrets=secrets, gpu="T4", timeout=1800)
def generate(prompt: str) -> str:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")
    inputs = tokenizer.encode(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(inputs, max_new_tokens=5)
    return tokenizer.decode(outputs[0])
```

### 8.3 Modal — Pricer class (persistent model + volume)

**File:** `week8/pricer_service2.py`

- **@app.cls** with **@modal.enter()** to load model once per container; **@modal.method()** for `price(description)`.
- **Volume** for HF cache so downloads persist across restarts; **min_containers** to keep instances warm.

```python
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)

@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu="T4",
    volumes={CACHE_DIR: hf_cache_volume},
    min_containers=0,
)
class Pricer:
    @modal.enter()
    def setup(self):
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        self.base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=quant_config, ...)
        self.fine_tuned_model = PeftModel.from_pretrained(self.base_model, FINETUNED_MODEL, revision=REVISION)

    @modal.method()
    def price(self, description: str) -> float:
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        outputs = self.fine_tuned_model.generate(inputs, max_new_tokens=5)
        # decode, split on PREFIX, regex float
        return float(match.group())
```

**Interview takeaway:** Class + `@modal.enter()` = load once; `@modal.method()` = stateless RPC; Volume = persistent cache; `modal.Cls.from_name("pricer-service", "Pricer")` to call from outside.

### 8.4 Agents — Base and Specialist

**File:** `week8/agents/agent.py` and `week8/agents/specialist_agent.py`

- **Base Agent:** name, color, `log(message)` for tracing.

```python
class Agent:
    name: str = ""
    color: str = '\033[37m'
    def log(self, message):
        logging.info(f"[{self.name}] {message}")
```

- **SpecialistAgent:** holds a **Modal Pricer** instance; `price(description)` = remote call.

```python
class SpecialistAgent(Agent):
    name = "Specialist Agent"
    def __init__(self):
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()

    def price(self, description: str) -> float:
        result = self.pricer.price.remote(description)
        return result
```

**Interview takeaway:** Specialist = thin wrapper over Modal; `.remote()` runs on Modal; same interface as other pricer agents.

### 8.5 FrontierAgent — RAG for pricing

**File:** `week8/agents/frontier_agent.py`

- **Chroma** collection of products (documents + metadata with price); **SentenceTransformer** to embed description; query collection for **top-5 similar** products and their prices; build context string; call **OpenAI** for price.

```python
def find_similars(self, description: str):
    vector = self.model.encode([description])
    results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
    documents = results["documents"][0]
    prices = [m["price"] for m in results["metadatas"][0]]
    return documents, prices

def price(self, description: str) -> float:
    documents, prices = self.find_similars(description)
    message = f"Estimate the price...\n\n{description}\n\n" + self.make_context(documents, prices)
    response = self.client.chat.completions.create(model=self.MODEL, messages=[{"role": "user", "content": message}], ...)
    return self.get_price(response.choices[0].message.content)
```

**Interview takeaway:** Frontier pricer = vector search over product catalog (RAG) + LLM with “similar products and prices” as context; no fine-tuning.

### 8.6 EnsembleAgent — Preprocess + weighted average

**File:** `week8/agents/ensemble_agent.py`

- **Preprocessor** (LiteLLM) rewrites description; **Specialist** (Modal), **Frontier** (RAG+GPT), **NeuralNetwork** (DNN) each return a price; **fixed weights** (e.g. 0.8, 0.1, 0.1); return weighted sum.

```python
def price(self, description: str) -> float:
    rewrite = self.preprocessor.preprocess(description)
    specialist = self.specialist.price(rewrite)
    frontier = self.frontier.price(rewrite)
    neural_network = self.neural_network.price(rewrite)
    combined = frontier * 0.8 + specialist * 0.1 + neural_network * 0.1
    return combined
```

**Interview takeaway:** Ensemble = same input (after preprocess) to multiple models; combine with fixed or learned weights; improves robustness.

### 8.7 ScannerAgent — RSS + structured output

**File:** `week8/agents/scanner_agent.py` and `week8/agents/deals.py`

- **ScrapedDeal:** fetch RSS (feedparser), scrape page (BeautifulSoup), truncate; list of deals.
- **Deal** (Pydantic): `product_description`, `price`, `url`.
- **DealSelection** (Pydantic): `deals: List[Deal]`.
- **ScannerAgent:** `fetch_deals(memory)` → filter by seen URLs; build user prompt (list of deal text); call **OpenAI** with **response_format=DealSelection**; parse to get 5 deals with price > 0.

```python
result = self.openai.chat.completions.parse(
    model=self.MODEL,
    messages=[{"role": "system", "content": self.SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
    response_format=DealSelection,
    reasoning_effort="minimal",
)
result = result.choices[0].message.parsed
result.deals = [d for d in result.deals if d.price > 0]
```

**Interview takeaway:** Structured output = Pydantic model + `.parse()` or `response_format`; ensures valid JSON and types; use for extraction (deals, prices).

### 8.8 PlanningAgent and DealAgentFramework

**File:** `week8/agents/planning_agent.py` and `week8/deal_agent_framework.py`

- **PlanningAgent:** owns Scanner, Ensemble, Messaging. `plan(memory)` = scan → for each deal run `ensemble.price(deal.product_description)` → discount = estimate - deal.price → sort by discount → if best > threshold, `messenger.alert(best)` → return best **Opportunity** (deal + estimate + discount).
- **DealAgentFramework:** Chroma client (products collection), **memory** = list of Opportunity (read/write JSON); `run()` = init planner → `planner.plan(memory)` → append result to memory, write file.

```python
# PlanningAgent
def plan(self, memory):
    selection = self.scanner.scan(memory=memory)
    if selection:
        opportunities = [self.run(deal) for deal in selection.deals[:5]]
        opportunities.sort(key=lambda opp: opp.discount, reverse=True)
        best = opportunities[0]
        if best.discount > self.DEAL_THRESHOLD:
            self.messenger.alert(best)
        return best if best.discount > self.DEAL_THRESHOLD else None
```

**Interview takeaway:** Planner = orchestration (scan → price → rank → notify); Framework = state (memory) + single entry point `run()` that calls the planner.

---

## Modules used in notebooks and scripts (by area)

Below is a **detailed list of the modules and libraries** used for **preprocessing, training, evaluation, and deployment** across the course. Use this to answer "what did you use for X?" in interviews.

---

### RAG (Week 5) — Document preprocessing, retrieval, answer, evaluation

| Purpose | Module / library | What it does in the code |
|--------|-------------------|---------------------------|
| **Load documents** | `langchain_community.document_loaders.DirectoryLoader`, `TextLoader` | Load markdown (or text) from folders; `glob="**/*.md"`, optional `encoding="utf-8"`. |
| **Chunking** | `langchain_text_splitters.RecursiveCharacterTextSplitter` | Split docs into chunks: `chunk_size=2000`, `chunk_overlap=200`. |
| **Embeddings** | `langchain_huggingface.HuggingFaceEmbeddings` | Local embeddings, e.g. `model_name="all-MiniLM-L6-v2"`. Optional: `langchain_openai.OpenAIEmbeddings` with `text-embedding-3-large`. |
| **Vector store** | `langchain_chroma.Chroma` | Store embeddings; `from_documents(chunks, embedding=..., persist_directory=...)`; `as_retriever(search_kwargs={"k": k})` for search. |
| **Keyword search** | `rank_bm25.BM25Okapi` | Lexical search: tokenize docs (e.g. `.lower().split()`), `BM25Okapi(tokenized_docs)`, `get_scores(tokenized_query)`. |
| **Reranking** | `sentence_transformers.CrossEncoder` | Rerank (query, doc) pairs: `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")`, `predict(pairs)`. |
| **LLM for answer / rewrite** | `langchain_openai.ChatOpenAI` | `ChatOpenAI(temperature=0, model_name=...)`, `invoke(messages)`; messages = `SystemMessage`, `HumanMessage`, `convert_to_messages(history)`. |
| **Pro implementation** | `litellm.completion` | One API for multiple providers; `completion(messages=..., model=...)`. |
| **Retries** | `tenacity.retry`, `wait_exponential` | Decorate API calls to retry on failure. |
| **Structured eval** | `pydantic.BaseModel`, `Field` | Define `RetrievalEval`, `AnswerEval` for LLM-as-judge `response_format`. |
| **Eval metrics** | Built-in `math`, loops | MRR = 1/rank of first relevant doc; nDCG = DCG/IDCG; keyword coverage = % keywords in top-k. |
| **App** | `gradio` (`gr.Blocks`, `gr.Chatbot`, `gr.Textbox`, `.submit().then()`) | Chat UI; call `answer_question`, show context in second column. |

---

### Week 6 — Data loading, preprocessing, DNN training, evaluation, OpenAI fine-tuning

| Purpose | Module / library | What it does in the code |
|--------|-------------------|---------------------------|
| **Data model** | `pydantic.BaseModel` | `Item`: title, category, price, full, prompt; `make_prompt()`, `model_dump()`, `model_validate()`. |
| **Datasets** | `datasets.load_dataset`, `Dataset`, `DatasetDict` | Load from Hugging Face (e.g. Amazon-Reviews); `Item.from_hub(dataset_name)`; push with `DatasetDict(...).push_to_hub()`. |
| **Data loading** | `week6/pricer/loaders.ItemLoader` | `load_dataset("McAuley-Lab/Amazon-Reviews-2023", ...)`; chunk dataset; `ProcessPoolExecutor` + `parse()` per chunk to build list of `Item`. |
| **Parsing / scrub** | `week6/pricer/parser` | `parse(datapoint, category)` → scrub (remove part numbers, limit length), filter MIN_CHARS/MIN_PRICE/MAX_PRICE, return `Item`. |
| **Preprocessing (LLM)** | `litellm.completion` | Normalize raw product text: system + user messages, `completion(messages=..., model="groq/openai/gpt-oss-20b", reasoning_effort="low")`; used in `Preprocessor.preprocess()`. |
| **DNN text to vector** | `sklearn.feature_extraction.text.HashingVectorizer` | `HashingVectorizer(n_features=5000, stop_words="english", binary=True)`; `fit_transform(train_documents)` → sparse matrix → NumPy → PyTorch tensor. |
| **DNN model** | `torch`, `torch.nn` | `nn.Linear`, `nn.LayerNorm`, `nn.ReLU`, `nn.Dropout`; custom `ResidualBlock` and `DeepNeuralNetwork`; `TensorDataset`, `DataLoader`. |
| **DNN training** | `torch.optim.AdamW`, `torch.optim.lr_scheduler.CosineAnnealingLR` | Optimizer and scheduler; `loss.backward()`, `optimizer.step()`, `clip_grad_norm_()`; log-price normalization (mean/std). |
| **Evaluation** | `sklearn.metrics.mean_squared_error`, `r2_score` | Compare predicted vs true price; also custom `Tester` with `run_datapoint`, `post_process` (regex), color bands, Plotly charts. |
| **Visualization** | `plotly.express`, `plotly.graph_objects`, `pandas` | Build DataFrames (truth, guess, title); `px.scatter`, `go.Figure` for evaluator charts. |
| **Parallel load** | `concurrent.futures.ProcessPoolExecutor`, `tqdm` | Parallel parsing in loaders; `pool.map(self.from_chunk, self.chunk_generator())`. |
| **OpenAI batch / FT** | `openai` (files, fine_tuning), `json` | Build JSONL (custom_id, method, url, body with messages); upload file; create fine-tuning job (used in batch.py / notebooks). |
| **Groq (optional)** | `groq.Groq` | Alternative for preprocessor or batch calls in some scripts. |

---

### Week 7 — Open-source fine-tuning (QLoRA) in notebooks

| Purpose | Module / library | What it does in the code |
|--------|-------------------|---------------------------|
| **Env / Hub** | `dotenv.load_dotenv`, `huggingface_hub.login` | Load `HF_TOKEN`; `login(hf_token)` so Colab can push/pull private datasets and adapters. |
| **Data** | `datasets.load_dataset`, `Dataset`, `DatasetDict` | Load train/val/test from Hub (same Item format as Week 6); convert to HF `Dataset` with `text` or `messages` column for SFT. |
| **Tokenizer** | `transformers.AutoTokenizer` | `AutoTokenizer.from_pretrained(BASE_MODEL)`; set `pad_token = eos_token`, `padding_side = "right"`. |
| **Quantization** | `transformers.BitsAndBytesConfig` | 4-bit: `load_in_4bit=True`, `bnb_4bit_use_double_quant=True`, `bnb_4bit_compute_dtype=torch.float16`, `bnb_4bit_quant_type="nf4"`. |
| **Base model** | `transformers.AutoModelForCausalLM` | `from_pretrained(BASE_MODEL, quantization_config=quant_config, device_map="auto")`. |
| **LoRA** | `peft.LoraConfig`, `peft.PeftModel` | `LoraConfig(r=8, lora_alpha=32, target_modules=["q_proj","v_proj"], ...)`; at inference `PeftModel.from_pretrained(base_model, adapter_name, revision=...)`. |
| **Training** | `trl.SFTTrainer`, `trl.SFTConfig` | `SFTTrainer(model=base_model, train_dataset=..., peft_config=lora_config, dataset_text_field="text", ...)`; optional `DataCollatorForCompletionOnlyLM` for response-only loss. |
| **Training args** | `transformers.TrainingArguments` | Epochs, batch size, LR, warmup, logging, eval strategy, save strategy, bf16/fp16, push_to_hub. |
| **Eval (metrics)** | `sklearn.metrics.mean_squared_error`, `r2_score`, `mean_absolute_error` | Evaluate predicted price vs ground truth on val/test; sometimes `transformers.Trainer` + custom compute_metrics. |
| **Viz** | `matplotlib.pyplot` | Plot loss curves, error distributions in notebooks. |
| **Inference** | `transformers.set_seed` | `set_seed(42)`; encode prompt → `model.generate(max_new_tokens=5)` → decode → regex to extract price. |

---

### Week 8 — Deployment (Modal), agents, Chroma, Gradio

| Purpose | Module / library | What it does in the code |
|--------|-------------------|---------------------------|
| **Modal** | `modal`, `modal.Image`, `modal.Volume`, `modal.Secret` | `App("name")`, `Image.debian_slim().pip_install(...)`, `@app.function` / `@app.cls`, `@modal.enter()`, `@modal.method()`, `Volume.from_name(...)`, `Secret.from_name("huggingface-secret")`. |
| **Modal client** | `modal.Cls.from_name`, `modal.Function.from_name` | From notebook or another app: `Pricer = modal.Cls.from_name("pricer-service", "Pricer")`, then `pricer.price.remote(description)`. |
| **Transformers on Modal** | `transformers`, `peft` | Same as Week 7: `AutoTokenizer`, `AutoModelForCausalLM`, `BitsAndBytesConfig`, `PeftModel.from_pretrained` inside `@modal.enter()` or inside `@app.function`. |
| **Chroma** | `chromadb.PersistentClient` | `PersistentClient(path=DB)`; `get_or_create_collection("products")`; `collection.query(query_embeddings=..., n_results=5)`; store documents + metadatas (e.g. price). |
| **Embeddings (agents)** | `sentence_transformers.SentenceTransformer` | `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")`; `model.encode([description])` for FrontierAgent RAG. |
| **LLM API** | `openai.OpenAI` | `client.chat.completions.create(model=..., messages=..., seed=42, reasoning_effort="none")`; Scanner uses `.parse(..., response_format=DealSelection)`. |
| **Structured output** | `pydantic.BaseModel`, `Field` | `Deal`, `DealSelection`, `Opportunity`, `ScrapedDeal`; used in `deals.py` and ScannerAgent. |
| **RSS / scraping** | `feedparser`, `requests`, `bs4.BeautifulSoup` | Fetch RSS feeds; scrape deal pages; extract title, summary, details, features in `deals.py`. |
| **Preprocessor (agent)** | `litellm.completion` | Same as Week 6: normalize product text in EnsembleAgent before calling specialist/frontier/DNN. |
| **DNN inference** | `week8/agents/deep_neural_network.DeepNeuralNetworkInference` | Load saved `.pth`; HashingVectorizer + PyTorch model; used by NeuralNetworkAgent. |
| **Visualization** | `sklearn.manifold.TSNE`, `numpy`, `plotly.graph_objects` | t-SNE on Chroma embeddings for product plot in DealAgentFramework; Gradio + Plotly in price_is_right UI. |
| **App** | `gradio`, `logging`, `queue`, `threading` | Price Is Right UI; log reformatting; optional queue/threading for async updates. |

---

### One-line "what module for what" (interview cheat sheet)

- **Document load:** `DirectoryLoader` + `TextLoader` (LangChain).
- **Chunking:** `RecursiveCharacterTextSplitter`.
- **Embeddings:** `HuggingFaceEmbeddings` or `OpenAIEmbeddings`; vector store = `Chroma`.
- **Keyword search:** `rank_bm25.BM25Okapi`.
- **Rerank:** `sentence_transformers.CrossEncoder`.
- **Product text normalization:** `litellm.completion` (or Groq) in Preprocessor.
- **Data:** `pydantic` Item, `datasets.load_dataset`, `DatasetDict.push_to_hub` / `from_hub`.
- **DNN:** `HashingVectorizer` → `torch` (Linear, LayerNorm, DataLoader, AdamW, CosineAnnealingLR).
- **QLoRA:** `BitsAndBytesConfig`, `AutoModelForCausalLM`, `LoraConfig`, `SFTTrainer`, `PeftModel`.
- **Deployment:** `modal` (Image, Volume, Secret, @app.cls, @modal.enter, @modal.method, Cls.from_name).
- **Agents:** `chromadb`, `SentenceTransformer`, `openai`, `pydantic`, `feedparser`, `BeautifulSoup`.

---


## Quick “Code Path” Recap for Interviews

| Week | One-line code idea |
|------|--------------------|
| 1 | Scraper: BeautifulSoup body text → messages → `ollama.chat.completions.create`. |
| 2 | Same messages; swap client (OpenAI/Anthropic); add streaming and structured output later. |
| 3 | HF pipelines + synthetic data generation for training. |
| 4 | Gradio + multi-model (get_openai_client, get_claude_client) + system/user prompts. |
| 5 | Ingest: DirectoryLoader → RecursiveCharacterTextSplitter → Chroma + BM25. Answer: rewrite → hybrid → rerank → system+context+user → llm.invoke. Eval: MRR/nDCG + LLM judge with response_format. |
| 6 | Item (Pydantic), parser scrub, preprocessor (LiteLLM), Tester, JSONL batch for OpenAI fine-tuning. |
| 7 | BitsAndBytesConfig 4-bit + AutoModelForCausalLM + LoraConfig + SFTTrainer; PeftModel.from_pretrained at inference. |
| 8 | Modal: @app.function / @app.cls + @modal.enter + @modal.method; Volume; modal.Cls.from_name. Agents: Specialist (Modal), Frontier (Chroma + GPT), Ensemble (preprocess + weights), Scanner (RSS + parse(DealSelection)), Planning (orchestrate), Framework (memory + run). |

Use this doc to **walk through the repo** and to **rehearse "how we built it"** in interviews, with concrete snippets above as the code you remember.

---

## File map (where to open code)

| Week | Key files to open |
|------|-------------------|
| 1 | `week1/scraper.py`, `week1/solution.py` |
| 2 | `week2/scraper.py`, notebooks for API calls |
| 4 | `week4/app.py` |
| 5 | `week5/implementation/ingest.py`, `answer.py`; `week5/evaluation/eval.py`; `week5/app.py` |
| 6 | `week6/pricer/items.py`, `parser.py`, `preprocessor.py`, `evaluator.py`, `batch.py` |
| 7 | `week7/day2.ipynb`, `day3 and 4.ipynb`, `day5.ipynb`; community notebooks for SFTTrainer/PeftModel |
| 8 | `week8/hello.py`, `llama.py`, `pricer_service2.py`; `week8/agents/agent.py`, `specialist_agent.py`, `frontier_agent.py`, `ensemble_agent.py`, `scanner_agent.py`, `planning_agent.py`, `deals.py`; `week8/deal_agent_framework.py` |

For concepts, libraries, and interview Q&A, use **LLM_ENGINEERING_COURSE_REFERENCE.md**.
