# CLAR — System Design Spec
**Date:** 2026-04-25
**Status:** Approved

---

## What CLAR Does

CLAR transforms confusing medical reports into plain-language explanations patients can understand and act on. It accepts uploaded lab results, radiology reports, pathology reports, and discharge summaries, de-identifies them before any LLM call, then runs a five-agent pipeline to explain findings, flag urgency, and generate doctor questions.

---

## Locked Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Cloud | GCP Cloud Run | Scales to zero, free tier, reuses cyber project Terraform |
| Container registry | Google Artifact Registry | Reuse existing GCP project |
| Secrets | GCP Secret Manager | ANTHROPIC_API_KEY never in env vars or Terraform |
| minScale | 1 during demo, 0 after submission | Prevents cold-start session loss mid-demo |
| LLM | claude-sonnet-4-6 | Specified by capstone rubric |
| Agent orchestration | LangGraph StateGraph (sequential) | Spec-compliant, simple to test, LangSmith auto-traces |
| PII removal | Microsoft Presidio | Before every LLM call — pipeline aborts on failure |
| Tracing | LangSmith | Native LangGraph integration, account exists |
| Metrics | Prometheus + Grafana | Exposed at /metrics, pre-provisioned dashboard |
| Logging | Loguru JSON sink | Structured, never logs raw_text or deid_text |
| PDF extraction | pdfplumber, digital PDFs only | No OCR/Tesseract needed for capstone demo |
| Chat sessions | In-memory dict, TTL 30 min | Spec-compliant; cold starts prevented by minScale=1 |
| Frontend | Next.js 14 (Pages Router) + TypeScript + Tailwind CSS | Consistent with Zeya/Alex course pattern; enables Clerk |
| Auth | Clerk `@clerk/nextjs@6.x` (pin to 6.x) | Known from Zeya + Alex; v7 removed SignedIn/SignedOut |
| Frontend deployment | Static export (`output: 'export'`) served by FastAPI | Single Docker container — same pattern as cyber + Week 1 |
| Design reference | CLAR_Prototype.html | Source of truth for layout, palette, sidebar, components |
| Font | IBM Plex Sans | Medical-grade, clinical feel |
| Icons | SVG only | No emojis anywhere in UI or code |
| API docs | GitBook via /openapi.json import | FastAPI generates spec automatically, zero extra writing |
| Testing discipline | TDD — test written before implementation | CI enforces >80% coverage, no merge without green tests |
| CI/CD auth | GCP Workload Identity Federation | No long-lived service account keys in GitHub secrets |

---

## Architecture

```
Next.js 14 (Pages Router, TypeScript, Tailwind, IBM Plex Sans)
  pages/index.tsx        ← public upload screen (Clerk SignedOut gate)
  pages/results.tsx      ← protected results + sidebar (Clerk SignedIn)
  pages/chat.tsx         ← protected chat drawer
  lib/api.ts             ← all fetch calls, one function per endpoint
    │
    ├── POST /api/upload   ← file (PDF or .txt, max 10 MB)
    ├── POST /api/chat     ← {report_id, question}
    ├── GET  /health
    └── GET  /metrics      ← Prometheus scrape

FastAPI (app/main.py)
    │
    └── LangGraph StateGraph (app/agents/pipeline.py)
            │
            ├── Node 1: ExtractAgent      (no LLM)
            ├── Node 2: DeIDAgent         (Presidio — ABORT on failure)
            │       └── conditional edge → ErrorNode if deid failed/empty
            ├── Node 3: ExplainAgent      (Claude, temp 0.1, JSON, max 2000 tok)
            ├── Node 4: FlagAgent         (rules-based + LLM fallback, temp 0.1, max 1000 tok)
            └── Node 5: AdvisorAgent      (Claude, temp 0.4, JSON, max 1000 tok)

Observability
    ├── LangSmith   ← auto-traces all LangGraph nodes
    ├── Prometheus  ← /metrics endpoint (6 metrics)
    ├── Grafana     ← pre-provisioned dashboard (docker-compose)
    └── Loguru      ← JSON sink, metadata only, never raw text

Infrastructure (GCP, adapted from cyber project)
    ├── Artifact Registry   ← Docker image
    ├── Cloud Run           ← CLAR container (minScale=1 demo, 0 post-submission)
    ├── Secret Manager      ← ANTHROPIC_API_KEY, LANGSMITH_API_KEY
    └── Terraform           ← infra/terraform/ (adapted from cyber/terraform/gcp/)

CI/CD (GitHub Actions)
    ├── ci.yml  ← lint + typecheck + pytest >80% + docker build (every PR)
    └── cd.yml  ← build + push + deploy + smoke test (merge to main)

API Documentation
    └── GitBook ← imports /openapi.json from FastAPI, supplemented with architecture + compliance pages
```

---

## Project Structure

```
clar/
  app/
    main.py                  # FastAPI app, router registration, lifespan
    config.py                # pydantic-settings, reads .env
    api/
      routes/
        upload.py            # POST /api/upload
        chat.py              # POST /api/chat
        health.py            # GET /health
        metrics.py           # GET /metrics (Prometheus)
    agents/
      pipeline.py            # LangGraph StateGraph — wires all 5 agents
      extract_agent.py       # Node 1
      deid_agent.py          # Node 2
      explain_agent.py       # Node 3
      flag_agent.py          # Node 4
      advisor_agent.py       # Node 5
    models/
      report.py              # CLARState, Finding, ReportResult, ChatRequest, ChatResponse
    services/
      extractor.py           # pdfplumber + .txt decode, report_type detection
      deid.py                # Presidio analyser + anonymiser + custom MRN recogniser
      llm.py                 # Anthropic client wrapper, retry, token counting
      session.py             # In-memory chat session store, TTL 30 min
    prompts/
      explain.py             # System + user prompt, 2 few-shot examples
      flag.py                # Chain-of-thought prompt
      advisor.py             # 5-question generation prompt
    observability/
      metrics.py             # Prometheus counter/histogram definitions
      logging.py             # Loguru configuration, JSON sink
  tests/
    unit/
      test_extractor.py      # written first (TDD)
      test_deid.py           # PII regression test — written first (TDD)
      test_explain_agent.py  # written first (TDD)
      test_flag_agent.py     # written first (TDD)
      test_advisor_agent.py  # written first (TDD)
    integration/
      test_pipeline.py       # full end-to-end
    eval/
      eval_pipeline.py       # 3-5 fixtures, logs to LangSmith
    fixtures/
      sample_cbc.txt
      sample_radiology.txt
  infra/
    terraform/
      main.tf                # Cloud Run, Artifact Registry, Secret Manager
      variables.tf
      outputs.tf             # service_url, registry_url
    docker/
      Dockerfile             # multi-stage, non-root user, linux/amd64
      docker-compose.yml     # api + prometheus + grafana
      docker-compose.prod.yml
      grafana/
        provisioning/        # pre-configured dashboard JSON
  .github/
    workflows/
      ci.yml
      cd.yml
  docs/
    superpowers/
      specs/
        2026-04-25-clar-system-design.md   # this file
  frontend/
    pages/
      index.tsx            # upload screen — public (Clerk SignedOut/SignedIn)
      results.tsx          # results + sidebar — protected
      _app.tsx             # ClerkProvider wrapper
    components/
      upload/              # UploadZone, SampleButton, TrustBadges
      results/             # Sidebar, FindingCard, VerdictBanner, QuestionList
      shared/              # NavBar, ErrorState, LoadingScreen
    lib/
      api.ts               # all fetch calls — one function per endpoint
    styles/
      tokens.ts            # design tokens (navy, blue, green, amber, red)
    public/
  CLAR_Prototype.html        # design reference only — not deployed
  requirements.txt
  requirements-dev.txt
  .env.example
  README.md
```

---

## LangGraph State

```python
class CLARState(TypedDict):
    raw_text:       str           # extracted from uploaded file
    deid_text:      str           # after Presidio de-identification
    report_type:    str           # lab | radiology | pathology | discharge
    findings:       list[dict]    # name, value, unit, reference_range, confidence
    explanations:   list[dict]    # + plain_explanation (max 3 sentences)
    flagged:        list[dict]    # + urgency (normal|watch|urgent), urgency_reason
    questions:      list[str]     # exactly 5, specific to findings
    deid_entities:  list[dict]    # type + count — for audit log and metrics
    error:          str | None
```

---

## Agent Specifications

### Node 1 — ExtractAgent (no LLM)
- pdfplumber for digital PDFs; plain decode for .txt
- Keyword scan to detect report_type
- Writes: `raw_text`, `report_type`

### Node 2 — DeIDAgent (CRITICAL SAFETY GATE)
- Presidio AnalyzerEngine + AnonymizerEngine
- Entities: PERSON, DATE_TIME, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS, MEDICAL_LICENSE, UK_NHS, US_SSN + custom MRN recogniser (`MRN[\s:-]?\d{6,10}`)
- Replacements: [PATIENT] [DATE] [CLINICIAN] [ADDRESS] [PHONE] [EMAIL] [MEDICAL_ID]
- On any failure: set `error`, pipeline routes to ErrorNode → 422 to user
- Never falls through to LLM with potentially identified text
- Structured warning logged for every entity replaced (audit trail)
- Conditional edge: `deid_text` empty or `deid_failed` → ErrorNode

### Node 3 — ExplainAgent
- Model: claude-sonnet-4-6, temperature 0.1, JSON mode, max_tokens 2000
- System prompt includes: "You are analysing a de-identified medical report. Do not attempt to re-identify the patient. Do not provide a diagnosis. Explain findings clearly for a non-medical audience."
- 2 few-shot examples in prompt (CBC lab + radiology)
- Output per finding: name, value, unit, reference_range, plain_explanation (max 3 sentences), confidence

### Node 4 — FlagAgent
- Rules-based classifier first: numeric value vs reference_range → normal/watch/urgent
- LLM fallback only for ambiguous cases (no numeric range, qualitative findings)
- Model: claude-sonnet-4-6, temperature 0.1, JSON mode, max_tokens 1000
- Chain-of-thought prompt: "Think step by step before classifying urgency"
- Output per finding: urgency (normal|watch|urgent), urgency_reason

### Node 5 — AdvisorAgent
- Model: claude-sonnet-4-6, temperature 0.4, JSON mode, max_tokens 1000
- Generates exactly 5 questions specific to flagged values — not generic
- Higher temperature for natural variation in questions

---

## API Contracts

### POST /api/upload
```
Request:  multipart/form-data, field=file, accept=.pdf,.txt, max 10 MB

Response 200:
{
  "report_id":           "uuid-v4",
  "report_type":         "lab",
  "verdict": {
    "level":             "watch",
    "summary":           "2 findings flagged for your attention"
  },
  "findings": [
    {
      "name":            "Haemoglobin",
      "value":           "10.2 g/dL",
      "reference_range": "12.0–16.0 g/dL",
      "urgency":         "watch",
      "urgency_reason":  "Below normal range",
      "explanation":     "Your haemoglobin is slightly below..."
    }
  ],
  "questions":           ["Could the low haemoglobin and MCV together indicate..."],
  "processing_time_ms":  1842,
  "deid_entities_removed": 3
}
```

### POST /api/chat
```
Request:  { "report_id": "uuid", "question": "Is my iron low?" }
Response: { "answer": "Based on your results..." }
Session:  in-memory dict[report_id → {findings, questions, report_type, expires_at}]
TTL:      30 minutes from upload
404:      graceful "session expired" if report_id not found or TTL elapsed
```

### GET /health
```
Response: { "status": "ok", "version": "1.0.0" }
```

### GET /metrics
```
Prometheus exposition format. Metrics:
  clar_requests_total              counter  labels: report_type, status
  clar_pipeline_duration_seconds   histogram
  clar_agent_duration_seconds      histogram  labels: agent_name
  clar_deid_entities_total         counter
  clar_llm_tokens_total            counter  labels: agent_name, direction (input|output)
  clar_errors_total                counter  labels: error_type
```

---

## Error Handling

All errors handled via FastAPI exception handlers — no scattered try/except in route handlers.

| Code | Trigger | Message |
|------|---------|---------|
| 413 | File > 10 MB | "File exceeds 10 MB limit" |
| 415 | Wrong file type | "Only PDF and plain text files are supported" |
| 422 | DeID failure | "Could not safely process this document. Please try again." |
| 504 | LLM timeout > 30s | "Analysis is taking longer than expected. Please try again." |
| 500 | All other | `{ "error": "...", "request_id": "uuid" }` |

---

## De-identification Contract

```python
def deidentify(text: str) -> tuple[str, list[dict]]:
    """
    Returns (anonymised_text, list of removed entities with type and count).
    Never raises — on failure returns original text with deid_failed=True
    so the pipeline can abort rather than send raw PII to the LLM.
    """
```

Custom recogniser: `MRN[\s:-]?\d{6,10}` → [MEDICAL_ID]

Test contract (test_deid.py — written before implementation):
1. Build string with known PII: name, DOB, phone, email, NHS number, MRN
2. Run `deidentify()`
3. Assert none of the original PII strings appear in output
4. Assert entity list is non-empty
5. Assert `deid_failed` is False on success

---

## Frontend — Next.js 14

**Stack:** Next.js 14 Pages Router · TypeScript · Tailwind CSS · Clerk `@clerk/nextjs@6.x`

**Auth pattern (from Zeya/Alex):**
- `ClerkProvider` wraps app in `_app.tsx`
- `index.tsx` uses `<SignedIn>` / `<SignedOut>` — upload gated behind sign-in
- `results.tsx` uses `useAuth().getToken()` — JWT passed as `Authorization: Bearer` to FastAPI
- Backend validates JWT against Clerk JWKS endpoint (no Clerk API call per request)
- Pin to `@clerk/nextjs@6.x` — v7 removed `SignedIn`/`SignedOut` components

**Deployment:** `output: 'export'` in `next.config.ts` → static export → served by FastAPI from `/static`. Single Docker container, same pattern as cyber project.

**Design (from CLAR_Prototype.html reference):**

| Screen | Detail |
|--------|--------|
| Font | IBM Plex Sans (Google Fonts) — medical-grade, clinical feel |
| Icons | Inline SVG only — no emojis anywhere |
| Upload screen | UploadZone + sample button + trust badges (PII stripped / no storage / HIPAA aligned) |
| Processing screen | Real agent status updates while awaiting API response |
| Results screen | Sidebar layout — report info + verdict + nav (Findings / Urgency / Questions) on left, detail on right |
| Chat drawer | Slides in from right, POST /api/chat with report_id, starter chips |
| Errors | Friendly error state on all API failures — never raw stack trace |

**Component rules (from Goldenberri/Zeya patterns):**
- Named exports for all components; default export for page files only
- All API calls through `lib/api.ts` — no inline fetch in components
- Design tokens in `styles/tokens.ts` — no hardcoded hex values in components
- 150-line hard cap per file — split before hitting limit

---

## Logging Rules

- JSON sink in production: `logger.add(sys.stdout, serialize=True)`
- Log points: request received (INFO), DeID complete (INFO), each agent start/complete (DEBUG), LLM call (DEBUG), pipeline complete (INFO), any exception (ERROR)
- Never log `raw_text` or `deid_text` — metadata only
- Every log line includes `request_id`

---

## Environment Variables

**Backend (.env):**
```
ANTHROPIC_API_KEY=             # from GCP Secret Manager in production
LANGSMITH_API_KEY=             # LangSmith account (exists)
LANGSMITH_PROJECT=clar-production
CLERK_JWKS_URL=                # from Clerk Dashboard — for JWT validation
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
REPORT_SESSION_TTL_MINUTES=30
```

**Frontend (frontend/.env.local):**
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=   # public, safe to expose
CLERK_SECRET_KEY=                    # server-side only
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## TDD Build Order

For every agent and service: write test first → run (red) → write implementation → run (green) → refactor.

```
1. test_extractor.py       → extractor.py
2. test_deid.py            → deid.py          (PII regression — most critical)
3. test_explain_agent.py   → explain_agent.py
4. test_flag_agent.py      → flag_agent.py
5. test_advisor_agent.py   → advisor_agent.py
6. test_pipeline.py        → pipeline.py      (integration — runs last)
```

CI enforces >80% coverage. No merge to main without passing tests.

---

## Infrastructure — Terraform (GCP, adapted from cyber/terraform/gcp/)

Resources:
- `google_project_service` — enables Cloud Run, Artifact Registry, Secret Manager APIs
- `google_artifact_registry_repository` — Docker image store
- `google_cloud_run_v2_service` — CLAR container, minScale=1 (demo), 0 (post-submission)
- `google_cloud_run_v2_service_iam_member` — allUsers invoker (public)
- `google_secret_manager_secret` — ANTHROPIC_API_KEY, LANGSMITH_API_KEY

Outputs: `service_url`, `registry_url`

Docker (3-stage build):
- Stage 1 (node): Node 20 Alpine — builds Next.js static export into `/out`
- Stage 2 (builder): Python 3.11 slim — installs dependencies into `/venv`
- Stage 3 (runtime): Python 3.11 slim — copies `/venv` + app code + `/out` as `./static`, runs as non-root user
- FastAPI mounts `./static` and serves `index.html` at root
- `--platform linux/amd64` required (same lesson from cyber + Alex)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` passed as Docker build arg (baked into JS bundle)

---

## CI/CD — GitHub Actions

**ci.yml** (every PR to main): checkout → Python 3.11 → pip install → ruff → mypy → pytest >80% → Node 20 setup → npm install → npm run build (Next.js static export) → docker build

**cd.yml** (merge to main): all CI steps → GCP Workload Identity auth (no long-lived keys) → docker build + push to Artifact Registry (`--platform linux/amd64`) → `gcloud run deploy` → curl /health smoke test → GitHub step summary on failure

`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is a build arg (baked into static JS bundle at build time — not a runtime env var).

---

## API Documentation — GitBook

1. FastAPI exposes `/openapi.json` automatically
2. Import into GitBook via OpenAPI block → live, browsable API reference
3. Supplement with: architecture overview, de-identification compliance note, environment variables reference, local dev quickstart (`docker-compose up`)

---

## docker-compose up (zero manual steps)

```yaml
services:
  api:        # FastAPI, bind mount for hot reload, port 8000
  prometheus: # scrapes /metrics every 15s
  grafana:    # pre-provisioned dashboard, port 3000
```

---

## Compliance Notes

- PII never reaches the LLM — Presidio de-identifies before every call
- Reports never stored — processed in memory, discarded after response
- Chat sessions: in-memory only, TTL 30 minutes, no persistence
- HIPAA / GDPR / NDPR aligned by design (no storage, no re-identification)
- Non-root Docker user in production container
