from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import Dict, List
from app.integrations.gmail_service import GmailService
from app.integrations.calendar_service import CalendarService
from app.integrations.hubspot_service import HubSpotService
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.services.rag_pipeline import rag_pipeline
from app.core.auth import get_google_credentials, get_hubspot_token

logger = logging.getLogger(__name__)

class BatchSyncService:
    """Orchestrate batch syncing from all external services"""
    
    async def sync_all(
        self,
        db: Session,
        user_id: int,
        gmail_credentials,
        hubspot_token: str,
        days_back: int = 30
    ) -> Dict:
        """
        Sync all data from Gmail, Calendar, and HubSpot
        
        Returns summary of synced data
        """
        logger.info(f"Starting full batch sync for user {user_id}")
        
        summary = {
            'emails_synced': 0,
            'contacts_synced': 0,
            'notes_synced': 0,
            'errors': []
        }
        
        # 1. Sync Gmail
        try:
            gmail_service = GmailService(gmail_credentials)
            emails = await gmail_service.batch_sync_emails(
                days_back=days_back,
                max_emails=500
            )
            
            # Save to database
            for email_data in emails:
                await self._save_email(db, user_id, email_data)
            
            summary['emails_synced'] = len(emails)
            logger.info(f"Gmail sync complete: {len(emails)} emails")
        
        except Exception as e:
            error_msg = f"Gmail sync failed: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
        
        # 2. Sync HubSpot Contacts
        try:
            hubspot_service = HubSpotService(hubspot_token)
            contacts = await hubspot_service.batch_sync_contacts(limit=500)
            
            # Save to database
            contact_ids = []
            for contact_data in contacts:
                contact_id = await self._save_contact(db, user_id, contact_data)
                if contact_id:
                    contact_ids.append(contact_data['hubspot_id'])
            
            summary['contacts_synced'] = len(contacts)
            logger.info(f"HubSpot contacts sync complete: {len(contacts)} contacts")
            
            # 3. Sync HubSpot Notes for all contacts
            notes = await hubspot_service.batch_sync_notes(contact_ids)
            
            for note_data in notes:
                await self._save_note(db, user_id, note_data)
            
            summary['notes_synced'] = len(notes)
            logger.info(f"HubSpot notes sync complete: {len(notes)} notes")
        
        except Exception as e:
            error_msg = f"HubSpot sync failed: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
        
        # 4. Process everything for RAG
        try:
            await self._process_for_rag(db, user_id)
            logger.info("RAG processing complete")
        except Exception as e:
            error_msg = f"RAG processing failed: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
        
        logger.info(f"Batch sync complete for user {user_id}: {summary}")
        return summary
    
    async def sync_gmail_incremental(
        self,
        db: Session,
        user_id: int,
        gmail_credentials,
        since_date: datetime = None
    ) -> int:
        """Incremental Gmail sync for new emails"""
        if not since_date:
            # Get last synced email date
            last_email = db.query(Email).filter(
                Email.user_id == user_id
            ).order_by(Email.date.desc()).first()
            
            if last_email and last_email.date:
                since_date = last_email.date
            else:
                since_date = datetime.now() - timedelta(days=7)
        
        logger.info(f"Incremental Gmail sync since {since_date}")
        
        gmail_service = GmailService(gmail_credentials)
        
        # Search for new emails
        emails = await gmail_service.search_emails(
            after_date=since_date,
            max_results=100
        )
        
        new_count = 0
        for email_data in emails:
            # Check if already exists
            existing = db.query(Email).filter(
                Email.gmail_id == email_data['gmail_id']
            ).first()
            
            if not existing:
                await self._save_email(db, user_id, email_data)
                new_count += 1
        
        logger.info(f"Incremental sync: {new_count} new emails")
        return new_count
    
    async def sync_hubspot_incremental(
        self,
        db: Session,
        user_id: int,
        hubspot_token: str
    ) -> Dict:
        """Incremental HubSpot sync for updated contacts"""
        logger.info("Incremental HubSpot sync")
        
        hubspot_service = HubSpotService(hubspot_token)
        
        # Get recently modified contacts (last 7 days)
        # Note: HubSpot API doesn't have built-in "since" filter for contacts
        # We'll fetch recent ones and check against database
        
        result = await hubspot_service.get_contacts(limit=100)
        contacts = result['contacts']
        
        new_count = 0
        updated_count = 0
        
        for contact_data in contacts:
            existing = db.query(HubSpotContact).filter(
                HubSpotContact.hubspot_id == contact_data['hubspot_id']
            ).first()
            
            if existing:
                # Check if updated
                if contact_data.get('updated_at') and existing.updated_at:
                    contact_updated = datetime.fromisoformat(
                        contact_data['updated_at'].replace('Z', '+00:00')
                    )
                    
                    if contact_updated > existing.updated_at:
                        await self._update_contact(db, existing, contact_data)
                        updated_count += 1
            else:
                await self._save_contact(db, user_id, contact_data)
                new_count += 1
        
        return {
            'new_contacts': new_count,
            'updated_contacts': updated_count
        }
    
    async def _save_email(self, db: Session, user_id: int, email_data: Dict) -> Email:
        """Save email to database"""
        try:
            # Check if exists
            existing = db.query(Email).filter(
                Email.gmail_id == email_data['gmail_id']
            ).first()
            
            if existing:
                logger.debug(f"Email {email_data['gmail_id']} already exists")
                return existing
            
            email = Email(
                user_id=user_id,
                gmail_id=email_data['gmail_id'],
                thread_id=email_data.get('thread_id'),
                subject=email_data.get('subject'),
                from_email=email_data.get('from_email'),
                from_name=email_data.get('from_name'),
                to_emails=email_data.get('to_emails', []),
                cc_emails=email_data.get('cc_emails', []),
                body_text=email_data.get('body_text'),
                body_html=email_data.get('body_html'),
                snippet=email_data.get('snippet'),
                date=email_data.get('date'),
                labels=email_data.get('labels', []),
                is_read=email_data.get('is_read', False),
                is_important=email_data.get('is_important', False),
                is_processed=False
            )
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            logger.debug(f"Saved email: {email.gmail_id}")
            return email
        
        except Exception as e:
            logger.error(f"Error saving email: {e}")
            db.rollback()
            raise
    
    async def _save_contact(
        self,
        db: Session,
        user_id: int,
        contact_data: Dict
    ) -> int:
        """Save HubSpot contact to database"""
        try:
            # Check if exists
            existing = db.query(HubSpotContact).filter(
                HubSpotContact.hubspot_id == contact_data['hubspot_id']
            ).first()
            
            if existing:
                logger.debug(f"Contact {contact_data['hubspot_id']} already exists")
                return existing.id
            
            # Parse dates
            created_at = None
            if contact_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(
                        contact_data['created_at'].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            contact = HubSpotContact(
                user_id=user_id,
                hubspot_id=contact_data['hubspot_id'],
                email=contact_data.get('email'),
                first_name=contact_data.get('first_name'),
                last_name=contact_data.get('last_name'),
                phone=contact_data.get('phone'),
                company=contact_data.get('company'),
                properties=contact_data.get('properties', {}),
                is_processed=False,
                created_at=created_at
            )
            
            db.add(contact)
            db.commit()
            db.refresh(contact)
            
            logger.debug(f"Saved contact: {contact.hubspot_id}")
            return contact.id
        
        except Exception as e:
            logger.error(f"Error saving contact: {e}")
            db.rollback()
            raise
    
    async def _update_contact(
        self,
        db: Session,
        contact: HubSpotContact,
        contact_data: Dict
    ):
        """Update existing contact"""
        try:
            contact.email = contact_data.get('email', contact.email)
            contact.first_name = contact_data.get('first_name', contact.first_name)
            contact.last_name = contact_data.get('last_name', contact.last_name)
            contact.phone = contact_data.get('phone', contact.phone)
            contact.company = contact_data.get('company', contact.company)
            contact.properties = contact_data.get('properties', contact.properties)
            contact.is_processed = False  # Mark for reprocessing
            
            db.commit()
            logger.debug(f"Updated contact: {contact.hubspot_id}")
        
        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            db.rollback()
            raise
    
    async def _save_note(
        self,
        db: Session,
        user_id: int,
        note_data: Dict
    ):
        """Save HubSpot note to database"""
        try:
            # Check if exists
            existing = db.query(HubSpotNote).filter(
                HubSpotNote.hubspot_id == note_data['hubspot_id']
            ).first()
            
            if existing:
                logger.debug(f"Note {note_data['hubspot_id']} already exists")
                return
            
            # Find contact by hubspot_id (we need to get this from association)
            # For now, skip if we can't determine contact
            # In production, you'd get this from the association API
            
            note = HubSpotNote(
                user_id=user_id,
                hubspot_id=note_data['hubspot_id'],
                body=note_data.get('body'),
                created_by=note_data.get('created_by'),
                is_processed=False
            )
            
            # Note: contact_id would be set via association lookup
            # Skipping for now as it requires additional API call
            
            db.add(note)
            db.commit()
            
            logger.debug(f"Saved note: {note.hubspot_id}")
        
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            db.rollback()
    
    async def _process_for_rag(self, db: Session, user_id: int):
        """Process all unprocessed items for RAG"""
        logger.info("Processing items for RAG indexing")
        
        # Process emails
        await rag_pipeline.batch_process_emails(db, user_id, limit=500)
        
        # Process contacts
        await rag_pipeline.batch_process_contacts(db, user_id, limit=500)
        
        # Process notes
        await rag_pipeline.batch_process_notes(db, user_id, limit=500)
        
        logger.info("RAG processing complete")

batch_sync_service = BatchSyncService()