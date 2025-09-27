"""
Test RAG pipeline functionality
Run: python test_rag.py
"""
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.services.rag_pipeline import rag_pipeline
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_pipeline():
    db = SessionLocal()
    
    try:
        # Assume user_id = 1 (you need to have a user in the database first)
        user_id = 1
        
        print("=" * 60)
        print("RAG Pipeline Test")
        print("=" * 60)
        
        # Test 1: Create and process a test email
        print("\n1. Testing Email Processing...")
        test_email = Email(
            user_id=user_id,
            gmail_id="test_email_001",
            thread_id="thread_001",
            subject="Baseball game this weekend",
            from_email="john.smith@example.com",
            from_name="John Smith",
            to_emails=["advisor@example.com"],
            body_text="Hi! My son plays baseball and we have a big game this weekend. Would love to discuss my portfolio after the game. Can we meet Monday?",
            date=datetime.utcnow(),
            is_processed=False
        )
        db.add(test_email)
        db.commit()
        db.refresh(test_email)
        
        # Process the email
        docs = await rag_pipeline.process_email(db, user_id, test_email)
        print(f"  ✓ Created {len(docs)} document chunks from email")
        
        # Test 2: Create and process a test HubSpot contact
        print("\n2. Testing HubSpot Contact Processing...")
        test_contact = HubSpotContact(
            user_id=user_id,
            hubspot_id="test_contact_001",
            email="sarah.jones@example.com",
            first_name="Sarah",
            last_name="Jones",
            phone="+1-555-0123",
            company="Tech Corp",
            properties={"investment_interest": "Tech stocks", "risk_tolerance": "Moderate"},
            is_processed=False
        )
        db.add(test_contact)
        db.commit()
        db.refresh(test_contact)
        
        docs = await rag_pipeline.process_hubspot_contact(db, user_id, test_contact)
        print(f"  ✓ Created {len(docs)} document chunks from contact")
        
        # Test 3: Create and process a test note
        print("\n3. Testing HubSpot Note Processing...")
        test_note = HubSpotNote(
            user_id=user_id,
            contact_id=test_contact.id,
            hubspot_id="test_note_001",
            body="Client mentioned wanting to sell AAPL stock due to market concerns. Scheduled follow-up call.",
            created_by="Advisor",
            is_processed=False
        )
        db.add(test_note)
        db.commit()
        db.refresh(test_note)
        
        docs = await rag_pipeline.process_hubspot_note(db, user_id, test_note)
        print(f"  ✓ Created {len(docs)} document chunks from note")
        
        # Test 4: Vector search
        print("\n4. Testing Vector Search...")
        
        # Search for baseball-related content
        result = await rag_pipeline.search_context(
            db=db,
            user_id=user_id,
            query="Who mentioned their kid plays baseball?"
        )
        
        print(f"  ✓ Found {result['document_count']} relevant documents")
        print(f"\n  Search Results Preview:")
        print(f"  {result['formatted_context'][:200]}...")
        
        # Search for AAPL stock
        result = await rag_pipeline.search_context(
            db=db,
            user_id=user_id,
            query="Why did someone want to sell AAPL stock?"
        )
        
        print(f"\n  ✓ Found {result['document_count']} documents about AAPL")
        print(f"  Search Results Preview:")
        print(f"  {result['formatted_context'][:200]}...")
        
        # Test 5: Metadata filtering
        print("\n5. Testing Metadata Filtering...")
        result = await rag_pipeline.search_context(
            db=db,
            user_id=user_id,
            query="client information",
            doc_types=['hubspot_contact']
        )
        
        print(f"  ✓ Found {result['document_count']} HubSpot contacts")
        
        print("\n" + "=" * 60)
        print("✓ All RAG Pipeline Tests Passed!")
        print("=" * 60)
        
        # Cleanup test data
        print("\n6. Cleaning up test data...")
        db.delete(test_note)
        db.delete(test_contact)
        db.delete(test_email)
        
        # Delete generated documents
        from app.models.document import Document
        db.query(Document).filter(
            Document.user_id == user_id,
            Document.source_id.in_(['test_email_001', 'test_contact_001', 'test_note_001'])
        ).delete()
        
        db.commit()
        print("  ✓ Test data cleaned up")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  Make sure you have:")
    print("  1. Created a user in the database (user_id = 1)")
    print("  2. Set OPENAI_API_KEY in .env")
    print("  3. Run: alembic upgrade head\n")
    
    asyncio.run(test_rag_pipeline())