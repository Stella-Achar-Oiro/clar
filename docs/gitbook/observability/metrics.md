# Health & Metrics

## Health check

```
GET /health
```

Returns `{"status": "ok", "version": "1.0.0"}` when the service is running normally. Used by Cloud Run's startup and liveness probes.

## Prometheus metrics

```
GET /metrics
```

CLAR exposes Prometheus-compatible metrics at `/metrics`. These include:

| Metric | Type | Description |
|---|---|---|
| `http_requests_total` | Counter | Total HTTP requests, labelled by method, endpoint, and status code |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `report_processing_duration_seconds` | Histogram | End-to-end report processing time |
| `llm_calls_total` | Counter | LLM API calls made, labelled by outcome |

### Scraping

Point your Prometheus instance at `https://<base-url>/metrics`. The endpoint returns plain text in the standard Prometheus exposition format.

### Example output

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/report",status="200"} 47.0
http_requests_total{method="GET",endpoint="/health",status="200"} 1203.0
```

## LLM tracing

CLAR integrates with [LangSmith](https://smith.langchain.com) for LLM call tracing. When configured, every LLM call is recorded with:

- Input prompt
- Model response
- Latency
- Token counts

Traces are visible in the LangSmith dashboard under the configured project name.
