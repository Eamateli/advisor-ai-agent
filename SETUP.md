# Financial Advisor AI Agent - Setup Guide

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose
- Git

### 2. Environment Setup
Create a `.env` file in the root directory with the following variables:

```bash
# Copy the example and fill in your values
cp .env.example .env
```

Required environment variables:
- `SECRET_KEY` - Generate with: `openssl rand -base64 32`
- `ENCRYPTION_KEY` - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `HUBSPOT_CLIENT_ID` and `HUBSPOT_CLIENT_SECRET` - From HubSpot Developer Portal
- `OPENAI_API_KEY` - From OpenAI Platform
- `ANTHROPIC_API_KEY` - From Anthropic Console

### 3. Start the Application

**Option A: Using the build script (recommended)**
```bash
# Linux/Mac
./build.sh

# Windows
build.bat
```

**Option B: Test build (if you encounter issues)**
```bash
# Linux/Mac
./test-build.sh

# Windows
test-build.bat
```

**Option C: Manual Docker commands**
```bash
docker-compose up --build
```

**Note**: The frontend dependencies have been optimized to resolve version conflicts. If you still encounter issues, use the test build scripts which include additional troubleshooting steps.

### 4. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555

## Services

The application includes:
- **Backend**: FastAPI with PostgreSQL and Redis
- **Frontend**: React with TypeScript
- **Celery Worker**: Background task processing
- **Celery Beat**: Periodic task scheduling
- **Flower**: Celery monitoring dashboard

## Features

- ✅ Google OAuth authentication
- ✅ HubSpot CRM integration
- ✅ Gmail integration
- ✅ Google Calendar integration
- ✅ RAG-powered knowledge base
- ✅ Real-time chat with WebSocket streaming
- ✅ Proactive agent capabilities
- ✅ Background task processing
- ✅ User consent management

## Production Deployment

For production deployment on Render:
1. Update `render.yaml` with your domain URLs
2. Set all environment variables in Render dashboard
3. Deploy both backend and frontend services
4. The Celery workers will be automatically deployed

## Troubleshooting

### Common Issues:
1. **Database connection errors**: Ensure PostgreSQL is running
2. **Redis connection errors**: Ensure Redis is running
3. **OAuth errors**: Check your OAuth app configuration
4. **API key errors**: Verify all API keys are set correctly

### Logs:
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery-worker
```
