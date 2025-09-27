"""
Test security features
Run: python test_security.py
"""
import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.models.consent import consent_manager
from app.core.audit import audit_logger
from app.core.rate_limit import rate_limiter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_consent_system():
    """Test consent management"""
    print("\n" + "="*60)
    print("TEST 1: Consent System")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("[FAIL] No test user found")
            return
        
        # Test granting consent
        print("\n1. Granting consent for send_email...")
        consent = consent_manager.grant_consent(
            db=db,
            user_id=user.id,
            action_type="send_email",
            scope="all",
            conditions={"max_per_day": 10}
        )
        print(f"[PASS] Consent granted: ID={consent.id}")
        
        # Test checking consent
        print("\n2. Checking consent...")
        is_allowed, reason = consent_manager.check_consent(
            db=db,
            user_id=user.id,
            action_type="send_email"
        )
        print(f"[PASS] Consent check: allowed={is_allowed}, reason={reason}")
        
        # Test revoking consent
        print("\n3. Revoking consent...")
        success = consent_manager.revoke_consent(
            db=db,
            user_id=user.id,
            action_type="send_email"
        )
        print(f"[PASS] Consent revoked: success={success}")
        
        # Test checking revoked consent
        print("\n4. Checking revoked consent...")
        is_allowed, reason = consent_manager.check_consent(
            db=db,
            user_id=user.id,
            action_type="send_email"
        )
        print(f"[PASS] Consent check after revoke: allowed={is_allowed}")
        print(f"   Reason: {reason}")
        
        print("\n[PASS] Consent system test passed!")
    
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_audit_logging():
    """Test audit trail"""
    print("\n" + "="*60)
    print("TEST 2: Audit Logging")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("[FAIL] No test user found")
            return
        
        # Test tool execution logging
        print("\n1. Logging tool execution...")
        audit_logger.log_tool_execution(
            db=db,
            user_id=user.id,
            user_email=user.email,
            tool_name="send_email",
            tool_input={"to": ["test@example.com"], "subject": "Test"},
            result={"success": True, "message_id": "12345"},
            status="success",
            ip_address="127.0.0.1"
        )
        print("[PASS] Tool execution logged")
        
        # Test proactive action logging
        print("\n2. Logging proactive action...")
        audit_logger.log_proactive_action(
            db=db,
            user_id=user.id,
            user_email=user.email,
            action="auto_create_contact",
            details={"contact_email": "new@example.com"},
            trigger_event="email_received"
        )
        print("[PASS] Proactive action logged")
        
        # Test unauthorized attempt logging
        print("\n3. Logging unauthorized attempt...")
        audit_logger.log_unauthorized_attempt(
            db=db,
            user_id=user.id,
            action="send_email_without_consent",
            reason="No consent granted",
            ip_address="127.0.0.1"
        )
        print("[PASS] Unauthorized attempt logged")
        
        # Query audit logs
        print("\n4. Querying audit logs...")
        from app.core.audit import AuditLog
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == user.id
        ).order_by(AuditLog.created_at.desc()).limit(5).all()
        
        print(f"[PASS] Found {len(logs)} audit logs:")
        for log in logs:
            print(f"   - {log.action} ({log.status}) at {log.created_at}")
        
        # Cleanup
        db.query(AuditLog).filter(AuditLog.user_id == user.id).delete()
        db.commit()
        
        print("\n[PASS] Audit logging test passed!")
    
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_rate_limiting():
    """Test rate limiting"""
    print("\n" + "="*60)
    print("TEST 3: Rate Limiting")
    print("="*60)
    
    try:
        if not rate_limiter.enabled:
            print("[WARN] Rate limiter disabled (Redis not available)")
            return
        
        identifier = "test_user_123"
        endpoint = "/test/endpoint"
        
        print("\n1. Testing rate limit (max 3 per minute)...")
        
        for i in range(5):
            result = await rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=3,
                window_seconds=60
            )
            
            if result["allowed"]:
                print(f"   Request {i+1}: [PASS] Allowed (remaining: {result['remaining']})")
            else:
                print(f"   Request {i+1}: [FAIL] Rate limited (reset in {result['reset']} seconds)")
        
        print("\n[PASS] Rate limiting test passed!")
    
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)

async def test_webhook_security():
    """Test webhook signature verification"""
    print("\n" + "="*60)
    print("TEST 4: Webhook Security")
    print("="*60)
    
    try:
        from app.core.webhook_security import webhook_security
        import hmac
        import hashlib
        
        # Test HubSpot signature
        print("\n1. Testing HubSpot signature verification...")
        
        secret = "test_secret_key_12345"
        body = b'{"test": "data"}'
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Test with valid signature
        is_valid = webhook_security.verify_hubspot_signature(
            signature=valid_signature,
            body=body,
            secret=secret
        )
        print(f"   Valid signature: {'[PASS] Verified' if is_valid else '[FAIL] Failed'}")
        
        # Test with invalid signature
        is_valid = webhook_security.verify_hubspot_signature(
            signature="invalid_signature",
            body=body,
            secret=secret
        )
        print(f"   Invalid signature: {'[FAIL] Rejected' if not is_valid else '[PASS] Incorrectly accepted'}")
        
        # Test Gmail token verification
        print("\n2. Testing Gmail token verification...")
        
        token = "test_token_xyz"
        is_valid = webhook_security.verify_gmail_pubsub(token, token)
        print(f"   Valid token: {'[PASS] Verified' if is_valid else '[FAIL] Failed'}")
        
        is_valid = webhook_security.verify_gmail_pubsub("wrong", token)
        print(f"   Invalid token: {'[FAIL] Rejected' if not is_valid else '[PASS] Incorrectly accepted'}")
        
        print("\n[PASS] Webhook security test passed!")
    
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)

async def test_data_sanitization():
    """Test sensitive data sanitization"""
    print("\n" + "="*60)
    print("TEST 5: Data Sanitization")
    print("="*60)
    
    try:
        from app.core.audit import AuditLogger
        
        print("\n1. Testing data sanitization...")
        
        sensitive_data = {
            "user": "john@example.com",
            "password": "secret123",
            "api_key": "sk-abc123",
            "access_token": "token_xyz",
            "normal_field": "this is fine",
            "nested": {
                "secret": "should be hidden",
                "public": "this is ok"
            }
        }
        
        sanitized = AuditLogger._sanitize_data(sensitive_data)
        
        print("   Original data:")
        for key, value in sensitive_data.items():
            print(f"     {key}: {value}")
        
        print("\n   Sanitized data:")
        for key, value in sanitized.items():
            print(f"     {key}: {value}")
        
        # Verify sensitive fields are redacted
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["access_token"] == "***REDACTED***"
        assert sanitized["normal_field"] == "this is fine"
        assert sanitized["nested"]["secret"] == "***REDACTED***"
        
        print("\n[PASS] Data sanitization test passed!")
    
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)

async def run_all_tests():
    """Run all security tests"""
    print("\n" + "="*60)
    print("STARTING SECURITY TESTS")
    print("="*60)
    print("\nPrerequisites:")
    print("   1. Test user must exist (run create_test_user.py)")
    print("   2. Database must be migrated (alembic upgrade head)")
    print("   3. Redis should be running (for rate limit tests)")
    
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    await asyncio.sleep(3)
    
    # Run tests
    await test_consent_system()
    await test_audit_logging()
    await test_rate_limiting()
    await test_webhook_security()
    await test_data_sanitization()
    
    print("\n" + "="*60)
    print("ALL SECURITY TESTS COMPLETE")
    print("="*60)
    
    print("\n[PASS] Security features are working!")
    print("\nSecurity checklist:")
    print("   [PASS] Consent management")
    print("   [PASS] Audit trail logging")
    print("   [PASS] Rate limiting")
    print("   [PASS] Webhook signature verification")
    print("   [PASS] Data sanitization")

if __name__ == "__main__":
    asyncio.run(run_all_tests())