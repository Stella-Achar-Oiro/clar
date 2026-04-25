# CLAR Backend

FastAPI + LangGraph backend for CLAR — Clinical Lab Analysis Report.

**Live:** https://clar-608805582585.us-central1.run.app

**GCP Console:** https://console.cloud.google.com/run/detail/us-central1/clar/metrics?project=stella-cyber-analyzer

**LangSmith:** https://smith.langchain.com (project: `clar-production`)

---

## Stack

- **Python 3.11**, **FastAPI** — REST API + SSE streaming
- **LangGraph** — multi-node pipeline with typed state
- **Anthropic Claude Sonnet 4.6** — LLM for extraction, flagging, explanation, advice, chat
- **spaCy `en_core_web_lg`** — local NER for de-identification (no PHI sent externally before anonymisation)
- **Pydantic v2** — request/response validation and settings
- **Loguru** — structured JSON logging in production
- **Prometheus** — metrics via `/metrics`
- **LangSmith** — full LLM trace observability

---

## Structure

```
app/
├── agents/
│   ├── pipeline.py         # LangGraph graph definition and compilation
│   ├── deid_agent.py       # spaCy NER de-identification node
│   ├── extract_agent.py    # Finding extraction node
│   ├── flag_agent.py       # Urgency flagging node
│   ├── explain_agent.py    # Lay-language explanation node
│   └── advisor_agent.py    # Doctor question generation node
├── api/routes/
│   ├── upload.py           # POST /api/upload — runs pipeline, stores session
│   ├── chat.py             # POST /api/chat (single-turn) + /api/chat/stream (SSE)
│   ├── health.py           # GET /health
│   └── metrics.py          # GET /metrics (Prometheus)
├── models/
│   ├── report.py           # CLARState TypedDict, Pydantic request/response models
│   └── __init__.py
├── observability/
│   ├── logging.py          # configure_logging() — JSON in prod, coloured in dev
│   └── metrics.py          # Prometheus counters and histograms
├── prompts/
│   ├── explain.py          # System + user prompt for explain_agent
│   ├── flag.py             # System + user prompt for flag_agent
│   └── advisor.py          # System + user prompt for advisor_agent
├── services/
│   ├── deid.py             # spaCy pipeline wrapper
│   ├── extractor.py        # PDF text extraction (pdfminer)
│   ├── llm.py              # Anthropic client wrapper (call_llm, retry, token logging)
│   └── session.py          # In-memory TTL session store (30 min default)
├── config.py               # Pydantic settings (reads .env / Secret Manager env vars)
└── main.py                 # FastAPI app, routers, exception handlers, LangSmith init
```

---

## Pipeline

```
POST /api/upload
       │
       ▼
  extract_text (PDF or plain text)
       │
       ▼
  LangGraph pipeline
  ┌─────────────────────────────────────────┐
  │  deid_agent   → strip PII with spaCy   │
  │       │                                 │
  │  extract_agent → find lab/rad findings  │
  │       │                                 │
  │  flag_agent   → assign urgency levels  │
  │       │                                 │
  │  explain_agent → lay-language per item │
  │       │                                 │
  │  advisor_agent → 3–5 doctor questions  │
  └─────────────────────────────────────────┘
       │
       ▼
  store session (report_id → state, TTL 30 min)
       │
       ▼
  return UploadResponse (findings, verdict, questions, report_id)
```

**State:** `CLARState` TypedDict flows through every node. Nodes return partial state updates; LangGraph merges them. If any node sets `error`, the error node short-circuits the rest of the pipeline.

---

## LLM interaction

All LLM calls go through `services/llm.py → call_llm()`:

- Single Anthropic client instance (module-level)
- Structured JSON output: system prompt includes JSON schema, `json.loads()` with markdown fence stripping
- Temperature tuned per node: 0.1 (extraction), 0.2 (flagging), 0.3 (explanation, chat), 0.4 (advice)
- Token usage logged to `clar_llm_tokens_total` Prometheus counter per agent and direction

LangSmith tracing is enabled at startup in `main.py` when `LANGSMITH_API_KEY` is present — every pipeline run appears as a trace in the `clar-production` project.

---

## Observability

| Signal | Implementation |
|---|---|
| LLM traces | LangSmith — full prompt/response, latency, token counts per run |
| Request metrics | `clar_requests_total{report_type, status}` |
| Pipeline latency | `clar_pipeline_duration_seconds` histogram |
| Per-agent latency | `clar_agent_duration_seconds{agent_name}` histogram |
| Token usage | `clar_llm_tokens_total{agent_name, direction}` counter |
| PII removed | `clar_deid_entities_total` counter |
| Errors | `clar_errors_total{error_type}` counter |
| Logs | Structured JSON (prod) / coloured (dev) via Loguru — metadata only, never raw text |

---

## Running locally

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m spacy download en_core_web_lg
uvicorn app.main:app --reload
# → http://localhost:8000
```

Create `.env` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls__...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
ENVIRONMENT=development
```

---

## Testing

```bash
pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=term-missing
```

80% coverage required. CI runs this on every PR against a pinned `ANTHROPIC_API_KEY=sk-ant-test-key` so no real API calls are made in CI.

---

## API reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Liveness check — returns `{"status": "ok"}` |
| POST | `/api/upload` | Clerk JWT | Upload PDF or text, returns full analysis |
| POST | `/api/chat` | Clerk JWT | Single-turn Q&A on a report session |
| POST | `/api/chat/stream` | Clerk JWT | Streaming Q&A via SSE |
| GET | `/metrics` | none | Prometheus metrics |
