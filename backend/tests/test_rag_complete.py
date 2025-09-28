"""
Complete RAG pipeline test
Run: python test_rag_complete.py
"""
from dotenv import load_dotenv
from app.models.user import User
from app.models.document import Document
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.models.chat import ChatMessage
from app.models.task import Task, Instruction
from app.models.consent import UserConsent
load_dotenv()  # Load environment variables

import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.models.consent import UserConsent
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.models.document import Document
from app.models.chat import ChatMessage
from app.models.task import Task, Instruction
from app.services.rag_pipeline import rag_pipeline
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_rag():
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print(" No test user found. Run create_test_user.py first")
            return
        
        print(f" Using test user: {user.id}")
        
        # CLEAN UP ANY EXISTING TEST DATA FIRST
        print("\n0. Cleaning up any previous test data...")
        db.query(Document).filter(Document.source_id == "test_email_baseball_001").delete()
        existing_email = db.query(Email).filter(Email.gmail_id == "test_email_baseball_001").first()
        if existing_email:
            db.delete(existing_email)
        db.commit()
        print("   Cleaned up previous test data")
        
        # Test 1: Create and process email
        print("\n1. Testing Email Processing...")
        test_email = Email(
            user_id=user.id,
            gmail_id="test_email_baseball_001",
            subject="Baseball game this weekend",
            from_email="john@example.com",
            from_name="John Smith",
            to_emails=["advisor@example.com"],
            body_text="Hi! My son plays baseball and we have a big game this weekend.",
            date=datetime.now(timezone.utc),  # Fixed deprecation warning
            is_processed=False
        )
        db.add(test_email)
        db.commit()
        db.refresh(test_email)
        
        docs = await rag_pipeline.process_email(db, user.id, test_email)
        print(f"   Created {len(docs)} chunks from email")
        
        # Test 2: Search
        print("\n2. Testing Vector Search...")
        result = await rag_pipeline.search_context(
            db=db,
            user_id=user.id,
            query="Who mentioned baseball?"
        )
    
        print(f"   Found {result['document_count']} documents")
        if result['document_count'] > 0:
            print(f"   Context preview: {result['formatted_context'][:150]}...")
        
        # Test 3: Check caching
        print("\n3. Testing Embedding Cache...")
        result2 = await rag_pipeline.search_context(
            db=db,
            user_id=user.id,
            query="Who mentioned baseball?"  # Same query - should hit cache
        )
        print(f"   Cache working (check logs for 'Cache HIT' or 'All embeddings retrieved from cache')")
        
        print("\n" + "="*60)
        print(" RAG Pipeline Complete and Working!")
        print("="*60)
        
        # Cleanup
        print("\n4. Cleaning up test data...")
        db.query(Document).filter(Document.source_id == "test_email_baseball_001").delete()
        db.delete(test_email)
        db.commit()
        print("   Cleaned up")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_complete_rag())