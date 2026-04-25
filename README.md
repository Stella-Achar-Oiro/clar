# CLAR — Clinical Lab Analysis Report

CLAR is a medical report analysis tool that takes lab results, radiology reports, or discharge summaries and explains them in plain English. It de-identifies personal details, extracts findings, flags anything outside the normal range, and lets patients ask follow-up questions via a real-time streaming chat.

**Live:** https://clar-608805582585.us-central1.run.app

**GCP Console:** https://console.cloud.google.com/run/detail/us-central1/clar/metrics?project=stella-cyber-analyzer

**GitHub:** https://github.com/Stella-Achar-Oiro/clar

---

## What it does

1. Upload a PDF or plain-text medical report
2. CLAR de-identifies personal details (names, DOB, MRN) using spaCy NER
3. A LangGraph pipeline extracts findings, flags urgency, explains each result in lay language, and generates doctor questions
4. Results page shows all findings with urgency levels (normal / watch / urgent), a verdict summary, and suggested questions
5. Ask follow-up questions via the built-in chat — answers stream back token-by-token in real time

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, LangGraph, Anthropic Claude Sonnet 4.6 |
| Frontend | Next.js 14 (Pages Router), TypeScript, Tailwind CSS, Clerk auth |
| Observability | LangSmith (LLM tracing), Prometheus metrics, structured Loguru logging |
| Infra | Google Cloud Run v2, Artifact Registry, Secret Manager |
| CI/CD | GitHub Actions + Workload Identity Federation (keyless GCP auth) |
| IaC | Terraform (Cloud Run, Artifact Registry, Secret Manager) |

---

## Architecture

```
Browser (Next.js static export)
        │  HTTPS
        ▼
  FastAPI (Cloud Run)
        │
        ├── POST /api/upload ──► LangGraph pipeline
        │                              │
        │                    ┌─────────┴──────────┐
        │                    ▼                    ▼
        │               deid_agent          (parallel future)
        │                    │
        │               extract_agent
        │                    │
        │               flag_agent
        │                    │
        │               explain_agent
        │                    │
        │               advisor_agent
        │                    │
        │            ◄── CLARState ──────────────────
        │
        ├── POST /api/chat ──► Anthropic (single-turn)
        └── POST /api/chat/stream ──► Anthropic (SSE streaming)
```

**Key design decisions:**
- LangGraph chosen over bare function chains for explicit state transitions and easy node addition
- Static Next.js export served by FastAPI avoids a separate frontend server (one Cloud Run instance = zero cold-start overhead on the frontend)
- Workload Identity Federation instead of service account keys — no long-lived secrets in GitHub
- spaCy `en_core_web_lg` for de-identification because it runs locally with no external API call, keeping PHI off third-party servers before anonymisation

---

## LLM pipeline

```
upload → deid → extract → flag → explain → advisor → response
```

Each step is a LangGraph node with its own prompt, structured output (JSON), and error handling:

| Node | Model call | Output |
|---|---|---|
| `extract_agent` | Claude Sonnet 4.6 | List of raw findings |
| `flag_agent` | Claude Sonnet 4.6 | Urgency level per finding |
| `explain_agent` | Claude Sonnet 4.6 | Lay-language explanation per finding |
| `advisor_agent` | Claude Sonnet 4.6 | 3–5 doctor questions |
| `chat` / `chat/stream` | Claude Sonnet 4.6 | Contextual Q&A |

**Prompt strategy:** System prompt separation (role + constraints), structured JSON output with schema in the prompt, temperature tuned per node (0.1 for extraction, 0.4 for advice), JSON fence stripping to handle model formatting variation.

All pipeline runs are traced in LangSmith under the `clar-production` project.

---

## Observability

| Signal | Tool | Detail |
|---|---|---|
| LLM traces | LangSmith | Full input/output per pipeline run, latency, token counts |
| Metrics | Prometheus (`/metrics`) | Requests, pipeline duration, per-agent duration, token usage, errors, PII entities removed |
| Logs | Loguru (structured JSON in prod) | Every agent start/end, errors with context — no raw text logged |

---

## Evaluation

### Urgency classification accuracy

The `evals/eval_urgency.py` script validates the rules-based urgency classifier (`flag_agent`) against 21 labelled clinical test cases covering haematology, metabolic, and renal findings.

```
python evals/eval_urgency.py --verbose --min-accuracy 0.90
```

| Metric | Result |
|---|---|
| Test cases | 21 (haematology, metabolic, renal) |
| Accuracy | 100% (21/21) |
| Threshold | ≥90% required — enforced in CI |

**Note:** The rules-based classifier handles numeric findings by computing the percentage deviation from the reference range (threshold: 50% for urgent). Qualitative findings (radiology, discharge text) fall through to the LLM with a structured prompt, which is validated manually against the sample fixtures.

### LLM output quality

Prompt design was validated against the three sample fixture types (CBC lab, radiology, discharge summary):

- **Structured JSON output**: system prompt includes schema definition; JSON fences stripped automatically
- **Few-shot examples**: two in-context examples in `explain_agent` for CBC and radiology report formats
- **Temperature tuning**: 0.1 for extraction (deterministic), 0.4 for advice (creative)
- **Retry on transient errors**: up to 3 attempts with exponential backoff (2s, 4s) for 429/5xx responses

---

## Project structure

```
clar/
├── app/                    # FastAPI backend
│   ├── agents/             # LangGraph pipeline nodes (deid, extract, flag, explain, advisor)
│   ├── api/routes/         # upload, chat, chat/stream, health, metrics
│   ├── models/             # Pydantic models + CLARState TypedDict
│   ├── observability/      # Prometheus metrics, structured logging
│   ├── prompts/            # LLM prompt templates (system + user per agent)
│   └── services/           # de-id (spaCy), LLM client, session store (TTL cache)
├── frontend/               # Next.js frontend
│   ├── components/
│   │   ├── results/        # FindingCard, Sidebar, ChatDrawer, VerdictBanner, ChatMessage
│   │   ├── shared/         # NavBar, LoadingScreen, ErrorState
│   │   └── upload/         # UploadZone, SampleButton, TrustBadges
│   ├── lib/                # api.ts, types.ts
│   ├── pages/              # index.tsx (upload), results.tsx
│   └── styles/             # tokens.ts (design system — single source of truth for colors)
├── infra/
│   ├── docker/             # Dockerfile (3-stage: node-builder → python-builder → runtime)
│   └── terraform/          # Cloud Run v2, Artifact Registry, Secret Manager
├── tests/
│   ├── unit/               # Per-agent and service unit tests
│   ├── integration/        # Full pipeline integration tests
│   └── fixtures/           # Sample reports (lab, radiology, discharge)
└── .github/workflows/
    ├── ci.yml              # lint (ruff + mypy) + test (pytest >80% cov) + docker build on every PR
    └── cd.yml              # build + push + deploy on merge to main + smoke test
```

---

## Running locally

**Prerequisites:** Python 3.11, Node 20, a `.env` file (copy `.env.example`).

```bash
# Backend
pip install -r requirements.txt
python -m spacy download en_core_web_lg
uvicorn app.main:app --reload
# → http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` for local dev.

---

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/upload` | Upload report (PDF or text) — returns findings, verdict, questions |
| POST | `/api/chat` | Single-turn Q&A about a report session |
| POST | `/api/chat/stream` | Streaming Q&A via SSE (`text/event-stream`) |
| GET | `/metrics` | Prometheus metrics |

---

## Deployment

The CD workflow (`cd.yml`) runs on every push to `main`:

1. Lint (ruff + mypy) and test (pytest, >80% coverage required)
2. Build Next.js static export
3. Build Docker image (linux/amd64, 3-stage)
4. Push to Artifact Registry (`us-central1-docker.pkg.dev/stella-cyber-analyzer/clar/clar`)
5. Deploy to Cloud Run v2
6. Smoke test `/health` — fails the workflow if the service is down

Infrastructure is managed with Terraform. GCP authentication uses Workload Identity Federation — no long-lived service account keys stored in GitHub.

---

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | GCP Secret Manager | Claude API access |
| `LANGSMITH_API_KEY` | GCP Secret Manager | LangSmith tracing |
| `CLERK_SECRET_KEY` | GCP Secret Manager | Clerk JWT verification |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | GitHub Secret | Clerk frontend auth |
| `NEXT_PUBLIC_API_URL` | Build arg | Backend base URL baked into static export |
