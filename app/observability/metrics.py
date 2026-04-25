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
