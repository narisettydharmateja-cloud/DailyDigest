# DailyDigest Frontend & API Setup

This guide explains how to run the React frontend and FastAPI backend for DailyDigest.

## Prerequisites

- Python 3.11+ with `uv` package manager
- Node.js 18+
- PostgreSQL database running
- `.env` file configured (see main README.md)

## Backend API Server

The FastAPI backend handles subscription management.

### Installation

The API uses FastAPI and requires additional dependencies:

```bash
# Install FastAPI and uvicorn
uv pip install fastapi uvicorn python-multipart email-validator
```

### Running the API

```bash
# From the project root directory
python api_server.py
```

The API will start on http://localhost:8000

### API Endpoints

- `GET /` - Health check
- `POST /api/subscribe` - Create or update a subscription
  - Body: `{ "email": "user@example.com", "categories": ["genai", "product"], "frequency": "daily" }`
- `GET /api/subscriptions` - List all active subscriptions
- `DELETE /api/subscribe/{email}` - Unsubscribe an email

### Database

The API automatically creates a `subscriptions` table in your PostgreSQL database with:
- `id` - Primary key
- `email` - Unique email address
- `categories` - Array of selected categories
- `frequency` - Delivery frequency (daily/weekly/biweekly)
- `created_at` - Subscription creation timestamp
- `updated_at` - Last update timestamp
- `is_active` - Active status

## Frontend React App

### Installation

```bash
cd frontend
npm install
```

### Running the Frontend

```bash
npm run dev
```

The app will open at http://localhost:3000

### Building for Production

```bash
npm run build
npm run preview
```

## Running Both Together

### Option 1: Two Terminals

Terminal 1 (Backend):
```bash
python api_server.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

### Option 2: Using a Process Manager

Install concurrently:
```bash
npm install -g concurrently
```

Create a start script in the root `package.json`:
```json
{
  "scripts": {
    "start": "concurrently \"python api_server.py\" \"cd frontend && npm run dev\""
  }
}
```

Then run:
```bash
npm start
```

## Environment Configuration

Make sure your `.env` file includes:

```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dailydigest

# SMTP (for sending emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## Integrating with Existing Digest System

To send digests to subscribed users, modify your existing digest CLI to:

1. Query the `subscriptions` table for active users
2. Filter by their selected categories
3. Send digests via email using the configured SMTP settings

Example integration in your digest command:

```python
from api_server import Subscription, SessionLocal

def send_to_subscribers(persona: str, digest_content: str):
    """Send digest to all subscribers interested in this persona."""
    db = SessionLocal()
    try:
        subscriptions = db.query(Subscription).filter(
            Subscription.is_active == "true"
        ).all()
        
        for sub in subscriptions:
            if persona in sub.categories:
                # Send email using your email service
                send_email(sub.email, digest_content)
    finally:
        db.close()
```

## Troubleshooting

### CORS Errors
If you see CORS errors, ensure the backend is running on port 8000 and the frontend on port 3000.

### Database Connection
Verify your `DATABASE_URL` in `.env` matches your PostgreSQL setup.

### Port Already in Use
If port 8000 or 3000 is taken, you can change them:
- Backend: Modify the port in `api_server.py`
- Frontend: Modify the port in `vite.config.js`

## Next Steps

1. Start both servers
2. Open http://localhost:3000 in your browser
3. Test the subscription form
4. Check the database for the new subscription entry
5. Integrate with your digest generation system
