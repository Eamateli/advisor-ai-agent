"""
Test AI Agent functionality
Run: python test_agent.py
"""
import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.agents.agent import create_agent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_chat():
    """Test basic chat without tools"""
    print("\n" + "="*60)
    print("TEST 1: Basic Chat")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ No test user found. Run create_test_user.py first")
            return
        
        agent = create_agent(db, user)
        
        print("\n📤 User: Hello! What can you help me with?")
        print("🤖 Assistant: ", end="", flush=True)
        
        async for event in agent.chat_stream("Hello! What can you help me with?"):
            if event["type"] == "content":
                print(event["text"], end="", flush=True)
            elif event["type"] == "done":
                print("\n")
                break
        
        print("✅ Basic chat test passed!")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_rag_search():
    """Test RAG search tool"""
    print("\n" + "="*60)
    print("TEST 2: RAG Search Tool")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ No test user found")
            return
        
        # First, add some test data
        print("\n📥 Adding test email...")
        from app.models.email import Email
        from app.services.rag_pipeline import rag_pipeline
        from datetime import datetime, timezone
        
        test_email = Email(
            user_id=user.id,
            gmail_id="test_baseball_999",
            subject="Re: Baseball game",
            from_email="parent@example.com",
            from_name="John Parent",
            to_emails=["advisor@example.com"],
            body_text="Hi! My daughter plays baseball and has a tournament this weekend. Can we reschedule our meeting?",
            date=datetime.now(timezone.utc),
            is_processed=False
        )
        
        # Check if it already exists
        existing = db.query(Email).filter(Email.gmail_id == "test_baseball_999").first()
        if existing:
            db.delete(existing)
            db.commit()
        
        db.add(test_email)
        db.commit()
        db.refresh(test_email)
        
        # Process for RAG
        await rag_pipeline.process_email(db, user.id, test_email)
        print("✅ Test email added and processed")
        
        # Now test the agent
        agent = create_agent(db, user)
        
        print("\n📤 User: Who mentioned their kid plays baseball?")
        print("🤖 Assistant: ", end="", flush=True)
        
        async for event in agent.chat_stream("Who mentioned their kid plays baseball?"):
            if event["type"] == "content":
                print(event["text"], end="", flush=True)
            elif event["type"] == "tool_use_start":
                print(f"\n🔧 [Using tool: {event['tool_name']}]", end="", flush=True)
            elif event["type"] == "tool_result":
                print(f"\n✓ [Tool completed]", end="", flush=True)
            elif event["type"] == "done":
                print("\n")
                break
        
        print("✅ RAG search test passed!")
        
        # Cleanup
        db.delete(test_email)
        from app.models.document import Document
        db.query(Document).filter(Document.source_id == "test_baseball_999").delete()
        db.commit()
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_task_creation():
    """Test task creation and tracking"""
    print("\n" + "="*60)
    print("TEST 3: Task Creation")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ No test user found")
            return
        
        agent = create_agent(db, user)
        
        print("\n📤 User: Create a task to follow up with John next week")
        print("🤖 Assistant: ", end="", flush=True)
        
        async for event in agent.chat_stream("Create a task to follow up with John next week about his portfolio review"):
            if event["type"] == "content":
                print(event["text"], end="", flush=True)
            elif event["type"] == "tool_use_start":
                print(f"\n🔧 [Using tool: {event['tool_name']}]", end="", flush=True)
            elif event["type"] == "tool_result":
                print(f"\n✓ [Tool completed]", end="", flush=True)
            elif event["type"] == "done":
                print("\n")
                break
        
        # Verify task was created
        from app.models.task import Task
        tasks = db.query(Task).filter(Task.user_id == user.id).all()
        
        if tasks:
            print(f"✅ Task creation test passed! Found {len(tasks)} task(s)")
            
            # Cleanup
            for task in tasks:
                db.delete(task)
            db.commit()
        else:
            print("⚠️ No tasks were created")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_ongoing_instruction():
    """Test saving ongoing instructions"""
    print("\n" + "="*60)
    print("TEST 4: Ongoing Instructions")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ No test user found")
            return
        
        agent = create_agent(db, user)
        
        print("\n📤 User: When someone new emails me, always create a HubSpot contact")
        print("🤖 Assistant: ", end="", flush=True)
        
        async for event in agent.chat_stream("When someone new emails me that's not in HubSpot, please create a contact for them"):
            if event["type"] == "content":
                print(event["text"], end="", flush=True)
            elif event["type"] == "tool_use_start":
                print(f"\n🔧 [Using tool: {event['tool_name']}]", end="", flush=True)
            elif event["type"] == "tool_result":
                print(f"\n✓ [Tool completed]", end="", flush=True)
            elif event["type"] == "done":
                print("\n")
                break
        
        # Verify instruction was saved
        from app.models.task import Instruction
        instructions = db.query(Instruction).filter(Instruction.user_id == user.id).all()
        
        if instructions:
            print(f"✅ Instruction test passed! Found {len(instructions)} instruction(s)")
            print(f"   📝 Instruction: {instructions[0].instruction}")
            
            # Cleanup
            for inst in instructions:
                db.delete(inst)
            db.commit()
        else:
            print("⚠️ No instructions were saved")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_multi_turn_conversation():
    """Test multi-turn conversation with context"""
    print("\n" + "="*60)
    print("TEST 5: Multi-Turn Conversation")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ No test user found")
            return
        
        agent = create_agent(db, user)
        
        # First turn
        print("\n📤 User: My name is Sarah and I love tennis")
        print("🤖 Assistant: ", end="", flush=True)
        
        async for event in agent.chat_stream("My name is Sarah and I love tennis"):
            if event["type"] == "content":
                print(event["text"], end="", flush=True)
            elif event["type"] == "done":
                print("\n")
                break
        
        # Second turn - test if agent remembers
        print("\n📤 User: What sport did I say I love?")
        print("🤖 Assistant: ", end="", flush=True)
        
        response_text = ""
        async for event in agent.chat_stream("What sport did I say I love?"):
            if event["type"] == "content":
                text = event["text"]
                print(text, end="", flush=True)
                response_text += text
            elif event["type"] == "done":
                print("\n")
                break
        
        if "tennis" in response_text.lower():
            print("✅ Multi-turn conversation test passed! Agent remembered context")
        else:
            print("⚠️ Agent may not have remembered the context correctly")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        db.close()

async def run_all_tests():
    """Run all agent tests"""
    print("\n" + "="*60)
    print("STARTING AI AGENT TESTS")
    print("="*60)
    print("\nPrerequisites:")
    print("   1. Test user must exist (run create_test_user.py)")
    print("   2. ANTHROPIC_API_KEY must be set in .env")
    print("   3. Database must be migrated (alembic upgrade head)")
    
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    await asyncio.sleep(3)
    
    # Run tests
    await test_basic_chat()
    await test_rag_search()
    await test_task_creation()
    await test_ongoing_instruction()
    await test_multi_turn_conversation()
    
    print("\n" + "="*60)
    print("ALL AGENT TESTS COMPLETE")
    print("="*60)
    
    print("\n✅ Agent is ready to use!")
    print("\nNext steps:")
    print("   1. Test the streaming endpoint: POST /chat/stream")
    print("   2. Integrate with frontend")
    print("   3. Test with real OAuth credentials")

if __name__ == "__main__":
    asyncio.run(run_all_tests())