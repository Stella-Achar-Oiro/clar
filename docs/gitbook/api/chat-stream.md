# Streaming Chat

CLAR's chat endpoint streams responses token-by-token using Server-Sent Events (SSE).

## Request

```
POST /report/{report_id}/chat
Content-Type: application/json
```

### Path parameters

| Parameter | Description |
|---|---|
| `report_id` | The `report_id` returned by `POST /report` |

### Body

```json
{
  "message": "Is my cholesterol level something I should worry about?"
}
```

### Example (curl)

```bash
curl -N -X POST https://<base-url>/report/rpt_01j.../chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is my cholesterol level something I should worry about?"}'
```

## Response

```
200 OK
Content-Type: text/event-stream
```

The response is a stream of SSE events. Each event has the format:

```
data: {"token": "Your "}

data: {"token": "cholesterol "}

data: {"token": "level..."}

data: [DONE]
```

The stream ends with a `data: [DONE]` sentinel.

### Handling the stream

Consume the stream incrementally and append each `token` to build the full response. When `[DONE]` is received, the response is complete.

## Notes

- Chat responses are grounded in the content of the specific report identified by `report_id`.
- The response is generated in markdown. Render it appropriately if displaying in a UI.
- If the user asks a question outside the scope of the report, CLAR will indicate it cannot answer from the available document.
