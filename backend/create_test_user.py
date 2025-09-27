"""
Create a test user for testing the RAG pipeline
Run: python create_test_user.py
"""
from app.core.database import SessionLocal
from app.models.user import User

# Import all models to avoid circular import issues
from app.models.document import Document
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.models.chat import ChatMessage
from app.models.task import Task, Instruction

def create_test_user():
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if existing_user:
            print(f"✓ User already exists: ID={existing_user.id}, Email={existing_user.email}")
            return existing_user.id
        else:
            user = User(
                email="test@example.com",
                full_name="Test User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✓ Created user: ID={user.id}, Email={user.email}")
            return user.id
    
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    user_id = create_test_user()
    print(f"\nTest user ID: {user_id}")
    print("You can now use this user_id for testing the RAG pipeline")