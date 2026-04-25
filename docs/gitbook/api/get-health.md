# GET /health

Returns the health status of the CLAR backend service.

## Request

```
GET /health
```

No authentication or parameters required.

### Example (curl)

```bash
curl https://<base-url>/health
```

## Response

```
200 OK
Content-Type: application/json
```

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

A `200` response with `"status": "ok"` indicates the service is ready to accept requests.

This endpoint is used by Cloud Run's health check configuration and can be used by external monitoring to verify uptime.
