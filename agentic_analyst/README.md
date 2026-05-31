# Agentic AI Data Analyst

A production-ready multi-agent AI system for natural language data analysis.
Upload CSVs or Excel files and interact with your data through 7 specialist AI agents.

---

## Quick Start

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | |
| MySQL | 8.x | Local or Docker |
| Ollama | latest | Local LLM runtime |
| Node / Docker | — | For Docker Compose path |

### 1. Install Ollama and pull the model

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
```

### 2. Set up MySQL

```sql
CREATE DATABASE analyst_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 4. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Start the frontend (new terminal)

```bash
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser.

---

## Docker Compose (all services)

```bash
docker compose up -d

# Pull the LLM model into the Ollama container
docker exec analyst_ollama ollama pull llama3
```

Services:
- **MySQL**: `localhost:3306`
- **Ollama**: `localhost:11434`
- **FastAPI backend**: `localhost:8000` — API docs at `/docs`
- **Streamlit frontend**: `localhost:8501`

---

## Architecture

```
User
 └─ Streamlit Frontend (5 pages)
     └─ FastAPI Backend (/api/*)
         └─ Router Agent  ← classifies intent
             ├─ SQL Agent           → pandasql execution
             ├─ Visualization Agent → Plotly charts
             ├─ Insight Agent       → trend + anomaly analysis
             ├─ Cleaning Agent      → missing/duplicate/outlier fixes
             ├─ Profiling Agent     → statistical overview
             └─ Report Agent        → ReportLab PDF
         └─ Data Layer
             ├─ MySQL (metadata + history)
             ├─ Pandas (in-memory DataFrames)
             └─ ChromaDB (vector search, future)
         └─ Ollama (Llama 3 — local LLM)
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/` | Upload CSV/Excel file |
| GET | `/api/upload/list` | List all datasets |
| POST | `/api/query/` | NL query → router agent |
| GET | `/api/profile/{id}` | Full data profile |
| POST | `/api/clean/{id}` | Run data cleaner |
| POST | `/api/visualize/` | Generate chart |
| POST | `/api/report/generate` | Generate PDF report |
| GET | `/api/report/list` | List past reports |
| POST | `/api/chat/` | Multi-turn chat |
| GET | `/api/chat/history/{id}` | Chat history |

Interactive API docs: **http://localhost:8000/docs**

---

## Project Structure

```
agentic_analyst/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── api/routes/
│   │   ├── upload.py              # File upload + dataset listing
│   │   ├── query.py               # NL query dispatcher
│   │   ├── profile.py             # Data profiling endpoint
│   │   ├── clean.py               # Data cleaning endpoint
│   │   ├── visualize.py           # Chart generation endpoint
│   │   ├── report.py              # PDF report endpoints
│   │   └── chat.py                # Multi-turn chat endpoint
│   ├── agents/
│   │   ├── router_agent.py        # Intent classification + dispatch
│   │   ├── sql_agent.py           # NL → SQL → results
│   │   ├── visualization_agent.py # Chart type selection + Plotly
│   │   ├── insight_agent.py       # Trends, KPIs, anomalies
│   │   ├── cleaning_agent.py      # Data quality fixes
│   │   ├── profiling_agent.py     # Statistical profile
│   │   └── report_agent.py        # ReportLab PDF assembly
│   ├── database/
│   │   └── connection.py          # SQLAlchemy engine + session
│   ├── models/
│   │   └── orm_models.py          # ORM table definitions
│   ├── schemas/
│   │   └── schemas.py             # Pydantic request/response models
│   └── services/
│       ├── llm_service.py         # Ollama LLM factory
│       └── dataset_service.py     # DataFrame cache + loader
├── frontend/
│   ├── app.py                     # Home page + upload
│   └── pages/
│       ├── 01_Explorer.py         # Dataset profile viewer
│       ├── 02_AI_Chat.py          # Conversational chat UI
│       ├── 03_Dashboard.py        # KPIs + charts + insights
│       └── 04_Reports.py          # PDF report generation
├── uploads/                       # Uploaded files
├── reports/                       # Generated PDFs
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```

---

## Agent Details

### Router Agent
Classifies user intent into: `sql | visualization | insight | cleaning | profiling | report | general`
Uses a LangChain LLM chain with a classification prompt and regex-safe output parsing.

### SQL Agent
Builds schema description from the DataFrame, generates SELECT-only SQL via Llama 3,
executes against the in-memory DataFrame using `pandasql`, and returns results + explanation.

### Visualization Agent
Selects chart type (line/bar/pie/scatter/histogram/heatmap/box) based on data shape and query.
Returns a Plotly figure serialised as JSON for direct use in Streamlit.

### Insight Agent
Computes descriptive statistics and IQR-based anomaly detection, then feeds the summary
to Llama 3 to generate actionable business insights in bullet form.

### Cleaning Agent
Standardises column names, removes duplicates, imputes missing values (median/mode),
attempts numeric type coercion, and caps outliers using the IQR method.

### Profiling Agent
Generates per-column stats (mean, std, min, max, null %, unique count), a correlation
heatmap, and distribution histograms — all as Plotly JSON.

### Report Agent
Assembles a multi-section PDF with ReportLab Platypus: dataset overview, quality summary,
AI insights, embedded chart images (via kaleido), and statistical summary tables.

---

## Future Enhancements

- Multi-user authentication (JWT + Keycloak)
- Voice analytics assistant (Whisper STT)
- Forecasting agent (Prophet / statsmodels)
- AutoML agent (PyCaret)
- RAG over uploaded PDFs (ChromaDB + embeddings)
- Multi-dataset JOIN support
- Real-time streaming dashboards (WebSockets)
- Agent memory (LangChain ConversationBufferMemory)
- CrewAI multi-agent orchestration
- LangGraph workflow graphs
