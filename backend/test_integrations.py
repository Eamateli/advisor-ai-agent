"""
Test all external API integrations
Run: python test_integrations.py
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.integrations.gmail_service import GmailService
from app.integrations.calendar_service import CalendarService
from app.integrations.hubspot_service import HubSpotService
from app.core.auth import get_google_credentials, get_hubspot_token
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gmail_integration():
    """Test Gmail API integration"""
    print("\n" + "="*60)
    print("TESTING GMAIL INTEGRATION")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user or not user.google_access_token:
            print("❌ No user with Google OAuth found")
            print("   Please authenticate with Google first")
            return
        
        # Get credentials
        creds = await get_google_credentials(user, db)
        gmail = GmailService(creds)
        
        # Test 4: Batch sync
        print("\n4. Testing batch_sync_contacts...")
        batch_contacts = await hubspot.batch_sync_contacts(limit=10)
        print(f"   ✓ Batch synced {len(batch_contacts)} contacts")
        
        print("\n✓ HubSpot integration tests passed!")
    
    except Exception as e:
        print(f"\n❌ HubSpot integration test failed: {e}")
        logger.error(f"HubSpot test error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_batch_sync():
    """Test full batch sync service"""
    print("\n" + "="*60)
    print("TESTING BATCH SYNC SERVICE")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ Test user not found")
            return
        
        from app.services.batch_sync import batch_sync_service
        
        # Check OAuth status
        has_google = bool(user.google_access_token)
        has_hubspot = bool(user.hubspot_access_token)
        
        print(f"\nOAuth Status:")
        print(f"   Google: {'✓' if has_google else '✗'}")
        print(f"   HubSpot: {'✓' if has_hubspot else '✗'}")
        
        if not has_google and not has_hubspot:
            print("\n⚠️  No OAuth connections found")
            print("   Please authenticate with Google and/or HubSpot first")
            return
        
        # Get credentials
        gmail_creds = None
        hubspot_token = None
        
        if has_google:
            gmail_creds = await get_google_credentials(user, db)
        
        if has_hubspot:
            hubspot_token = await get_hubspot_token(user, db)
        
        # Run batch sync
        print("\nRunning batch sync (this may take a minute)...")
        summary = await batch_sync_service.sync_all(
            db=db,
            user_id=user.id,
            gmail_credentials=gmail_creds,
            hubspot_token=hubspot_token,
            days_back=7  # Only last week to keep it quick
        )
        
        print("\n✓ Batch Sync Complete!")
        print(f"   Emails synced: {summary['emails_synced']}")
        print(f"   Contacts synced: {summary['contacts_synced']}")
        print(f"   Notes synced: {summary['notes_synced']}")
        
        if summary['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in summary['errors']:
                print(f"   - {error}")
    
    except Exception as e:
        print(f"\n❌ Batch sync test failed: {e}")
        logger.error(f"Batch sync error: {e}", exc_info=True)
    
    finally:
        db.close()

async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🚀 STARTING INTEGRATION TESTS")
    print("="*60)
    print("\n⚠️  Prerequisites:")
    print("   1. User must be authenticated with Google OAuth")
    print("   2. User must be authenticated with HubSpot OAuth")
    print("   3. APIs must be enabled in Google Cloud Console")
    print("   4. Environment variables must be set")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    await asyncio.sleep(3)
    
    # Run tests
    await test_gmail_integration()
    await test_calendar_integration()
    await test_hubspot_integration()
    await test_batch_sync()
    
    print("\n" + "="*60)
    print("✅ ALL INTEGRATION TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    print("\n🧪 Integration Test Suite")
    print("Testing Gmail, Calendar, and HubSpot APIs\n")
    
    asyncio.run(run_all_tests())1: Fetch recent messages
        print("\n1. Testing fetch_messages...")
        result = await gmail.fetch_messages(max_results=5)
        print(f"   ✓ Fetched {len(result['messages'])} messages")
        
        if result['messages']:
            # Test 2: Get message detail
            print("\n2. Testing get_message_detail...")
            msg_id = result['messages'][0]['id']
            detail = await gmail.get_message_detail(msg_id)
            print(f"   ✓ Got message: {detail.get('subject', 'No subject')[:50]}")
            print(f"   From: {detail.get('from_name')} <{detail.get('from_email')}>")
        
        # Test 3: Search emails
        print("\n3. Testing search_emails...")
        emails = await gmail.search_emails(max_results=3)
        print(f"   ✓ Found {len(emails)} emails")
        
        # Test 4: Batch sync (commented out to avoid too many API calls)
        # print("\n4. Testing batch_sync_emails...")
        # batch_emails = await gmail.batch_sync_emails(days_back=7, max_emails=10)
        # print(f"   ✓ Batch synced {len(batch_emails)} emails")
        
        print("\n✓ Gmail integration tests passed!")
    
    except Exception as e:
        print(f"\n❌ Gmail integration test failed: {e}")
        logger.error(f"Gmail test error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_calendar_integration():
    """Test Google Calendar API integration"""
    print("\n" + "="*60)
    print("TESTING GOOGLE CALENDAR INTEGRATION")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user or not user.google_access_token:
            print("❌ No user with Google OAuth found")
            return
        
        # Get credentials
        creds = await get_google_credentials(user, db)
        calendar = CalendarService(creds)
        
        # Test 1: Get upcoming events
        print("\n1. Testing get_upcoming_events...")
        events = await calendar.get_upcoming_events(max_results=5)
        print(f"   ✓ Found {len(events)} upcoming events")
        
        for event in events[:3]:
            print(f"   - {event['summary']} at {event['start_time']}")
        
        # Test 2: Get free slots
        print("\n2. Testing get_free_slots...")
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)
        
        free_slots = await calendar.get_free_slots(
            start_date=start_date,
            end_date=end_date,
            duration_minutes=30
        )
        print(f"   ✓ Found {len(free_slots)} free slots in next 7 days")
        
        if free_slots:
            print(f"   First slot: {free_slots[0]['start_formatted']}")
        
        # Test 3: Search events
        print("\n3. Testing search_events...")
        search_results = await calendar.search_events("meeting", max_results=3)
        print(f"   ✓ Found {len(search_results)} events matching 'meeting'")
        
        print("\n✓ Calendar integration tests passed!")
    
    except Exception as e:
        print(f"\n❌ Calendar integration test failed: {e}")
        logger.error(f"Calendar test error: {e}", exc_info=True)
    
    finally:
        db.close()

async def test_hubspot_integration():
    """Test HubSpot API integration"""
    print("\n" + "="*60)
    print("TESTING HUBSPOT INTEGRATION")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user or not user.hubspot_access_token:
            print("❌ No user with HubSpot OAuth found")
            print("   Please authenticate with HubSpot first")
            return
        
        # Get token
        token = await get_hubspot_token(user, db)
        hubspot = HubSpotService(token)
        
        # Test 1: Get contacts
        print("\n1. Testing get_contacts...")
        result = await hubspot.get_contacts(limit=5)
        contacts = result['contacts']
        print(f"   ✓ Fetched {len(contacts)} contacts")
        
        for contact in contacts[:3]:
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            print(f"   - {name} ({contact.get('email')})")
        
        if contacts:
            test_contact = contacts[0]
            contact_id = test_contact['hubspot_id']
            
            # Test 2: Get contact notes
            print("\n2. Testing get_contact_notes...")
            notes = await hubspot.get_contact_notes(contact_id)
            print(f"   ✓ Found {len(notes)} notes for contact")
            
            # Test 3: Search contacts
            print("\n3. Testing search_contacts...")
            if test_contact.get('email'):
                search_results = await hubspot.search_contacts(
                    test_contact['email'],
                    property_to_search="email"
                )
                print(f"   ✓ Found {len(search_results)} contacts")
        
        # Test