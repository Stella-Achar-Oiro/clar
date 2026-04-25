# API Overview

CLAR exposes a REST API used by the web frontend. All endpoints are served over HTTPS.

## Base URL

```
https://clar-<hash>-uc.a.run.app
```

The exact URL is available in the [GCP Cloud Run console](https://console.cloud.google.com/run).

## Authentication

API endpoints do not require a separate API key. The web frontend authenticates users via Clerk session tokens. Direct API access is not currently supported for external callers.

## Content types

| Direction | Content-Type |
|---|---|
| Request body (file upload) | `multipart/form-data` |
| Request body (chat) | `application/json` |
| Response (report analysis) | `application/json` |
| Response (chat) | `text/event-stream` (Server-Sent Events) |

## Rate limiting

No explicit rate limit is enforced at the API layer. Cloud Run scales automatically under load up to the configured maximum instance count.

## Errors

All error responses use standard HTTP status codes with a JSON body:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|---|---|
| 400 | Bad request (e.g. unsupported file type) |
| 422 | Validation error |
| 500 | Internal server error |
| 503 | LLM provider temporarily unavailable |
