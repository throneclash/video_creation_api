# Quick Start Guide

Get the Video Creation API up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- Instagram API credentials (access token and account ID)

## Installation & Setup (5 minutes)

### 1. Extract the Project

```bash
unzip video_creation_api.zip
cd video_api
```

### 2. Set Up Environment Variables

Copy the example environment file and add your Instagram credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_ACCOUNT_ID=your_account_id_here
```

### 3. Run the API

**On Linux/macOS:**

```bash
chmod +x run.sh
./run.sh
```

**On Windows:**

```bash
run.bat
```

**Or manually:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Verify It's Working

Open your browser and visit:

- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Create Your First Video (30 seconds)

### Using cURL

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

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/videos/template-a",
    json={
        "king_name": "Luiz Girão",
        "king_photo_url": "https://example.com/avatar.jpg",
        "amount": 250.00,
        "message": "Do zero ao topo! 🚀"
    }
)

video_id = response.json()["video_id"]
print(f"Video created with ID: {video_id}")
```

### Using JavaScript

```javascript
const response = await fetch("http://localhost:8000/api/v1/videos/template-a", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    king_name: "Luiz Girão",
    king_photo_url: "https://example.com/avatar.jpg",
    amount: 250.00,
    message: "Do zero ao topo! 🚀"
  })
});

const data = await response.json();
console.log(`Video created with ID: ${data.video_id}`);
```

## Check Video Status

```bash
curl "http://localhost:8000/api/v1/videos/{video_id}"
```

Replace `{video_id}` with the ID returned from the creation request.

## Available Templates

### Template A - Drama Intenso 🔥

Intense, dramatic video with customizable colors and alerts.

```bash
curl -X POST "http://localhost:8000/api/v1/videos/template-a" \
  -H "Content-Type: application/json" \
  -d '{
    "king_name": "Your Name",
    "king_photo_url": "https://example.com/photo.jpg",
    "amount": 500.00,
    "message": "Your message here"
  }'
```

### Template B - FOMO ⏳

Urgency-focused template with time-sensitive messaging.

```bash
curl -X POST "http://localhost:8000/api/v1/videos/template-b" \
  -H "Content-Type: application/json" \
  -d '{
    "king_name": "Your Name",
    "king_photo_url": "https://example.com/photo.jpg",
    "amount": 500.00
  }'
```

### Template C - Aspiracional ✨

Aspirational template focused on prestige and achievement.

```bash
curl -X POST "http://localhost:8000/api/v1/videos/template-c" \
  -H "Content-Type: application/json" \
  -d '{
    "king_name": "Your Name",
    "king_photo_url": "https://example.com/photo.jpg",
    "amount": 500.00,
    "message": "Your aspirational message"
  }'
```

## Docker Deployment (Optional)

If you have Docker installed:

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000

## Common Issues

### Port 8000 Already in Use

Change the port in `.env`:

```
API_PORT=8001
```

Then run the API again.

### Instagram Publishing Not Working

Ensure your credentials are correct in `.env`:

```
INSTAGRAM_ACCESS_TOKEN=your_valid_token
INSTAGRAM_ACCOUNT_ID=your_valid_account_id
```

You can still create videos without valid credentials; they just won't be published to Instagram.

### Module Not Found Errors

Make sure you've activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the API docs at http://localhost:8000/docs
3. Customize templates and colors for your brand
4. Integrate with your application

## Support

For detailed API documentation, visit http://localhost:8000/docs when the server is running.

---

Happy video creating! 🎬
