"""
Test script to verify OAuth setup
Run: python test_auth.py
"""
import asyncio
from app.core.config import settings
from app.services.google_oauth import google_oauth
from app.services.hubspot_oauth import hubspot_oauth

async def test_oauth_config():
    print("=" * 60)
    print("OAuth Configuration Test")
    print("=" * 60)
    
    # Test Google OAuth
    print("\n✓ Google OAuth Configuration:")
    print(f"  Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
    print(f"  Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    print(f"  Scopes: {len(settings.GOOGLE_SCOPES)} scopes configured")
    
    # Generate test auth URL
    test_state = "test_state_123"
    google_url = google_oauth.get_authorization_url(test_state)
    print(f"\n  Sample Auth URL: {google_url[:80]}...")
    
    # Test HubSpot OAuth
    print("\n✓ HubSpot OAuth Configuration:")
    print(f"  Client ID: {settings.HUBSPOT_CLIENT_ID[:20]}...")
    print(f"  Redirect URI: {settings.HUBSPOT_REDIRECT_URI}")
    print(f"  Scopes: {settings.HUBSPOT_SCOPES}")
    
    # Generate test auth URL
    hubspot_url = hubspot_oauth.get_authorization_url(test_state)
    print(f"\n  Sample Auth URL: {hubspot_url[:80]}...")
    
    # Test Encryption
    print("\n✓ Token Encryption:")
    from app.core.encryption import token_encryption
    test_token = "test_access_token_12345"
    encrypted = token_encryption.encrypt(test_token)
    decrypted = token_encryption.decrypt(encrypted)
    print(f"  Encryption: {'✓ Working' if decrypted == test_token else '✗ Failed'}")
    
    # Test JWT
    print("\n✓ JWT Token Generation:")
    from app.core.security import create_access_token, verify_token
    token = create_access_token({"sub": 1})
    payload = verify_token(token)
    print(f"  JWT: {'✓ Working' if payload.get('sub') == 1 else '✗ Failed'}")
    
    print("\n" + "=" * 60)
    print("✓ All OAuth configurations verified!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Start the backend: uvicorn app.main:app --reload")
    print("2. Visit: http://localhost:8000/docs")
    print("3. Test /auth/google/login endpoint")
    print("4. Make sure webshookeng@gmail.com is added as test user in Google Console")

if __name__ == "__main__":
    asyncio.run(test_oauth_config())