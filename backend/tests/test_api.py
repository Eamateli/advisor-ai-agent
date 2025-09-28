# backend/tests/test_api.py
"""
API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture
def test_token():
    """Create test JWT token"""
    return create_access_token({"sub": 1})

@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {test_token}"}

def test_root_endpoint():
    """Test root health check"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_endpoint():
    """Test detailed health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert data["status"] in ["healthy", "degraded"]

def test_chat_stream_requires_auth():
    """Test chat endpoint requires authentication"""
    response = client.post("/api/v1/chat/stream", json={"message": "Hello"})
    assert response.status_code == 403  # No auth header

def test_chat_stream_with_auth(auth_headers):
    """Test authenticated chat stream"""
    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "Hello, what can you help me with?"},
        headers=auth_headers
    )
    # Should return SSE stream
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

def test_rate_limiting(auth_headers):
    """Test rate limiting works"""
    # Send 11 requests (limit is 10 per minute)
    for i in range(11):
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": f"Test {i}"},
            headers=auth_headers
        )
        
        if i < 10:
            assert response.status_code == 200
        else:
            # 11th request should be rate limited
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["error"]

def test_websocket_connection():
    """Test WebSocket connection"""
    token = create_access_token({"sub": 1})
    
    with client.websocket_connect(f"/api/v1/chat/ws/{token}") as websocket:
        # Should receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "connected"
        
        # Test ping/pong
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"

def test_profile_endpoints(auth_headers):
    """Test profile endpoints"""
    # Get profile
    response = client.get("/api/v1/profile/", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()
    
    # Update profile
    response = client.patch(
        "/api/v1/profile/",
        json={"full_name": "Test User Updated"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test User Updated"

def test_sync_endpoints(auth_headers):
    """Test sync endpoints"""
    # Get sync status
    response = client.get("/api/v1/sync/status", headers=auth_headers)
    assert response.status_code == 200
    assert "gmail" in response.json()
    assert "hubspot" in response.json()
    
    # Trigger full sync (will fail without OAuth but should accept request)
    response = client.post(
        "/api/v1/sync/full",
        json={"days_back": 7, "include_gmail": True, "include_hubspot": False},
        headers=auth_headers
    )
    # Should return 400 because no OAuth configured in test
    assert response.status_code in [200, 400]

def test_rag_search(auth_headers):
    """Test RAG search endpoint"""
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "test search", "limit": 5},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "documents" in response.json()
    assert "document_count" in response.json()

def test_consent_management(auth_headers):
    """Test consent endpoints"""
    # Grant consent
    response = client.post(
        "/api/v1/chat/consent/grant",
        json={
            "action_type": "send_email",
            "scope": "all"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "consent_id" in response.json()
    
    # Get consents
    response = client.get("/api/v1/chat/consent", headers=auth_headers)
    assert response.status_code == 200
    assert "consents" in response.json()
    
    # Revoke consent
    response = client.post(
        "/api/v1/chat/consent/revoke/send_email",
        headers=auth_headers
    )
    assert response.status_code == 200

def test_audit_logs(auth_headers):
    """Test audit log endpoint"""
    response = client.get("/api/v1/chat/audit?limit=10", headers=auth_headers)
    assert response.status_code == 200
    assert "audit_logs" in response.json()

# ============================================================================
# Run tests with: pytest backend/tests/test_api.py -v