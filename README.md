# CLAR — Clinical Lab Analysis Report

CLAR is a medical report analysis tool that takes lab results, radiology reports, or discharge summaries and explains them in plain English. It flags urgent findings, summarises urgency, and lets patients ask follow-up questions in a chat interface.

**Live:** https://clar-608805582585.us-central1.run.app

---

## What it does

1. Upload a PDF or plain-text medical report
2. CLAR de-identifies personal details, extracts findings, and flags anything outside the normal range
3. Results page shows all findings with urgency levels (normal / watch / urgent), a verdict summary, and suggested questions to ask your doctor
4. Ask follow-up questions via the built-in chat — answers stream back in real time

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, LangGraph, Anthropic Claude |
| Frontend | Next.js 14 (Pages Router), TypeScript, Tailwind CSS, Clerk auth |
| Infra | Google Cloud Run, Artifact Registry, Secret Manager |
| CI/CD | GitHub Actions + Workload Identity Federation (keyless GCP auth) |

---

## Project structure

```
clar/
├── app/                    # FastAPI backend
│   ├── agents/             # LangGraph pipeline nodes
│   ├── api/routes/         # upload, chat, health, metrics
│   ├── models/             # Pydantic models
│   ├── prompts/            # LLM prompt templates
│   └── services/           # de-id, LLM client, session store
├── frontend/               # Next.js frontend
│   ├── components/
│   │   ├── results/        # FindingCard, Sidebar, ChatDrawer, VerdictBanner
│   │   ├── shared/         # NavBar, LoadingScreen, ErrorState
│   │   └── upload/         # UploadZone, SampleButton, TrustBadges
│   ├── lib/                # api.ts, types.ts
│   ├── pages/              # index.tsx, results.tsx
│   └── styles/             # tokens.ts (design system)
├── infra/
│   ├── docker/             # Dockerfile (3-stage: node → python → runtime)
│   └── terraform/          # Cloud Run, Artifact Registry, Secret Manager
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── .github/workflows/
    ├── ci.yml              # lint + test + docker build on every PR
    └── cd.yml              # build + push + deploy on merge to main
```

---

## Running locally

**Prerequisites:** Python 3.11, Node 20, a `.env` file with your API keys (see `.env.example`).

```bash
# Backend
pip install -r requirements.txt
python -m spacy download en_core_web_lg
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:3000`.

---

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/upload` | Upload report — returns findings + verdict |
| POST | `/api/chat` | Single-turn Q&A about a report |
| POST | `/api/chat/stream` | Streaming Q&A (SSE) |
| GET | `/metrics` | Prometheus metrics |

---

## Pipeline

```
upload → deid → extract → flag → explain → advisor → response
```

Each step is a LangGraph node. The pipeline runs synchronously; the chat endpoint uses Anthropic's streaming API for real-time responses.

---

## Deployment

The CD workflow runs on every push to `main`:

1. Lint (ruff + mypy) and test (pytest, >80% coverage)
2. Build Next.js static export, then Docker image (linux/amd64)
3. Push to Artifact Registry
4. Deploy to Cloud Run
5. Smoke test `/health`

GCP authentication uses Workload Identity Federation — no long-lived service account keys stored in GitHub.
