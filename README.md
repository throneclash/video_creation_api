# Video Creation API

A FastAPI-based REST API for creating and publishing Instagram videos with customizable templates. The API accepts video creation requests and processes them asynchronously in the background, returning an immediate response to the client.

## Features

- **Three Customizable Templates**: Drama Intenso (A), FOMO (B), and Aspiracional (C)
- **Asynchronous Processing**: Videos are processed in the background without blocking the client
- **Immediate Response**: API returns a job ID immediately after accepting a request
- **Instagram Integration**: Automatic publishing to Instagram after video creation
- **Secure Configuration**: All credentials stored in environment variables
- **Job Status Tracking**: Monitor the status of video processing jobs
- **Comprehensive Documentation**: Interactive API docs with Swagger UI

## Project Structure

```
video_creation_api/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration and environment variables
│   ├── models.py                # Pydantic models for request/response validation
│   └── job_queue.py             # Job queue for background task management
├── utils/
│   ├── __init__.py              # Package initialization
│   └── video_processor.py       # Video processing and Instagram publishing logic
├── templates/                   # Template definitions (for future expansion)
├── output/                      # Directory for processed videos
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**

```bash
cd video_creation_api
```

2. **Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy `.env.example` to `.env` and fill in your Instagram credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id_here
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
VIDEO_OUTPUT_DIR=./output
MAX_WORKERS=4
```

## Running the API

### Development Mode

```bash
python main.py
```

The API will start on `http://localhost:8000`

### Production Mode with Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the API is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

**Endpoint**: `GET /health`

Check if the API is running and healthy.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Create Video - Generic Endpoint

**Endpoint**: `POST /api/v1/videos/create`

Create a video with any template type.

**Request Body**:
```json
{
  "template": "A",
  "params": {
    "king_name": "Luiz Girão",
    "king_photo_url": "https://example.com/avatar.jpg",
    "amount": 250.00,
    "message": "Do zero ao topo! 🚀",
    "hook": "ALGUÉM ACABOU DE PAGAR",
    "badge_text": "⚠️ ALERTA DE CONQUISTA",
    "primary_color": "#00ff88",
    "accent_color": "#00d4ff",
    "badge_color": "#ff0044"
  }
}
```

**Response** (HTTP 202 Accepted):
```json
{
  "status": "ok",
  "message": "Video creation job accepted. Processing in background.",
  "video_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Create Video - Template A (Drama Intenso)

**Endpoint**: `POST /api/v1/videos/template-a`

Create a video using Template A with dramatic intensity.

**Request Body**:
```json
{
  "king_name": "Luiz Girão",
  "king_photo_url": "https://example.com/avatar.jpg",
  "amount": 250.00,
  "message": "Do zero ao topo! 🚀",
  "hook": "ALGUÉM ACABOU DE PAGAR",
  "badge_text": "⚠️ ALERTA DE CONQUISTA",
  "logo": "THRONECLASH",
  "primary_color": "#00ff88",
  "accent_color": "#00d4ff",
  "badge_color": "#ff0044"
}
```

**Query Parameters**:
- `publish` (boolean, default: true): Whether to publish to Instagram

**Response** (HTTP 202 Accepted):
```json
{
  "status": "ok",
  "message": "Video creation job accepted. Processing in background.",
  "video_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Create Video - Template B (FOMO)

**Endpoint**: `POST /api/v1/videos/template-b`

Create a video using Template B with urgency and FOMO messaging.

**Request Body**:
```json
{
  "king_name": "Luiz Girão",
  "king_photo_url": "https://example.com/avatar.jpg",
  "amount": 250.00,
  "message": "Não perca esta oportunidade!",
  "hook": "ÚLTIMA CHANCE ANTES QUE ACABE",
  "cta": "NÃO FIQUE DE FORA!",
  "primary_color": "#ffd700",
  "accent_color": "#ff6b35"
}
```

**Response** (HTTP 202 Accepted):
```json
{
  "status": "ok",
  "message": "Video creation job accepted. Processing in background.",
  "video_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Create Video - Template C (Aspiracional)

**Endpoint**: `POST /api/v1/videos/template-c`

Create a video using Template C with aspirational messaging.

**Request Body**:
```json
{
  "king_name": "Luiz Girão",
  "king_photo_url": "https://example.com/avatar.jpg",
  "amount": 250.00,
  "message": "Seu sucesso começa aqui!",
  "hook": "SEU NOME PODE ESTAR AQUI",
  "subtitle": "Junte-se aos vencedores",
  "primary_color": "#bc13fe",
  "accent_color": "#00d4ff",
  "gold_color": "#ffd700"
}
```

**Response** (HTTP 202 Accepted):
```json
{
  "status": "ok",
  "message": "Video creation job accepted. Processing in background.",
  "video_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Get Video Status

**Endpoint**: `GET /api/v1/videos/{video_id}`

Get the current status of a video processing job.

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "template": "A",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00.000000",
  "started_at": "2024-01-15T10:30:01.000000",
  "completed_at": null,
  "error": null,
  "result": null
}
```

**Status Values**:
- `pending`: Job is waiting to be processed
- `processing`: Video is being created
- `completed`: Video creation completed successfully
- `failed`: Video creation failed
- `published`: Video published to Instagram

### List All Videos

**Endpoint**: `GET /api/v1/videos`

List all video processing jobs with optional filtering.

**Query Parameters**:
- `status_filter` (string, optional): Filter by status (pending, processing, completed, failed, published)
- `limit` (integer, default: 100): Maximum number of results to return

**Response**:
```json
{
  "total": 42,
  "returned": 10,
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "template": "A",
      "status": "published",
      "created_at": "2024-01-15T10:30:00.000000",
      "started_at": "2024-01-15T10:30:01.000000",
      "completed_at": "2024-01-15T10:35:00.000000",
      "error": null,
      "result": {...}
    }
  ]
}
```

## Template Parameters Reference

### Template A - Drama Intenso 🔥

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| king_name | string | Yes | - | Name of the featured person |
| king_photo_url | URL | Yes | - | Photo URL of the featured person |
| amount | number | Yes | - | Amount/value to display |
| message | string | Yes | - | Main message |
| hook | string | No | "ALGUÉM ACABOU DE PAGAR" | Hook text |
| badge_text | string | No | "⚠️ ALERTA DE CONQUISTA" | Badge text |
| logo | string | No | "THRONECLASH" | Logo text |
| primary_color | string | No | "#00ff88" | Primary neon green color |
| accent_color | string | No | "#00d4ff" | Accent cyan color |
| badge_color | string | No | "#ff0044" | Badge red color |

### Template B - FOMO ⏳

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| king_name | string | Yes | - | Name of the featured person |
| king_photo_url | URL | Yes | - | Photo URL of the featured person |
| amount | number | Yes | - | Amount/value to display |
| message | string | No | - | Main message |
| hook | string | No | "ÚLTIMA CHANCE ANTES QUE ACABE" | Hook text |
| cta | string | No | "NÃO FIQUE DE FORA!" | Call-to-action text |
| primary_color | string | No | "#ffd700" | Primary gold color |
| accent_color | string | No | "#ff6b35" | Accent urgent orange color |

### Template C - Aspiracional ✨

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| king_name | string | Yes | - | Name of the featured person |
| king_photo_url | URL | Yes | - | Photo URL of the featured person |
| amount | number | Yes | - | Amount/value to display |
| message | string | Yes | - | Main message |
| hook | string | No | "SEU NOME PODE ESTAR AQUI" | Hook text |
| subtitle | string | No | - | Subtitle text |
| primary_color | string | No | "#bc13fe" | Primary royal purple color |
| accent_color | string | No | "#00d4ff" | Accent aspirational blue color |
| gold_color | string | No | "#ffd700" | Gold prestige color |

## Usage Examples

### Using cURL

**Create a video with Template A**:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/template-a" \
  -H "Content-Type: application/json" \
  -d '{
    "king_name": "Luiz Girão",
    "king_photo_url": "https://example.com/avatar.jpg",
    "amount": 250.00,
    "message": "Do zero ao topo! 🚀"
  }'
```

**Check video status**:

```bash
curl "http://localhost:8000/api/v1/videos/550e8400-e29b-41d4-a716-446655440000"
```

**List all videos**:

```bash
curl "http://localhost:8000/api/v1/videos"
```

**Filter by status**:

```bash
curl "http://localhost:8000/api/v1/videos?status_filter=published"
```

### Using Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Create a video
response = requests.post(
    f"{BASE_URL}/api/v1/videos/template-a",
    json={
        "king_name": "Luiz Girão",
        "king_photo_url": "https://example.com/avatar.jpg",
        "amount": 250.00,
        "message": "Do zero ao topo! 🚀"
    }
)

video_id = response.json()["video_id"]
print(f"Video job created: {video_id}")

# Check status
status_response = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}")
print(json.dumps(status_response.json(), indent=2))
```

### Using JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:8000";

// Create a video
const createResponse = await fetch(`${BASE_URL}/api/v1/videos/template-a`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    king_name: "Luiz Girão",
    king_photo_url: "https://example.com/avatar.jpg",
    amount: 250.00,
    message: "Do zero ao topo! 🚀"
  })
});

const data = await createResponse.json();
const videoId = data.video_id;
console.log(`Video job created: ${videoId}`);

// Check status
const statusResponse = await fetch(`${BASE_URL}/api/v1/videos/${videoId}`);
const statusData = await statusResponse.json();
console.log(JSON.stringify(statusData, null, 2));
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| INSTAGRAM_ACCESS_TOKEN | Instagram API access token | `your_token_here` |
| INSTAGRAM_ACCOUNT_ID | Instagram account ID | `123456789` |
| API_HOST | API host address | `0.0.0.0` |
| API_PORT | API port number | `8000` |
| DEBUG | Enable debug mode | `False` |
| VIDEO_OUTPUT_DIR | Directory for output videos | `./output` |
| MAX_WORKERS | Maximum worker threads | `4` |

## Obtaining Instagram Credentials

To get your Instagram credentials:

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app or use an existing one
3. Add Instagram Graph API product
4. Generate an access token with appropriate permissions
5. Get your Instagram Account ID
6. Add these values to your `.env` file

## Error Handling

The API returns appropriate HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 202 | Accepted (video creation job queued) |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found (video job not found) |
| 500 | Internal Server Error |

**Error Response Example**:

```json
{
  "detail": "Invalid template: X. Must be A, B, or C"
}
```

## Performance Considerations

- The API uses FastAPI's `BackgroundTasks` for asynchronous processing
- Videos are processed sequentially in the background
- For high-volume scenarios, consider using a task queue like Celery with Redis
- The API maintains an in-memory job queue; jobs are lost on server restart
- For production, implement persistent job storage (database)

## Logging

The API logs all operations to the console. Log levels include:

- `INFO`: General information about API operations
- `WARNING`: Warning messages (e.g., missing environment variables)
- `ERROR`: Error messages with full traceback

Logs include timestamps, logger names, and detailed messages for debugging.

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Access Tokens**: Keep Instagram access tokens secure and rotate them regularly
3. **HTTPS**: Use HTTPS in production environments
4. **Authentication**: Consider adding API key authentication for production
5. **Rate Limiting**: Implement rate limiting to prevent abuse
6. **Input Validation**: All inputs are validated using Pydantic models

## Troubleshooting

### API won't start

- Check if port 8000 is already in use: `lsof -i :8000`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.8+)

### Instagram publishing fails

- Verify `INSTAGRAM_ACCESS_TOKEN` is correct and not expired
- Verify `INSTAGRAM_ACCOUNT_ID` is correct
- Check Instagram API rate limits
- Review API logs for detailed error messages

### Video processing hangs

- Check system resources (CPU, memory)
- Verify output directory has write permissions
- Check logs for specific error messages

## Future Enhancements

- [ ] Persistent job storage with database
- [ ] Celery integration for distributed task processing
- [ ] Redis caching for improved performance
- [ ] Advanced video editing features
- [ ] Multiple output format support
- [ ] Webhook notifications for job completion
- [ ] API authentication and authorization
- [ ] Rate limiting and throttling
- [ ] Comprehensive video analytics
- [ ] Template customization UI

## License

This project is provided as-is for commercial use.

## Support

For issues, questions, or feature requests, please refer to the API documentation at `/docs` when the server is running.

---

**Version**: 1.0.0  
**Last Updated**: January 2024
