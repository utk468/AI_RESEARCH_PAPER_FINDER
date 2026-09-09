# AI Research Paper Finder 🔬

A production-quality AI application that finds, analyzes, and summarizes academic research papers using a **12-node LangGraph pipeline**, FastAPI backend, MongoDB, FAISS vector search, and a clean, modern SaaS pure white UI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **LLM Query Understanding** | Extracts research topics, keywords, subtopics, and search intent |
| **Query Expansion** | Generates synonyms, Boolean queries, and academic search variants |
| **Multi-Engine Search** | Tavily, Exa, SerpAPI, Google CSE, or Bing (configurable) |
| **Academic Filtering** | arXiv, IEEE, ACM, Springer, Semantic Scholar, OpenReview + more |
| **Metadata Extraction** | Title, authors, year, DOI, abstract, citations via LLM |
| **PDF Download & Parse** | PyMuPDF extraction with section/figure/table detection |
| **BAAI/bge-large-en-v1.5 Embeddings** | 1024-dim semantic embeddings stored in FAISS |
| **RAG Summarization** | Grounded paper summaries with no hallucinations |
| **Research Gap Analysis** | Trends, challenges, thesis ideas, novel directions |
| **Recommendations** | Related papers, datasets, authors, conferences |
| **RAG Chat** | Ask questions about any paper, answered from retrieved chunks |
| **MongoDB Storage** | Papers, history, embeddings, bookmarks, feedback |
| **Clean Pure White UI** | Ultra-crisp SaaS white aesthetic with vibrant purple accents |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd RESEARCH_PAPER_FINDER
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start MongoDB

```bash
# Make sure MongoDB is running locally
mongod --dbpath ./data/db
```

### 4. Run the Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open the Frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
# Python simple server
python -m http.server 3000 --directory frontend

# Then visit: http://localhost:3000
```

---

## 🔑 API Keys Required

| Service | Purpose | Get Key |
|---|---|---|
| **GROQ / OpenAI / Gemini** | LLM (choose one) | [groq.com](https://groq.com), [platform.openai.com](https://platform.openai.com), [ai.google.dev](https://ai.google.dev) |
| **Tavily** | Academic web search | [tavily.com](https://tavily.com) |
| **MongoDB** | Database | Local or [atlas.mongodb.com](https://atlas.mongodb.com) |

Optional: Exa, SerpAPI, Google CSE, or Bing for alternative search engines.

---

## ⚙️ Configuration

All settings live in `.env`:

```env
LLM_PROVIDER=groq           # openai | gemini | groq
GROQ_API_KEY=gsk_...

SEARCH_PROVIDER=tavily      # tavily | exa | serpapi | google | bing
TAVILY_API_KEY=tvly-...

MONGODB_URL=mongodb://localhost:27017
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

---

## 🏗️ Architecture

```
User Query
    ↓
Query Understanding (LLM extracts intent)
    ↓
Query Expansion (synonyms, Boolean queries)
    ↓
Web Search (Tavily / Exa / SerpAPI / Google / Bing)
    ↓
Academic Filter (domain whitelist)
    ↓
Metadata Extraction (LLM from page content)
    ↓
PDF Fetch (async download)
    ↓
PDF Parsing (PyMuPDF — text, sections, figures)
    ↓
Embedding (BAAI/bge-large-en-v1.5 → FAISS)
    ↓
RAG Retrieval (cosine similarity top-K)
    ↓
Summarization (grounded, no hallucinations)
    ↓
Research Gap Analysis (cross-paper LLM analysis)
    ↓
Recommendations (papers, datasets, authors)
    ↓
Dashboard (Clean White + Purple SaaS UI)
```

---

## 📂 Project Structure

```
RESEARCH_PAPER_FINDER/
├── .env.example
├── README.md
├── frontend/
│   ├── index.html          # Landing / search page
│   ├── dashboard.html      # Results dashboard
│   ├── paper.html          # Paper detail page
│   ├── css/
│   │   ├── style.css       # Clean white + purple theme
│   │   ├── components.css  # UI components
│   │   ├── dashboard.css   # Dashboard layout & empty state
│   │   └── responsive.css  # Mobile breakpoints
│   └── js/
│       ├── api.js          # API client
│       ├── app.js          # Page router + logic
│       ├── components.js   # Card builders
│       ├── dashboard.js    # Dashboard logic & source chip filter
│       ├── chat.js         # RAG chat
│       └── search.js       # Search utilities
└── backend/
    ├── main.py             # FastAPI app
    ├── config.py           # Settings (pydantic-settings)
    ├── requirements.txt
    ├── routers/
    │   ├── search.py       # POST /search, GET /history
    │   ├── papers.py       # GET /paper/{id}, GET /related/{id}
    │   ├── chat.py         # POST /chat
    │   ├── bookmarks.py    # POST /bookmark, GET /bookmarks
    │   ├── feedback.py     # POST /feedback
    │   └── health.py       # GET /health
    ├── services/
    │   ├── search_service.py
    │   ├── paper_service.py
    │   └── llm_service.py
    ├── langgraph/
    │   ├── state.py        # GraphState TypedDict
    │   ├── graph.py        # 12-node StateGraph
    │   └── nodes/
    │       ├── query_understanding.py
    │       ├── query_expansion.py
    │       ├── web_search.py
    │       ├── academic_filter.py
    │       ├── metadata.py
    │       ├── pdf_fetch.py
    │       ├── pdf_parser.py
    │       ├── embedding.py
    │       ├── retrieval.py
    │       ├── summarizer.py
    │       ├── research_gap.py
    │       └── recommendation.py
    ├── models/paper.py
    ├── schemas/{requests,responses}.py
    ├── database/{mongodb,faiss_store}.py
    ├── prompts/templates.py
    └── utils/{logger,helpers}.py
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/search` | Run full pipeline |
| `GET`  | `/api/search/history` | Recent searches |
| `GET`  | `/api/paper/{id}` | Paper details |
| `POST` | `/api/paper/summary` | Generate summary |
| `GET`  | `/api/paper/related/{id}` | Related papers |
| `POST` | `/api/chat` | RAG chat with paper |
| `POST` | `/api/bookmarks` | Bookmark a paper |
| `GET`  | `/api/bookmarks` | List bookmarks |
| `POST` | `/api/feedback` | Submit rating |
| `GET`  | `/health` | Health check |

---

## 🎨 UI Features

- **Pure White SaaS Theme** (`#ffffff` background) with vibrant purple accent highlights
- **Source Pill Tag Chips** for arXiv, IEEE Xplore, ACM DL, Springer, and Semantic Scholar (no square checkbox inputs)
- **Modern Empty State Card** with centered icon badge, title, description, and quick action buttons ("Reset Filters" and "New Search")
- **Pipeline Progress Visualization** (12-step real-time pipeline status)
- **Paper Cards** with similarity scores, metadata, keywords, and citations
- **Tabbed Dashboard** (Papers / Research Gaps / Recommendations)
- **RAG-Powered Chat** with thinking animation and KaTeX math equation rendering
- **Sort & Filter Sidebar** (year range, source chip tags, sort order)
- **Export Results** as formatted JSON
- **Responsive** mobile & desktop design

---

## 📋 Requirements

- Python 3.10+
- MongoDB 6.0+
- 4GB+ RAM (for embedding model)
- GPU optional (CPU inference supported)

---

## 🔧 Troubleshooting

**Backend won't start?**
- Check `.env` has valid API keys
- Ensure MongoDB is running: `mongod --dbpath ./data/db`

**Embeddings slow?**
- First run downloads `BAAI/bge-large-en-v1.5` (~1.3GB)
- CPU inference is slower; use GPU if available

**No papers found?**
- Verify `TAVILY_API_KEY` or your chosen search provider is valid
- Check `LOG_LEVEL=DEBUG` for detailed pipeline logs

---

## 📄 License

MIT License — free to use and modify.
