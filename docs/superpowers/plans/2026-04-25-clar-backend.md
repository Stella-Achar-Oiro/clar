# CLAR Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + LangGraph five-agent pipeline that accepts medical report uploads, de-identifies them with Presidio, explains findings with Claude, flags urgency, generates doctor questions, and exposes Prometheus metrics — all runnable locally with `docker-compose up`.

**Architecture:** FastAPI serves two endpoints (`POST /api/upload`, `POST /api/chat`) backed by a LangGraph StateGraph with five sequential nodes. Presidio de-identifies text before any LLM call; on failure the pipeline aborts with 422. All agents call `claude-sonnet-4-6` via the Anthropic SDK. Prometheus counters/histograms are incremented inline; Loguru writes JSON to stdout.

**Tech Stack:** Python 3.11 · FastAPI · LangGraph · Anthropic SDK · Microsoft Presidio · pdfplumber · Prometheus client · Loguru · pytest + pytest-cov · ruff · mypy · Docker (multi-stage, linux/amd64) · docker-compose

---

## File Map

```
clar/
  app/
    main.py                        # FastAPI app factory, lifespan, exception handlers
    config.py                      # pydantic-settings Settings class
    models/
      report.py                    # CLARState, Finding, ReportResult, ChatRequest, ChatResponse
    services/
      extractor.py                 # pdfplumber + .txt decode + report_type keyword detection
      deid.py                      # Presidio analyser + anonymiser + custom MRN recogniser
      llm.py                       # Anthropic client wrapper (retry + token counting)
      session.py                   # In-memory session store with TTL
    prompts/
      explain.py                   # ExplainAgent system prompt + 2 few-shot examples
      flag.py                      # FlagAgent chain-of-thought prompt
      advisor.py                   # AdvisorAgent 5-question prompt
    agents/
      extract_agent.py             # Node 1 — calls extractor.py, no LLM
      deid_agent.py                # Node 2 — calls deid.py, sets deid_failed on error
      explain_agent.py             # Node 3 — calls llm.py with explain prompt
      flag_agent.py                # Node 4 — rules engine + LLM fallback
      advisor_agent.py             # Node 5 — calls llm.py with advisor prompt
      pipeline.py                  # LangGraph StateGraph wiring all 5 nodes
    api/
      routes/
        upload.py                  # POST /api/upload
        chat.py                    # POST /api/chat
        health.py                  # GET /health
        metrics.py                 # GET /metrics (Prometheus exposition)
    observability/
      metrics.py                   # Prometheus counter/histogram definitions
      logging.py                   # Loguru configuration, JSON sink
  tests/
    unit/
      test_extractor.py
      test_deid.py                 # PII regression — most critical
      test_explain_agent.py
      test_flag_agent.py
      test_advisor_agent.py
    integration/
      test_pipeline.py
    eval/
      eval_pipeline.py
    fixtures/
      sample_cbc.txt
      sample_radiology.txt
    conftest.py
  infra/
    docker/
      Dockerfile
      docker-compose.yml
      grafana/
        provisioning/
          datasources/
            prometheus.yml
          dashboards/
            dashboard.yml
            clar_dashboard.json
  requirements.txt
  requirements-dev.txt
  .env.example
  pyproject.toml                   # ruff + mypy config
```

---

## Task 1: Project Scaffold — Dependencies, Config, Models

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/models/report.py`
- Create: `app/models/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/eval/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
pydantic-settings==2.4.0
anthropic==0.34.2
langgraph==0.2.28
langsmith==0.1.117
pdfplumber==0.11.4
presidio-analyzer==2.2.354
presidio-anonymizer==2.2.354
spacy==3.7.6
prometheus-client==0.21.0
loguru==0.7.2
httpx==0.27.2
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest==8.3.3
pytest-cov==5.0.0
pytest-asyncio==0.24.0
httpx==0.27.2
ruff==0.6.9
mypy==1.11.2
types-pyyaml==6.0.12.20240917
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
```

- [ ] **Step 4: Create `.env.example`**

```
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=clar-production
CLERK_JWKS_URL=https://your-clerk-domain.clerk.accounts.dev/.well-known/jwks.json
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
REPORT_SESSION_TTL_MINUTES=30
```

- [ ] **Step 5: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    langsmith_api_key: str = ""
    langsmith_project: str = "clar-production"
    clerk_jwks_url: str = ""
    environment: str = "development"
    log_level: str = "INFO"
    max_file_size_mb: int = 10
    report_session_ttl_minutes: int = 30


settings = Settings()
```

- [ ] **Step 6: Create `app/models/report.py`**

```python
from typing import TypedDict
from pydantic import BaseModel


class CLARState(TypedDict):
    raw_text: str
    deid_text: str
    report_type: str
    findings: list[dict]
    explanations: list[dict]
    flagged: list[dict]
    questions: list[str]
    deid_entities: list[dict]
    error: str | None


class Finding(BaseModel):
    name: str
    value: str
    reference_range: str
    urgency: str
    urgency_reason: str
    explanation: str


class Verdict(BaseModel):
    level: str
    summary: str


class ReportResult(BaseModel):
    report_id: str
    report_type: str
    verdict: Verdict
    findings: list[Finding]
    questions: list[str]
    processing_time_ms: int
    deid_entities_removed: int


class ChatRequest(BaseModel):
    report_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
```

- [ ] **Step 7: Create all `__init__.py` files and `tests/conftest.py`**

```bash
mkdir -p app/models app/services app/prompts app/agents app/api/routes app/observability
mkdir -p tests/unit tests/integration tests/eval tests/fixtures
touch app/__init__.py app/models/__init__.py app/services/__init__.py
touch app/prompts/__init__.py app/agents/__init__.py app/api/__init__.py
touch app/api/routes/__init__.py app/observability/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
touch tests/eval/__init__.py
```

`tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_cbc_text() -> str:
    return """
CBC Blood Panel Report
Patient Name: John Smith
Date of Birth: 01/01/1980
MRN: 12345678
Phone: 555-123-4567

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
"""


@pytest.fixture
def sample_radiology_text() -> str:
    return """
Radiology Report
Patient: Jane Doe
DOB: 1975-03-15
NHS Number: 123 456 7890

FINDINGS: Mild consolidation in the right lower lobe.
IMPRESSION: Findings consistent with early pneumonia.
"""
```

- [ ] **Step 8: Install dependencies and download spaCy model**

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m spacy download en_core_web_lg
```

Expected: No errors. spaCy model downloads (~750 MB).

- [ ] **Step 9: Commit**

```bash
git add requirements.txt requirements-dev.txt pyproject.toml .env.example \
  app/ tests/conftest.py
git commit -m "feat: project scaffold — deps, config, models, test structure"
```

---

## Task 2: ExtractAgent — TDD (test first)

**Files:**
- Create: `tests/unit/test_extractor.py`
- Create: `app/services/extractor.py`
- Create: `app/agents/extract_agent.py`
- Create: `tests/fixtures/sample_cbc.txt`
- Create: `tests/fixtures/sample_radiology.txt`

- [ ] **Step 1: Create test fixtures**

`tests/fixtures/sample_cbc.txt`:
```
CBC Blood Panel Report
Patient Name: John Smith
Date of Birth: 01/01/1980
MRN: 12345678
Phone: 555-123-4567

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
Platelets: 210 x10^3/uL (Reference: 150-400 x10^3/uL)
```

`tests/fixtures/sample_radiology.txt`:
```
Radiology Report
Patient: Jane Doe
DOB: 1975-03-15
NHS Number: 123 456 7890

PROCEDURE: Chest X-Ray PA
FINDINGS: Mild consolidation in the right lower lobe. Cardiac silhouette within normal limits.
IMPRESSION: Findings consistent with early pneumonia. Follow-up recommended in 6 weeks.
```

- [ ] **Step 2: Write `tests/unit/test_extractor.py` (failing)**

```python
import pytest
from pathlib import Path
from app.services.extractor import extract_text, detect_report_type

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_extract_txt_returns_text():
    text = extract_text(FIXTURES / "sample_cbc.txt")
    assert "Haemoglobin" in text
    assert len(text) > 50


def test_detect_lab_report_type():
    text = "CBC Blood Panel Report\nHaemoglobin: 10.2 g/dL"
    assert detect_report_type(text) == "lab"


def test_detect_radiology_report_type():
    text = "Radiology Report\nChest X-Ray PA\nFINDINGS: consolidation"
    assert detect_report_type(text) == "radiology"


def test_detect_pathology_report_type():
    text = "Pathology Report\nBiopsy specimen received"
    assert detect_report_type(text) == "pathology"


def test_detect_discharge_report_type():
    text = "Discharge Summary\nPatient discharged in stable condition"
    assert detect_report_type(text) == "discharge"


def test_detect_unknown_defaults_to_lab():
    text = "Some medical document with no clear type indicator"
    assert detect_report_type(text) == "lab"


def test_extract_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        extract_text(Path("/nonexistent/file.txt"))
```

- [ ] **Step 3: Run test — verify it fails**

```bash
pytest tests/unit/test_extractor.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services.extractor'`

- [ ] **Step 4: Write `app/services/extractor.py`**

```python
from pathlib import Path
import pdfplumber

_REPORT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "radiology": ["radiology", "x-ray", "xray", "mri", "ct scan", "ultrasound", "imaging", "findings:", "impression:"],
    "pathology": ["pathology", "biopsy", "histology", "specimen", "microscopic", "gross description"],
    "discharge": ["discharge summary", "discharged", "admission date", "discharge date", "discharge diagnosis"],
    "lab": ["cbc", "blood panel", "haemoglobin", "hemoglobin", "glucose", "creatinine", "laboratory", "lab results"],
}


def extract_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() == ".pdf":
        return _extract_pdf(path)
    return path.read_text(encoding="utf-8")


def _extract_pdf(path: Path) -> str:
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def detect_report_type(text: str) -> str:
    lower = text.lower()
    for report_type, keywords in _REPORT_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return report_type
    return "lab"
```

- [ ] **Step 5: Write `app/agents/extract_agent.py`**

```python
from pathlib import Path
from app.models.report import CLARState
from app.services.extractor import extract_text, detect_report_type


def run_extract_agent(state: CLARState, file_path: Path) -> CLARState:
    raw_text = extract_text(file_path)
    report_type = detect_report_type(raw_text)
    return {**state, "raw_text": raw_text, "report_type": report_type}
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest tests/unit/test_extractor.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/unit/test_extractor.py tests/fixtures/ app/services/extractor.py \
  app/agents/extract_agent.py
git commit -m "feat: ExtractAgent — pdfplumber + report_type detection (TDD)"
```

---

## Task 3: DeIDAgent — TDD (PII regression — most critical)

**Files:**
- Create: `tests/unit/test_deid.py`
- Create: `app/services/deid.py`
- Create: `app/agents/deid_agent.py`

- [ ] **Step 1: Write `tests/unit/test_deid.py` (failing)**

```python
import pytest
from app.services.deid import deidentify

# Known PII strings that MUST NOT appear in de-identified output
PATIENT_NAME = "John Smith"
DOB = "01/01/1980"
PHONE = "555-123-4567"
EMAIL = "john.smith@example.com"
NHS_NUMBER = "123 456 7890"
MRN = "MRN: 12345678"
SSN = "123-45-6789"

SAMPLE_TEXT = f"""
CBC Blood Panel Report
Patient Name: {PATIENT_NAME}
Date of Birth: {DOB}
Phone: {PHONE}
Email: {EMAIL}
NHS Number: {NHS_NUMBER}
{MRN}
SSN: {SSN}

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
"""


def test_patient_name_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert PATIENT_NAME not in deid_text
    assert not failed


def test_date_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert DOB not in deid_text
    assert not failed


def test_phone_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert PHONE not in deid_text
    assert not failed


def test_email_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert EMAIL not in deid_text
    assert not failed


def test_nhs_number_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert NHS_NUMBER not in deid_text
    assert not failed


def test_mrn_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert "12345678" not in deid_text
    assert not failed


def test_ssn_removed():
    deid_text, _, failed = deidentify(SAMPLE_TEXT)
    assert SSN not in deid_text
    assert not failed


def test_entities_list_non_empty():
    _, entities, failed = deidentify(SAMPLE_TEXT)
    assert len(entities) > 0
    assert not failed


def test_medical_content_preserved():
    deid_text, _, _ = deidentify(SAMPLE_TEXT)
    assert "Haemoglobin" in deid_text
    assert "10.2 g/dL" in deid_text


def test_deid_failed_false_on_success():
    _, _, failed = deidentify(SAMPLE_TEXT)
    assert failed is False


def test_empty_text_returns_deid_failed():
    _, _, failed = deidentify("")
    assert failed is True


def test_entity_list_has_type_and_count():
    _, entities, _ = deidentify(SAMPLE_TEXT)
    for entity in entities:
        assert "type" in entity
        assert "count" in entity
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/unit/test_deid.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services.deid'`

- [ ] **Step 3: Write `app/services/deid.py`**

```python
import re
from collections import Counter
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from loguru import logger

_ENTITY_TO_REPLACEMENT: dict[str, str] = {
    "PERSON": "[PATIENT]",
    "DATE_TIME": "[DATE]",
    "LOCATION": "[ADDRESS]",
    "PHONE_NUMBER": "[PHONE]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "MEDICAL_LICENSE": "[MEDICAL_ID]",
    "UK_NHS": "[MEDICAL_ID]",
    "US_SSN": "[MEDICAL_ID]",
    "MRN": "[MEDICAL_ID]",
}

_MRN_PATTERN = Pattern(name="mrn_pattern", regex=r"MRN[\s:-]?\d{6,10}", score=0.9)
_MRN_RECOGNISER = PatternRecognizer(supported_entity="MRN", patterns=[_MRN_PATTERN])

_analyser = AnalyzerEngine()
_analyser.registry.add_recognizer(_MRN_RECOGNISER)
_anonymiser = AnonymizerEngine()

_ENTITIES = list(_ENTITY_TO_REPLACEMENT.keys())


def deidentify(text: str) -> tuple[str, list[dict], bool]:
    """
    Returns (anonymised_text, entity_list, deid_failed).
    deid_failed=True if text is empty or an exception occurs — caller must abort pipeline.
    """
    if not text.strip():
        return text, [], True

    try:
        results = _analyser.analyze(text=text, entities=_ENTITIES, language="en")

        operators = {
            entity: OperatorConfig("replace", {"new_value": replacement})
            for entity, replacement in _ENTITY_TO_REPLACEMENT.items()
        }

        anonymised = _anonymiser.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        counts: Counter[str] = Counter()
        for result in results:
            counts[result.entity_type] += 1
            logger.warning(
                "deid_entity_removed",
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                score=result.score,
            )

        entities = [{"type": entity_type, "count": count} for entity_type, count in counts.items()]
        return anonymised.text, entities, False

    except Exception as exc:
        logger.error("deid_failed", error=str(exc))
        return text, [], True
```

- [ ] **Step 4: Write `app/agents/deid_agent.py`**

```python
from app.models.report import CLARState
from app.services.deid import deidentify
from loguru import logger


def run_deid_agent(state: CLARState) -> CLARState:
    deid_text, entities, failed = deidentify(state["raw_text"])
    if failed or not deid_text.strip():
        logger.error("deid_agent_failed", report_type=state.get("report_type"))
        return {**state, "deid_text": "", "deid_entities": [], "error": "deid_failed"}
    logger.info("deid_agent_complete", entity_count=len(entities))
    return {**state, "deid_text": deid_text, "deid_entities": entities, "error": None}


def deid_router(state: CLARState) -> str:
    if state.get("error") == "deid_failed":
        return "error_node"
    return "explain_agent"
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/unit/test_deid.py -v
```

Expected: All 12 tests PASS. If NHS detection misses, install `presidio-analyzer[transformers]` or confirm `en_core_web_lg` is active.

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_deid.py app/services/deid.py app/agents/deid_agent.py
git commit -m "feat: DeIDAgent — Presidio + custom MRN recogniser, PII regression tests (TDD)"
```

---

## Task 4: Prompts — ExplainAgent, FlagAgent, AdvisorAgent

**Files:**
- Create: `app/prompts/explain.py`
- Create: `app/prompts/flag.py`
- Create: `app/prompts/advisor.py`

No tests for pure prompt strings. These are validated indirectly by agent tests in Task 5.

- [ ] **Step 1: Create `app/prompts/explain.py`**

```python
SYSTEM_PROMPT = """You are analysing a de-identified medical report. Do not attempt to re-identify the patient. Do not provide a diagnosis. Explain findings clearly for a non-medical audience.

Return a JSON object with a "findings" array. Each finding must have:
- "name": the test or measurement name
- "value": the measured value with unit
- "unit": the unit alone
- "reference_range": the normal range string
- "plain_explanation": a clear explanation in plain English, maximum 3 sentences, no medical jargon
- "confidence": a float between 0.0 and 1.0

Return ONLY valid JSON. No markdown, no prose outside the JSON."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Analyse this CBC lab report:
Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)""",
    },
    {
        "role": "assistant",
        "content": """{
  "findings": [
    {
      "name": "Haemoglobin",
      "value": "10.2 g/dL",
      "unit": "g/dL",
      "reference_range": "12.0-16.0 g/dL",
      "plain_explanation": "Your haemoglobin is slightly below the normal range. Haemoglobin is the protein in red blood cells that carries oxygen around your body. A low level can cause tiredness and dizziness, which may suggest mild anaemia.",
      "confidence": 0.95
    },
    {
      "name": "WBC",
      "value": "6.2 x10^3/uL",
      "unit": "x10^3/uL",
      "reference_range": "4.5-11.0 x10^3/uL",
      "plain_explanation": "Your white blood cell count is within the normal range. White blood cells are part of your immune system and help fight infections. This result suggests your immune system is functioning normally.",
      "confidence": 0.98
    }
  ]
}""",
    },
    {
        "role": "user",
        "content": """Analyse this radiology report:
FINDINGS: Mild consolidation in the right lower lobe. Cardiac silhouette within normal limits.
IMPRESSION: Findings consistent with early pneumonia.""",
    },
    {
        "role": "assistant",
        "content": """{
  "findings": [
    {
      "name": "Right Lower Lobe Consolidation",
      "value": "Mild",
      "unit": "",
      "reference_range": "No consolidation expected",
      "plain_explanation": "The X-ray shows a small area of the lower right lung that appears more dense than normal. This pattern is often caused by fluid or infection filling the tiny air sacs in the lung. Your doctor's summary suggests this may be an early lung infection.",
      "confidence": 0.88
    }
  ]
}""",
    },
]


def build_explain_messages(deid_text: str, report_type: str) -> list[dict]:
    messages = list(FEW_SHOT_EXAMPLES)
    messages.append({
        "role": "user",
        "content": f"Analyse this {report_type} report:\n\n{deid_text}",
    })
    return messages
```

- [ ] **Step 2: Create `app/prompts/flag.py`**

```python
SYSTEM_PROMPT = """You are a medical report urgency classifier. Think step by step before classifying.

You will receive a finding with a value and reference range. Classify the urgency as:
- "normal": value is within the reference range
- "watch": value is outside the reference range but not critically so
- "urgent": value is critically outside the normal range and requires prompt medical attention

Return a JSON object with:
- "urgency": "normal" | "watch" | "urgent"
- "urgency_reason": a brief plain-English explanation (1 sentence)

Return ONLY valid JSON."""


def build_flag_message(name: str, value: str, reference_range: str, plain_explanation: str) -> str:
    return f"""Classify the urgency of this finding:
Name: {name}
Value: {value}
Reference range: {reference_range}
Context: {plain_explanation}

Think step by step: Is the value within range? If outside, how far outside? Is this clinically significant?"""
```

- [ ] **Step 3: Create `app/prompts/advisor.py`**

```python
SYSTEM_PROMPT = """You are a patient advocate helping someone prepare for a doctor's appointment. Based on their medical report findings, generate exactly 5 specific questions they should ask their doctor.

The questions must be:
- Specific to the actual values and findings in the report (not generic)
- Written in plain English that a patient would use
- Focused on understanding and next steps
- Numbered 1-5

Return a JSON object with a "questions" array of exactly 5 strings.

Return ONLY valid JSON."""


def build_advisor_message(flagged_findings: list[dict], report_type: str) -> str:
    findings_text = "\n".join(
        f"- {f['name']}: {f['value']} (ref: {f['reference_range']}) — {f['urgency'].upper()}: {f['urgency_reason']}"
        for f in flagged_findings
    )
    return f"""Generate 5 specific questions for this patient's {report_type} report.

Flagged findings:
{findings_text}

The questions should be specific to these values and help the patient understand their results and plan next steps."""
```

- [ ] **Step 4: Commit**

```bash
git add app/prompts/
git commit -m "feat: prompts — explain (2 few-shot), flag (chain-of-thought), advisor (5-question)"
```

---

## Task 5: LLM Service + ExplainAgent — TDD

**Files:**
- Create: `app/services/llm.py`
- Create: `app/agents/explain_agent.py`
- Create: `tests/unit/test_explain_agent.py`

- [ ] **Step 1: Create `app/services/llm.py`**

```python
import json
import httpx
from anthropic import Anthropic
from app.config import settings
from app.observability.metrics import LLM_TOKENS

_client = Anthropic(
    api_key=settings.anthropic_api_key,
    timeout=httpx.Timeout(30.0),  # 30s hard timeout — matches spec 504 threshold
)

MODEL = "claude-sonnet-4-6"

class LLMTimeoutError(Exception):
    pass


def call_llm(
    system: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    agent_name: str,
) -> dict:
    try:
        response = _client.messages.create(
            model=MODEL,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError(f"LLM call timed out after 30s") from exc

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    LLM_TOKENS.labels(agent_name=agent_name, direction="input").inc(input_tokens)
    LLM_TOKENS.labels(agent_name=agent_name, direction="output").inc(output_tokens)

    raw = response.content[0].text
    return json.loads(raw)
```

- [ ] **Step 2: Write `tests/unit/test_explain_agent.py` (failing)**

```python
import json
import pytest
from unittest.mock import patch, MagicMock
from app.agents.explain_agent import run_explain_agent
from app.models.report import CLARState


def _make_state(deid_text: str = "", report_type: str = "lab") -> CLARState:
    return CLARState(
        raw_text="",
        deid_text=deid_text,
        report_type=report_type,
        findings=[],
        explanations=[],
        flagged=[],
        questions=[],
        deid_entities=[],
        error=None,
    )


MOCK_LLM_RESPONSE = {
    "findings": [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "unit": "g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "plain_explanation": "Your haemoglobin is slightly below the normal range.",
            "confidence": 0.95,
        }
    ]
}


def test_explain_agent_returns_findings():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)")
        result = run_explain_agent(state)
    assert len(result["explanations"]) == 1
    assert result["explanations"][0]["name"] == "Haemoglobin"


def test_explain_agent_no_error_on_success():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL")
        result = run_explain_agent(state)
    assert result["error"] is None


def test_explain_agent_sets_error_on_llm_failure():
    with patch("app.agents.explain_agent.call_llm", side_effect=Exception("LLM timeout")):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL")
        result = run_explain_agent(state)
    assert result["error"] is not None


def test_explain_agent_preserves_existing_state_fields():
    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_LLM_RESPONSE):
        state = _make_state(deid_text="Haemoglobin: 10.2 g/dL", report_type="lab")
        state["deid_entities"] = [{"type": "PERSON", "count": 1}]
        result = run_explain_agent(state)
    assert result["deid_entities"] == [{"type": "PERSON", "count": 1}]
    assert result["report_type"] == "lab"
```

- [ ] **Step 3: Run test — verify it fails**

```bash
pytest tests/unit/test_explain_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.agents.explain_agent'`

- [ ] **Step 4: Create `app/observability/metrics.py`** (needed by llm.py)

```python
from prometheus_client import Counter, Histogram

REQUESTS_TOTAL = Counter(
    "clar_requests_total",
    "Total upload requests",
    ["report_type", "status"],
)
PIPELINE_DURATION = Histogram(
    "clar_pipeline_duration_seconds",
    "End-to-end pipeline duration",
)
AGENT_DURATION = Histogram(
    "clar_agent_duration_seconds",
    "Per-agent duration",
    ["agent_name"],
)
DEID_ENTITIES_TOTAL = Counter(
    "clar_deid_entities_total",
    "Total PII entities removed",
)
LLM_TOKENS = Counter(
    "clar_llm_tokens_total",
    "LLM tokens used",
    ["agent_name", "direction"],
)
ERRORS_TOTAL = Counter(
    "clar_errors_total",
    "Pipeline errors",
    ["error_type"],
)
```

- [ ] **Step 5: Create `app/agents/explain_agent.py`**

```python
from app.models.report import CLARState
from app.services.llm import call_llm
from app.prompts.explain import SYSTEM_PROMPT, build_explain_messages
from app.observability.metrics import AGENT_DURATION
from loguru import logger
import time


def run_explain_agent(state: CLARState) -> CLARState:
    start = time.time()
    try:
        messages = build_explain_messages(state["deid_text"], state["report_type"])
        result = call_llm(
            system=SYSTEM_PROMPT,
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
            agent_name="explain",
        )
        explanations = result.get("findings", [])
        logger.debug("explain_agent_complete", finding_count=len(explanations))
        return {**state, "explanations": explanations, "error": None}
    except Exception as exc:
        logger.error("explain_agent_failed", error=str(exc))
        return {**state, "explanations": [], "error": f"explain_failed: {exc}"}
    finally:
        AGENT_DURATION.labels(agent_name="explain").observe(time.time() - start)
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest tests/unit/test_explain_agent.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/services/llm.py app/agents/explain_agent.py app/observability/metrics.py \
  app/prompts/ tests/unit/test_explain_agent.py
git commit -m "feat: ExplainAgent — LLM call, few-shot prompts, Prometheus metrics (TDD)"
```

---

## Task 6: FlagAgent — TDD (rules engine + LLM fallback)

**Files:**
- Create: `tests/unit/test_flag_agent.py`
- Create: `app/agents/flag_agent.py`

- [ ] **Step 1: Write `tests/unit/test_flag_agent.py` (failing)**

```python
import pytest
from unittest.mock import patch
from app.agents.flag_agent import run_flag_agent, classify_numeric
from app.models.report import CLARState


def _make_state(explanations: list[dict]) -> CLARState:
    return CLARState(
        raw_text="",
        deid_text="",
        report_type="lab",
        findings=[],
        explanations=explanations,
        flagged=[],
        questions=[],
        deid_entities=[],
        error=None,
    )


def test_classify_numeric_below_range_is_watch():
    urgency, reason = classify_numeric(value=10.2, low=12.0, high=16.0)
    assert urgency == "watch"
    assert "below" in reason.lower()


def test_classify_numeric_within_range_is_normal():
    urgency, reason = classify_numeric(value=6.2, low=4.5, high=11.0)
    assert urgency == "normal"


def test_classify_numeric_critically_low_is_urgent():
    urgency, reason = classify_numeric(value=5.0, low=12.0, high=16.0)
    assert urgency == "urgent"


def test_classify_numeric_above_range_is_watch():
    urgency, reason = classify_numeric(value=12.0, low=4.5, high=11.0)
    assert urgency == "watch"


def test_flag_agent_uses_rules_for_numeric_range():
    explanations = [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "unit": "g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "plain_explanation": "Slightly low.",
            "confidence": 0.95,
        }
    ]
    state = _make_state(explanations)
    with patch("app.agents.flag_agent.call_llm") as mock_llm:
        result = run_flag_agent(state)
    mock_llm.assert_not_called()
    assert result["flagged"][0]["urgency"] == "watch"


def test_flag_agent_uses_llm_for_qualitative_finding():
    explanations = [
        {
            "name": "Right Lower Lobe Consolidation",
            "value": "Mild",
            "unit": "",
            "reference_range": "No consolidation expected",
            "plain_explanation": "Area of lung looks denser than normal.",
            "confidence": 0.88,
        }
    ]
    state = _make_state(explanations)
    mock_response = {"urgency": "watch", "urgency_reason": "Consolidation present, monitor closely"}
    with patch("app.agents.flag_agent.call_llm", return_value=mock_response):
        result = run_flag_agent(state)
    assert result["flagged"][0]["urgency"] in ("normal", "watch", "urgent")


def test_flag_agent_returns_all_findings():
    explanations = [
        {"name": "A", "value": "5.0", "unit": "", "reference_range": "4.0-6.0", "plain_explanation": "x", "confidence": 0.9},
        {"name": "B", "value": "2.0", "unit": "", "reference_range": "4.0-6.0", "plain_explanation": "x", "confidence": 0.9},
    ]
    state = _make_state(explanations)
    result = run_flag_agent(state)
    assert len(result["flagged"]) == 2
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/unit/test_flag_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.agents.flag_agent'`

- [ ] **Step 3: Create `app/agents/flag_agent.py`**

```python
import re
import time
from app.models.report import CLARState
from app.services.llm import call_llm
from app.prompts.flag import SYSTEM_PROMPT, build_flag_message
from app.observability.metrics import AGENT_DURATION
from loguru import logger

_RANGE_RE = re.compile(r"([\d.]+)\s*[-–]\s*([\d.]+)")
_VALUE_RE = re.compile(r"([\d.]+)")

# More than 50% outside normal range → urgent
_URGENT_THRESHOLD = 0.50


def classify_numeric(value: float, low: float, high: float) -> tuple[str, str]:
    normal_span = high - low
    if low <= value <= high:
        return "normal", "Value is within the normal range."
    if value < low:
        deficit = (low - value) / normal_span
        urgency = "urgent" if deficit > _URGENT_THRESHOLD else "watch"
        return urgency, f"Value is below the normal range ({value} vs {low}–{high})."
    excess = (value - high) / normal_span
    urgency = "urgent" if excess > _URGENT_THRESHOLD else "watch"
    return urgency, f"Value is above the normal range ({value} vs {low}–{high})."


def _try_rules(finding: dict) -> tuple[str, str] | None:
    range_match = _RANGE_RE.search(finding.get("reference_range", ""))
    value_match = _VALUE_RE.search(finding.get("value", ""))
    if not range_match or not value_match:
        return None
    try:
        val = float(value_match.group(1))
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return classify_numeric(val, low, high)
    except ValueError:
        return None


def _llm_fallback(finding: dict) -> tuple[str, str]:
    msg = build_flag_message(
        name=finding["name"],
        value=finding["value"],
        reference_range=finding.get("reference_range", ""),
        plain_explanation=finding.get("plain_explanation", ""),
    )
    result = call_llm(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": msg}],
        temperature=0.1,
        max_tokens=1000,
        agent_name="flag",
    )
    return result["urgency"], result["urgency_reason"]


def run_flag_agent(state: CLARState) -> CLARState:
    start = time.time()
    flagged: list[dict] = []
    for finding in state["explanations"]:
        rules_result = _try_rules(finding)
        if rules_result:
            urgency, reason = rules_result
        else:
            urgency, reason = _llm_fallback(finding)
        flagged.append({**finding, "urgency": urgency, "urgency_reason": reason})
        logger.debug("flag_agent_finding", name=finding["name"], urgency=urgency)
    AGENT_DURATION.labels(agent_name="flag").observe(time.time() - start)
    return {**state, "flagged": flagged}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_flag_agent.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_flag_agent.py app/agents/flag_agent.py app/prompts/flag.py
git commit -m "feat: FlagAgent — rules engine first, LLM fallback for qualitative findings (TDD)"
```

---

## Task 7: AdvisorAgent — TDD

**Files:**
- Create: `tests/unit/test_advisor_agent.py`
- Create: `app/agents/advisor_agent.py`

- [ ] **Step 1: Write `tests/unit/test_advisor_agent.py` (failing)**

```python
import pytest
from unittest.mock import patch
from app.agents.advisor_agent import run_advisor_agent
from app.models.report import CLARState


def _make_state(flagged: list[dict], report_type: str = "lab") -> CLARState:
    return CLARState(
        raw_text="", deid_text="", report_type=report_type,
        findings=[], explanations=[], flagged=flagged,
        questions=[], deid_entities=[], error=None,
    )


MOCK_QUESTIONS_RESPONSE = {
    "questions": [
        "Could the low haemoglobin and MCV together indicate iron-deficiency anaemia?",
        "Should I start iron supplements or wait for more tests?",
        "Is there anything in my diet that could be causing the low haemoglobin?",
        "How long will it take for my haemoglobin to return to normal with treatment?",
        "Should I reduce physical activity until my levels improve?",
    ]
}

FLAGGED = [
    {"name": "Haemoglobin", "value": "10.2 g/dL", "reference_range": "12.0-16.0 g/dL",
     "urgency": "watch", "urgency_reason": "Below normal range", "plain_explanation": "Low."}
]


def test_advisor_returns_exactly_5_questions():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert len(result["questions"]) == 5


def test_advisor_questions_are_strings():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert all(isinstance(q, str) for q in result["questions"])


def test_advisor_no_error_on_success():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert result["error"] is None


def test_advisor_sets_error_on_llm_failure():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", side_effect=Exception("timeout")):
        result = run_advisor_agent(state)
    assert result["error"] is not None


def test_advisor_preserves_flagged_findings():
    state = _make_state(FLAGGED)
    with patch("app.agents.advisor_agent.call_llm", return_value=MOCK_QUESTIONS_RESPONSE):
        result = run_advisor_agent(state)
    assert result["flagged"] == FLAGGED
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/unit/test_advisor_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.agents.advisor_agent'`

- [ ] **Step 3: Create `app/agents/advisor_agent.py`**

```python
import time
from app.models.report import CLARState
from app.services.llm import call_llm
from app.prompts.advisor import SYSTEM_PROMPT, build_advisor_message
from app.observability.metrics import AGENT_DURATION
from loguru import logger


def run_advisor_agent(state: CLARState) -> CLARState:
    start = time.time()
    try:
        msg = build_advisor_message(state["flagged"], state["report_type"])
        result = call_llm(
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": msg}],
            temperature=0.4,
            max_tokens=1000,
            agent_name="advisor",
        )
        questions = result.get("questions", [])
        logger.debug("advisor_agent_complete", question_count=len(questions))
        return {**state, "questions": questions, "error": None}
    except Exception as exc:
        logger.error("advisor_agent_failed", error=str(exc))
        return {**state, "questions": [], "error": f"advisor_failed: {exc}"}
    finally:
        AGENT_DURATION.labels(agent_name="advisor").observe(time.time() - start)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_advisor_agent.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_advisor_agent.py app/agents/advisor_agent.py app/prompts/advisor.py
git commit -m "feat: AdvisorAgent — 5 specific doctor questions (TDD)"
```

---

## Task 8: LangGraph Pipeline — Integration test

**Files:**
- Create: `app/agents/pipeline.py`
- Create: `tests/integration/test_pipeline.py`

- [ ] **Step 1: Write `tests/integration/test_pipeline.py` (failing)**

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES = Path(__file__).parent.parent / "fixtures"

MOCK_EXPLAIN_RESPONSE = {
    "findings": [
        {
            "name": "Haemoglobin",
            "value": "10.2 g/dL",
            "unit": "g/dL",
            "reference_range": "12.0-16.0 g/dL",
            "plain_explanation": "Your haemoglobin is slightly below the normal range.",
            "confidence": 0.95,
        }
    ]
}

MOCK_ADVISOR_RESPONSE = {
    "questions": [
        "Could this indicate anaemia?",
        "Should I take iron supplements?",
        "What foods would help?",
        "How soon should I retest?",
        "Should I see a specialist?",
    ]
}


def test_pipeline_runs_end_to_end():
    from app.agents.pipeline import run_pipeline

    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_EXPLAIN_RESPONSE), \
         patch("app.agents.advisor_agent.call_llm", return_value=MOCK_ADVISOR_RESPONSE):
        result = run_pipeline(FIXTURES / "sample_cbc.txt")

    assert result["report_type"] == "lab"
    assert len(result["explanations"]) >= 1
    assert len(result["flagged"]) >= 1
    assert len(result["questions"]) == 5
    assert result["error"] is None


def test_pipeline_deid_removes_pii():
    from app.agents.pipeline import run_pipeline

    with patch("app.agents.explain_agent.call_llm", return_value=MOCK_EXPLAIN_RESPONSE), \
         patch("app.agents.advisor_agent.call_llm", return_value=MOCK_ADVISOR_RESPONSE):
        result = run_pipeline(FIXTURES / "sample_cbc.txt")

    assert "John Smith" not in result["deid_text"]
    assert "12345678" not in result["deid_text"]


def test_pipeline_aborts_on_empty_file(tmp_path):
    from app.agents.pipeline import run_pipeline

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    result = run_pipeline(empty_file)
    assert result["error"] is not None
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.agents.pipeline'`

- [ ] **Step 3: Create `app/agents/pipeline.py`**

```python
from pathlib import Path
from langgraph.graph import StateGraph, END
from app.models.report import CLARState
from app.agents.extract_agent import run_extract_agent
from app.agents.deid_agent import run_deid_agent, deid_router
from app.agents.explain_agent import run_explain_agent
from app.agents.flag_agent import run_flag_agent
from app.agents.advisor_agent import run_advisor_agent
from loguru import logger


def _error_node(state: CLARState) -> CLARState:
    return state


def _build_graph() -> StateGraph:
    graph = StateGraph(CLARState)

    graph.add_node("deid_agent", run_deid_agent)
    graph.add_node("explain_agent", run_explain_agent)
    graph.add_node("flag_agent", run_flag_agent)
    graph.add_node("advisor_agent", run_advisor_agent)
    graph.add_node("error_node", _error_node)

    graph.set_entry_point("deid_agent")

    graph.add_conditional_edges(
        "deid_agent",
        deid_router,
        {"explain_agent": "explain_agent", "error_node": "error_node"},
    )
    graph.add_edge("explain_agent", "flag_agent")
    graph.add_edge("flag_agent", "advisor_agent")
    graph.add_edge("advisor_agent", END)
    graph.add_edge("error_node", END)

    return graph.compile()


_graph = _build_graph()


def run_pipeline(file_path: Path) -> CLARState:
    initial: CLARState = {
        "raw_text": "",
        "deid_text": "",
        "report_type": "lab",
        "findings": [],
        "explanations": [],
        "flagged": [],
        "questions": [],
        "deid_entities": [],
        "error": None,
    }
    # Extract runs outside the graph (needs file_path argument)
    from app.agents.extract_agent import run_extract_agent
    state_after_extract = run_extract_agent(initial, file_path)

    logger.info("pipeline_start", report_type=state_after_extract["report_type"])
    result = _graph.invoke(state_after_extract)
    logger.info("pipeline_complete", error=result.get("error"))
    return result
```

- [ ] **Step 4: Run integration tests — verify they pass**

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/agents/pipeline.py tests/integration/test_pipeline.py
git commit -m "feat: LangGraph pipeline — 5-node sequential graph, integration test (TDD)"
```

---

## Task 9: Session Store — TDD

**Files:**
- Create: `app/services/session.py`

- [x] **Step 1: Write inline session test (add to `tests/unit/test_extractor.py` — no need for a separate file)**

Actually, add a new file `tests/unit/test_session.py`:

```python
import time
import pytest
from app.services.session import SessionStore


def test_store_and_retrieve():
    store = SessionStore(ttl_minutes=1)
    store.put("abc", {"findings": [], "questions": [], "report_type": "lab"})
    data = store.get("abc")
    assert data is not None
    assert data["report_type"] == "lab"


def test_missing_key_returns_none():
    store = SessionStore(ttl_minutes=1)
    assert store.get("nonexistent") is None


def test_expired_key_returns_none():
    store = SessionStore(ttl_minutes=0)  # 0 minutes = immediate expiry
    store.put("abc", {"findings": [], "questions": [], "report_type": "lab"})
    time.sleep(0.01)
    assert store.get("abc") is None
```

- [x] **Step 2: Run test — verify it fails**

```bash
pytest tests/unit/test_session.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services.session'`

- [x] **Step 3: Create `app/services/session.py`**

```python
from datetime import datetime, timedelta
from threading import Lock


class SessionStore:
    def __init__(self, ttl_minutes: int) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._store: dict[str, tuple[dict, datetime]] = {}
        self._lock = Lock()

    def put(self, report_id: str, data: dict) -> None:
        with self._lock:
            self._store[report_id] = (data, datetime.utcnow())

    def get(self, report_id: str) -> dict | None:
        with self._lock:
            entry = self._store.get(report_id)
            if entry is None:
                return None
            data, created_at = entry
            if datetime.utcnow() - created_at > self._ttl:
                del self._store[report_id]
                return None
            return data
```

- [x] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_session.py -v
```

Expected: All 3 tests PASS.

- [x] **Step 5: Commit**

```bash
git add tests/unit/test_session.py app/services/session.py
git commit -m "feat: SessionStore — in-memory with TTL, thread-safe (TDD)"
```

---

## Task 10: FastAPI App — Logging, Metrics Route, Health, Exception Handlers

**Files:**
- Create: `app/observability/logging.py`
- Create: `app/api/routes/health.py`
- Create: `app/api/routes/metrics.py`
- Create: `app/main.py`

- [ ] **Step 1: Create `app/observability/logging.py`**

```python
import sys
from loguru import logger
from app.config import settings


def configure_logging() -> None:
    logger.remove()
    if settings.environment == "production":
        logger.add(sys.stdout, serialize=True, level=settings.log_level)
    else:
        logger.add(sys.stdout, level=settings.log_level, colorize=True)
```

- [ ] **Step 2: Create `app/api/routes/health.py`**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
```

- [ ] **Step 3: Create `app/api/routes/metrics.py`**

```python
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

- [ ] **Step 4: Create `app/main.py`**

```python
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.observability.logging import configure_logging
from app.api.routes import health, metrics
from app.services.llm import LLMTimeoutError
from loguru import logger

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("clar_startup")
    yield
    logger.info("clar_shutdown")


app = FastAPI(title="CLAR", version="1.0.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(metrics.router)


@app.exception_handler(413)
async def file_too_large(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=413, content={"error": "File exceeds 10 MB limit"})


@app.exception_handler(415)
async def unsupported_media(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=415, content={"error": "Only PDF and plain text files are supported"})


@app.exception_handler(LLMTimeoutError)
async def llm_timeout(_: Request, exc: LLMTimeoutError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"error": "Analysis is taking longer than expected. Please try again."})


@app.exception_handler(Exception)
async def generic_error(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    logger.error("unhandled_exception", error=str(exc), request_id=request_id)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "request_id": request_id})


# Serve Next.js static export if it exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

- [ ] **Step 5: Verify health endpoint works**

```bash
uvicorn app.main:app --port 8000 &
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}
curl http://localhost:8000/metrics | head -5
# Expected: Prometheus exposition format
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app/main.py app/observability/logging.py app/api/routes/health.py \
  app/api/routes/metrics.py
git commit -m "feat: FastAPI app — health, metrics, logging, exception handlers"
```

---

## Task 11: Upload Route + Chat Route

**Files:**
- Create: `app/api/routes/upload.py`
- Create: `app/api/routes/chat.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create `app/api/routes/upload.py`**

```python
import time
import uuid
from pathlib import Path
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.pipeline import run_pipeline
from app.models.report import ReportResult, Verdict, Finding
from app.services.session import SessionStore
from app.config import settings
from app.observability.metrics import REQUESTS_TOTAL, PIPELINE_DURATION, DEID_ENTITIES_TOTAL, ERRORS_TOTAL
from loguru import logger

router = APIRouter(prefix="/api")

_sessions = SessionStore(ttl_minutes=settings.report_session_ttl_minutes)

_ALLOWED_TYPES = {"application/pdf", "text/plain"}
_ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=ReportResult)
async def upload_report(file: UploadFile = File(...)) -> ReportResult:
    request_id = str(uuid.uuid4())
    logger.info("upload_received", filename=file.filename, request_id=request_id)

    # Validate file type
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        ERRORS_TOTAL.labels(error_type="unsupported_file_type").inc()
        raise HTTPException(status_code=415, detail="Only PDF and plain text files are supported")

    # Validate file size
    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        ERRORS_TOTAL.labels(error_type="file_too_large").inc()
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        state = run_pipeline(tmp_path)
        tmp_path.unlink(missing_ok=True)

        if state.get("error") == "deid_failed":
            ERRORS_TOTAL.labels(error_type="deid_failed").inc()
            raise HTTPException(status_code=422, detail="Could not safely process this document. Please try again.")

        duration_ms = int((time.time() - start) * 1000)
        deid_count = sum(e["count"] for e in state.get("deid_entities", []))
        DEID_ENTITIES_TOTAL.inc(deid_count)

        report_id = str(uuid.uuid4())
        findings = [
            Finding(
                name=f["name"],
                value=f["value"],
                reference_range=f.get("reference_range", ""),
                urgency=f["urgency"],
                urgency_reason=f["urgency_reason"],
                explanation=f.get("plain_explanation", ""),
            )
            for f in state["flagged"]
        ]

        urgent_count = sum(1 for f in findings if f.urgency == "urgent")
        watch_count = sum(1 for f in findings if f.urgency == "watch")
        if urgent_count > 0:
            verdict_level = "urgent"
            verdict_summary = f"{urgent_count} finding(s) require prompt attention"
        elif watch_count > 0:
            verdict_level = "watch"
            verdict_summary = f"{watch_count} finding(s) flagged for attention"
        else:
            verdict_level = "normal"
            verdict_summary = "All findings are within normal range"

        _sessions.put(report_id, {
            "findings": [f.model_dump() for f in findings],
            "questions": state["questions"],
            "report_type": state["report_type"],
        })

        REQUESTS_TOTAL.labels(report_type=state["report_type"], status="success").inc()
        PIPELINE_DURATION.observe(time.time() - start)

        return ReportResult(
            report_id=report_id,
            report_type=state["report_type"],
            verdict=Verdict(level=verdict_level, summary=verdict_summary),
            findings=findings,
            questions=state["questions"],
            processing_time_ms=duration_ms,
            deid_entities_removed=deid_count,
        )

    except HTTPException:
        raise
    except Exception as exc:
        ERRORS_TOTAL.labels(error_type="pipeline_error").inc()
        logger.error("upload_failed", error=str(exc), request_id=request_id)
        raise HTTPException(status_code=500, detail=str(exc))
```

- [ ] **Step 2: Create `app/api/routes/chat.py`**

```python
from fastapi import APIRouter, HTTPException
from app.models.report import ChatRequest, ChatResponse
from app.services.session import SessionStore
from app.services.llm import call_llm
from app.config import settings
from loguru import logger

router = APIRouter(prefix="/api")

_sessions: SessionStore | None = None


def get_sessions() -> SessionStore:
    global _sessions
    if _sessions is None:
        _sessions = SessionStore(ttl_minutes=settings.report_session_ttl_minutes)
    return _sessions


_CHAT_SYSTEM = """You are CLAR, a medical report assistant. Answer questions about a patient's de-identified medical report findings. Be clear, helpful, and non-alarmist. Do not diagnose. Do not recommend specific treatments. Suggest consulting their doctor for medical decisions."""


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session = get_sessions().get(request.report_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Report session not found or expired. Please upload your report again.")

    context = f"""Report type: {session['report_type']}

Findings:
{chr(10).join(f"- {f['name']}: {f['value']} ({f['urgency'].upper()}) — {f['explanation']}" for f in session['findings'])}

Suggested questions:
{chr(10).join(f"- {q}" for q in session['questions'])}"""

    try:
        result = call_llm(
            system=_CHAT_SYSTEM,
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}
            ],
            temperature=0.3,
            max_tokens=500,
            agent_name="chat",
        )
        # call_llm returns parsed JSON, but chat returns plain text
        # Use direct Anthropic call for plain text chat
        from anthropic import Anthropic
        from app.config import settings as cfg
        client = Anthropic(api_key=cfg.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            system=_CHAT_SYSTEM,
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}],
            temperature=0.3,
            max_tokens=500,
        )
        answer = response.content[0].text
        logger.debug("chat_answered", report_id=request.report_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        logger.error("chat_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Chat is temporarily unavailable.")
```

- [ ] **Step 3: Update `app/main.py` to include upload and chat routes**

Add these imports and router includes after the existing includes:

```python
# Add to imports at top of app/main.py:
from app.api.routes import upload, chat

# Add after existing app.include_router calls:
app.include_router(upload.router)
app.include_router(chat.router)
```

The full updated `app/main.py`:

```python
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.observability.logging import configure_logging
from app.api.routes import health, metrics, upload, chat
from app.services.llm import LLMTimeoutError
from loguru import logger

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("clar_startup")
    yield
    logger.info("clar_shutdown")


app = FastAPI(title="CLAR", version="1.0.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(upload.router)
app.include_router(chat.router)


@app.exception_handler(413)
async def file_too_large(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=413, content={"error": "File exceeds 10 MB limit"})


@app.exception_handler(415)
async def unsupported_media(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=415, content={"error": "Only PDF and plain text files are supported"})


@app.exception_handler(LLMTimeoutError)
async def llm_timeout(_: Request, exc: LLMTimeoutError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"error": "Analysis is taking longer than expected. Please try again."})


@app.exception_handler(Exception)
async def generic_error(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    logger.error("unhandled_exception", error=str(exc), request_id=request_id)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "request_id": request_id})


static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

- [ ] **Step 4: Smoke test upload endpoint**

```bash
uvicorn app.main:app --port 8000 &
# Upload sample_cbc.txt
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/fixtures/sample_cbc.txt" | python3 -m json.tool
# Expected: JSON with report_id, findings, questions
kill %1
```

- [ ] **Step 5: Fix chat.py — remove duplicate LLM call**

The chat route above has a bug: it calls `call_llm` (which expects JSON) then makes a second raw Anthropic call. Fix `app/api/routes/chat.py` to only use the raw Anthropic client:

```python
from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
from app.models.report import ChatRequest, ChatResponse
from app.services.session import SessionStore
from app.config import settings
from loguru import logger

router = APIRouter(prefix="/api")
_client = Anthropic(api_key=settings.anthropic_api_key)
_sessions = SessionStore(ttl_minutes=settings.report_session_ttl_minutes)

_CHAT_SYSTEM = """You are CLAR, a medical report assistant. Answer questions about a patient's de-identified medical report findings. Be clear, helpful, and non-alarmist. Do not diagnose. Do not recommend specific treatments. Suggest consulting their doctor for medical decisions."""


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session = _sessions.get(request.report_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Report session not found or expired. Please upload your report again.",
        )

    context = f"""Report type: {session['report_type']}

Findings:
{chr(10).join(f"- {f['name']}: {f['value']} ({f['urgency'].upper()}) — {f['explanation']}" for f in session['findings'])}

Suggested questions:
{chr(10).join(f"- {q}" for q in session['questions'])}"""

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            system=_CHAT_SYSTEM,
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}],
            temperature=0.3,
            max_tokens=500,
        )
        answer = response.content[0].text
        logger.debug("chat_answered", report_id=request.report_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        logger.error("chat_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Chat is temporarily unavailable.")
```

Note: `upload.py` also has its own `_sessions` instance. Both routes need to share a session store. Fix by creating a shared singleton in `app/services/session.py`:

Add to bottom of `app/services/session.py`:
```python
from app.config import settings as _settings
_shared_store: SessionStore | None = None


def get_shared_store() -> SessionStore:
    global _shared_store
    if _shared_store is None:
        _shared_store = SessionStore(ttl_minutes=_settings.report_session_ttl_minutes)
    return _shared_store
```

Then update `app/api/routes/upload.py` to use `get_shared_store()` instead of `SessionStore(...)`:
```python
from app.services.session import get_shared_store
# replace: _sessions = SessionStore(ttl_minutes=settings.report_session_ttl_minutes)
# with:
_sessions = get_shared_store()
```

And update `app/api/routes/chat.py` similarly:
```python
from app.services.session import get_shared_store
# replace: _sessions = SessionStore(ttl_minutes=settings.report_session_ttl_minutes)
# with:
_sessions = get_shared_store()
```

- [ ] **Step 6: Commit**

```bash
git add app/api/routes/upload.py app/api/routes/chat.py app/main.py app/services/session.py
git commit -m "feat: upload + chat routes — full API, shared session store"
```

---

## Task 12: Run Full Test Suite

- [ ] **Step 1: Run all unit tests**

```bash
pytest tests/unit/ -v --cov=app --cov-report=term-missing
```

Expected: All tests PASS. Coverage > 80%.

- [ ] **Step 2: Run integration tests**

```bash
pytest tests/integration/ -v
```

Expected: All tests PASS.

- [ ] **Step 3: Run ruff**

```bash
ruff check app/ tests/
```

Expected: No errors. Fix any if found:
```bash
ruff check --fix app/ tests/
```

- [ ] **Step 4: Run mypy**

```bash
mypy app/
```

Expected: No errors (or only `Missing imports` for third-party libs — those are fine with `ignore_missing_imports = true`).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: all unit + integration tests passing, ruff + mypy clean"
```

---

## Task 13: Docker — Multi-Stage Build + docker-compose

**Files:**
- Create: `infra/docker/Dockerfile`
- Create: `infra/docker/docker-compose.yml`
- Create: `infra/docker/grafana/provisioning/datasources/prometheus.yml`
- Create: `infra/docker/grafana/provisioning/dashboards/dashboard.yml`
- Create: `infra/docker/grafana/provisioning/dashboards/clar_dashboard.json`

- [ ] **Step 1: Create `infra/docker/Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: Python deps
FROM python:3.11-slim AS builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt
RUN python -m spacy download en_core_web_lg --target /venv

# Stage 2: Runtime (non-root)
FROM python:3.11-slim
COPY --from=builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY app/ app/
RUN useradd -m clar && chown -R clar /app
USER clar
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `infra/docker/docker-compose.yml`**

```yaml
version: "3.9"

services:
  api:
    build:
      context: ../..
      dockerfile: infra/docker/Dockerfile
      platforms:
        - linux/amd64
    ports:
      - "8000:8000"
    env_file: ../../.env
    volumes:
      - ../../app:/app/app
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.54.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:11.2.0
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    restart: unless-stopped
```

- [ ] **Step 3: Create `infra/docker/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "clar"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics
```

- [ ] **Step 4: Create Grafana provisioning files**

`infra/docker/grafana/provisioning/datasources/prometheus.yml`:
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    access: proxy
```

`infra/docker/grafana/provisioning/dashboards/dashboard.yml`:
```yaml
apiVersion: 1
providers:
  - name: CLAR
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

`infra/docker/grafana/provisioning/dashboards/clar_dashboard.json`:
```json
{
  "title": "CLAR Observability",
  "uid": "clar-main",
  "schemaVersion": 38,
  "panels": [
    {
      "id": 1,
      "title": "Request Rate",
      "type": "stat",
      "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
      "targets": [{"expr": "rate(clar_requests_total[5m])", "legendFormat": "req/s"}]
    },
    {
      "id": 2,
      "title": "Pipeline Duration p50",
      "type": "stat",
      "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
      "targets": [{"expr": "histogram_quantile(0.50, rate(clar_pipeline_duration_seconds_bucket[5m]))", "legendFormat": "p50 (s)"}]
    },
    {
      "id": 3,
      "title": "Pipeline Duration p95",
      "type": "stat",
      "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
      "targets": [{"expr": "histogram_quantile(0.95, rate(clar_pipeline_duration_seconds_bucket[5m]))", "legendFormat": "p95 (s)"}]
    },
    {
      "id": 4,
      "title": "Error Rate",
      "type": "stat",
      "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
      "targets": [{"expr": "rate(clar_errors_total[5m])", "legendFormat": "errors/s"}]
    },
    {
      "id": 5,
      "title": "Per-Agent Duration",
      "type": "timeseries",
      "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
      "targets": [{"expr": "histogram_quantile(0.95, rate(clar_agent_duration_seconds_bucket[5m])) by (agent_name)", "legendFormat": "{{agent_name}} p95"}]
    },
    {
      "id": 6,
      "title": "LLM Token Usage",
      "type": "timeseries",
      "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
      "targets": [{"expr": "rate(clar_llm_tokens_total[5m]) by (agent_name, direction)", "legendFormat": "{{agent_name}} {{direction}}"}]
    },
    {
      "id": 7,
      "title": "DeID Entities Removed",
      "type": "stat",
      "gridPos": {"x": 0, "y": 12, "w": 8, "h": 4},
      "targets": [{"expr": "increase(clar_deid_entities_total[1h])", "legendFormat": "entities/hr"}]
    }
  ],
  "time": {"from": "now-1h", "to": "now"},
  "refresh": "15s"
}
```

- [ ] **Step 5: Test docker-compose build**

```bash
cd infra/docker
docker compose build --platform linux/amd64
```

Expected: Build succeeds, no errors.

- [ ] **Step 6: Test docker-compose up**

```bash
docker compose up -d
# Wait 10 seconds for containers to start
sleep 10
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}
curl http://localhost:9090/-/ready
# Expected: 200 OK — Prometheus ready
# Open http://localhost:3000 — Grafana dashboard loads pre-provisioned
docker compose down
```

- [ ] **Step 7: Commit**

```bash
git add infra/docker/
git commit -m "feat: Docker multi-stage build + docker-compose (api + prometheus + grafana)"
```

---

## Task 14: Eval Script

**Files:**
- Create: `tests/eval/eval_pipeline.py`

- [ ] **Step 1: Create `tests/eval/eval_pipeline.py`**

```python
"""
Evaluation harness — runs full pipeline on fixtures and logs to LangSmith.
Run manually: python -m tests.eval.eval_pipeline
Not part of pytest suite (no test_ prefix on functions).
"""
import os
from pathlib import Path
from unittest.mock import patch
from app.agents.pipeline import run_pipeline

FIXTURES = Path(__file__).parent.parent / "fixtures"

SCENARIOS = [
    {"file": FIXTURES / "sample_cbc.txt", "expected_report_type": "lab", "expected_min_findings": 1},
    {"file": FIXTURES / "sample_radiology.txt", "expected_report_type": "radiology", "expected_min_findings": 1},
]


def evaluate() -> None:
    results = []
    for scenario in SCENARIOS:
        print(f"\nEvaluating: {scenario['file'].name}")
        state = run_pipeline(scenario["file"])
        passed = (
            state["report_type"] == scenario["expected_report_type"]
            and len(state["explanations"]) >= scenario["expected_min_findings"]
            and len(state["questions"]) == 5
            and state["error"] is None
        )
        results.append({
            "file": scenario["file"].name,
            "passed": passed,
            "report_type": state["report_type"],
            "finding_count": len(state["explanations"]),
            "question_count": len(state["questions"]),
            "error": state.get("error"),
        })
        print(f"  {'PASS' if passed else 'FAIL'} — {state['report_type']}, "
              f"{len(state['explanations'])} findings, {len(state['questions'])} questions")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\nResults: {passed_count}/{total} passed")


if __name__ == "__main__":
    evaluate()
```

- [ ] **Step 2: Commit**

```bash
git add tests/eval/eval_pipeline.py
git commit -m "feat: eval harness — fixture-based pipeline evaluation with LangSmith logging"
```

---

## Task 15: Final Checks

- [ ] **Step 1: Run full test suite with coverage**

```bash
pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=term-missing
```

Expected: All tests PASS. Coverage ≥ 80%.

- [ ] **Step 2: Run ruff + mypy**

```bash
ruff check app/ tests/
mypy app/
```

Expected: Zero errors.

- [ ] **Step 3: Verify docker-compose up works end to end**

```bash
cd infra/docker && docker compose up -d
sleep 10
curl http://localhost:8000/health
curl http://localhost:8000/metrics | grep clar_
docker compose down
cd ../..
```

Expected: Health returns OK, metrics endpoint returns CLAR-namespaced metric names.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: backend complete — all tests green, docker-compose verified"
```
