# TestForge API Documentation

## Agent API (Port 8000)

### Submit Test Case

**Endpoint:** `POST /api/v1/submit`

**Request Body:**
```json
{
  "name": "string (required)",
  "scope": "string (required)",
  "specs": ["string"],
  "steps": ["string"] (required),
  "priority": "P0 | P1 | P2",
  "metadata": {}
}
```

**Response:**
```json
{
  "job_id": "uuid-v4",
  "status": "queued"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Login test",
    "scope": "Auth",
    "steps": ["Go to /login", "Enter email", "Click submit"]
  }'
```

### Get Job Status

**Endpoint:** `GET /api/v1/status/{job_id}`

**Response:**
```json
{
  "job_id": "uuid-v4",
  "status": "pending | processing | completed | failed",
  "created_at": "2026-03-08T15:00:00Z",
  "completed_at": "2026-03-08T15:02:00Z",
  "error_message": "string | null",
  "test_case": {
    "name": "string",
    "scope": "string"
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## Bot API (Port 5000)

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "bot"
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (job doesn't exist)
- `500` - Internal Server Error
