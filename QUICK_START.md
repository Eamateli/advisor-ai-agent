# 🚀 Quick Start Guide - Financial Advisor AI Agent

## ⚠️ **Current Issue: Backend Not Running**

The "Failed to fetch" error you're seeing means the backend API is not running. Let's fix this!

---

## 📋 **Prerequisites**

Before starting, make sure you have:
- ✅ Docker Desktop installed and running
- ✅ Node.js 18+ installed
- ✅ `.env` file in the project root

---

## 🔧 **Step-by-Step Setup**

### **Step 1: Ensure Docker is Running**

**Windows/Mac**: Open Docker Desktop and make sure it's running (green icon in system tray).

**Linux/WSL**:
```bash
sudo systemctl start docker
```

### **Step 2: Start the Backend Services**

Open a terminal in the project root and run:

```bash
docker-compose up --build backend postgres redis celery-worker celery-beat
```

**What this does**:
- ✅ Starts PostgreSQL database (with pgvector for RAG)
- ✅ Starts Redis (for caching and task queue)
- ✅ Starts FastAPI backend (your API server)
- ✅ Starts Celery workers (for background tasks)
- ✅ Starts Celery beat (for scheduled tasks)

**Wait for this message**:
```
backend-1  | INFO:     Application startup complete.
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **Step 3: Start the Frontend** (In a NEW Terminal)

```bash
cd frontend
npm start
```

**Wait for**:
```
Compiled successfully!
Local: http://localhost:3000
```

### **Step 4: Access the Application**

1. Open your browser to **http://localhost:3000**
2. You should see the beautiful login page (not "Failed to fetch")
3. Click "Continue with Google" to authenticate

---

## 🎨 **Expected UI After Login**

After you log in, you should see:

### **Beautiful Chat Interface** matching the requirements:
- ✅ Clean, modern design
- ✅ Context header showing "Context set to all meetings"
- ✅ Chat input at the bottom
- ✅ Quick action buttons (before first message)
- ✅ Meeting cards when displaying results
- ✅ Streaming AI responses

### **Example Interactions**:
```
You: "Find meetings I've had with Bill and Tim this month"

Agent: Sure, here are some recent meetings...
┌─────────────────────────────────────┐
│ 8 Thursday                          │
│ 12 – 1:30pm                         │
│ Quarterly All Team Meeting          │
│ 👥 Bill, Tim, others                │
└─────────────────────────────────────┘
```

---

## 🐛 **Troubleshooting**

### **"Failed to fetch" Error**

**Cause**: Backend is not running

**Fix**:
```bash
# Check if backend is running
docker-compose ps

# If backend is not in the list, start it
docker-compose up --build backend postgres redis
```

### **Port Already in Use**

**Cause**: Another service is using port 3000 or 8000

**Fix**:
```bash
# Find what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill the process or use different ports
```

### **Docker Build Failures**

**Cause**: Missing dependencies or Docker issues

**Fix**:
```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up
```

### **Frontend Won't Start**

**Cause**: Node modules issue

**Fix**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm start
```

---

## 🔍 **Verify Everything is Working**

### **1. Check Backend Health**
```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### **2. Check API Docs**
Open: http://localhost:8000/docs

You should see the FastAPI interactive documentation.

### **3. Check Frontend**
Open: http://localhost:3000

You should see:
- ✅ Login page (if not authenticated)
- ✅ Chat interface (if authenticated)
- ✅ NO "Failed to fetch" errors

---

## 📊 **Service Status**

Run this to check all services:

```bash
docker-compose ps
```

**Expected output**:
```
NAME                          STATUS
advisor-ai-agent-backend-1    Up (healthy)
advisor-ai-agent-postgres-1   Up (healthy)
advisor-ai-agent-redis-1      Up (healthy)
advisor-ai-agent-celery-worker-1  Up
advisor-ai-agent-celery-beat-1    Up
```

---

## 🎯 **What Each Service Does**

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | React UI - Chat interface |
| **Backend** | 8000 | FastAPI API - Handles requests |
| **PostgreSQL** | 5432 | Database with pgvector for RAG |
| **Redis** | 6379 | Cache + Task queue |
| **Celery Worker** | - | Processes background tasks |
| **Celery Beat** | - | Schedules periodic tasks |

---

## 🔐 **OAuth Setup** (For Full Functionality)

To use Google OAuth and HubSpot integration, you need real API credentials:

### **1. Google OAuth**
1. Go to https://console.developers.google.com/
2. Create a new project
3. Enable Gmail API and Google Calendar API
4. Create OAuth 2.0 credentials
5. Add to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-actual-client-id
   GOOGLE_CLIENT_SECRET=your-actual-secret
   ```

### **2. HubSpot OAuth**
1. Go to https://developers.hubspot.com/
2. Create a developer account (free)
3. Create an app
4. Add to `.env`:
   ```
   HUBSPOT_CLIENT_ID=your-actual-client-id
   HUBSPOT_CLIENT_SECRET=your-actual-secret
   ```

### **3. AI API Keys**

**OpenAI** (for embeddings):
```
OPENAI_API_KEY=sk-proj-your-key-here
```

**Anthropic** (for Claude):
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## 🚀 **Running in Production**

For deployment to Render:

1. Push code to GitHub
2. Connect Render to your repo
3. Use `render.yaml` configuration
4. Set all environment variables in Render dashboard
5. Deploy!

---

## 📝 **Common Commands**

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart specific service
docker-compose restart backend

# Check status
docker-compose ps

# Clean everything
docker-compose down -v
docker system prune -af
```

---

## ✨ **Features You Should See**

Once everything is running:

### **✅ Authentication**
- Google OAuth login
- Secure JWT tokens
- Automatic token validation

### **✅ Chat Interface**
- Beautiful, responsive design
- Real-time streaming responses
- Context-aware conversations

### **✅ RAG System**
- Searches through emails
- Queries HubSpot contacts
- Vector similarity search

### **✅ AI Agent**
- Can schedule meetings
- Send emails
- Create HubSpot contacts
- Answer questions about clients

### **✅ Background Tasks**
- Syncs emails every 15 minutes
- Syncs HubSpot every hour
- Processes webhooks
- Handles long-running tasks

---

## 🆘 **Still Not Working?**

If you're still seeing issues:

1. **Check Docker logs**:
   ```bash
   docker-compose logs backend | tail -50
   ```

2. **Verify .env file**:
   ```bash
   cat .env | head -20
   ```

3. **Test database connection**:
   ```bash
   docker-compose exec postgres psql -U postgres -c "SELECT version();"
   ```

4. **Restart everything**:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

---

## 🎉 **Success Checklist**

- [ ] Docker Desktop is running
- [ ] Backend shows "Application startup complete"
- [ ] Frontend shows "Compiled successfully"
- [ ] http://localhost:3000 loads without "Failed to fetch"
- [ ] http://localhost:8000/health returns healthy status
- [ ] Can see login page
- [ ] Can click "Continue with Google"
- [ ] Chat interface loads after login

---

## 📞 **Need Help?**

If you're stuck, check:
1. Backend logs: `docker-compose logs backend`
2. Frontend console: Browser DevTools → Console tab
3. Network tab: Browser DevTools → Network tab
4. Health endpoint: http://localhost:8000/health

The most common issue is **backend not running** - make sure you see:
```
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Good luck!** 🚀
