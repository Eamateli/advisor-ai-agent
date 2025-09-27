from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.email import Email
from app.models.hubspot import HubSpotContact, HubSpotNote
from app.services.chunking import chunking_service
from app.services.embeddings import embedding_service
from app.services.vector_search import vector_search_service
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Main RAG pipeline for processing and searching documents"""
    
    async def process_email(
        self,
        db: Session,
        user_id: int,
        email: Email
    ) -> List[Document]:
        """Process an email into document chunks with embeddings"""
        try:
            # Prepare email data
            email_data = {
                'gmail_id': email.gmail_id,
                'subject': email.subject,
                'from_email': email.from_email,
                'from_name': email.from_name,
                'to_emails': email.to_emails,
                'date': email.date,
                'body_html': email.body_html,
                'body_text': email.body_text,
            }
            
            # Chunk the email
            chunks = chunking_service.chunk_email(email_data)
            
            if not chunks:
                logger.warning(f"No chunks generated for email {email.gmail_id}")
                return []
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Create document records
            documents = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = Document(
                    user_id=user_id,
                    doc_type='email',
                    source_id=email.gmail_id,
                    title=email.subject,
                    content=email.body_text or email.body_html,
                    chunk_text=chunk['text'],
                    chunk_index=idx,
                    embedding=embedding,
                    metadata=chunk['metadata']
                )
                documents.append(doc)
                db.add(doc)
            
            # Mark email as processed
            email.is_processed = True
            email.processed_at = func.now()
            
            db.commit()
            
            logger.info(f"Processed email {email.gmail_id} into {len(documents)} chunks")
            return documents
        
        except Exception as e:
            logger.error(f"Error processing email {email.gmail_id}: {e}")
            db.rollback()
            raise
    
    async def process_hubspot_contact(
        self,
        db: Session,
        user_id: int,
        contact: HubSpotContact
    ) -> List[Document]:
        """Process a HubSpot contact into document chunks with embeddings"""
        try:
            # Prepare contact data
            contact_data = {
                'hubspot_id': contact.hubspot_id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
                'phone': contact.phone,
                'company': contact.company,
                'properties': contact.properties,
            }
            
            # Chunk the contact
            chunks = chunking_service.chunk_hubspot_contact(contact_data)
            
            if not chunks:
                logger.warning(f"No chunks generated for contact {contact.hubspot_id}")
                return []
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Create document records
            documents = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = Document(
                    user_id=user_id,
                    doc_type='hubspot_contact',
                    source_id=contact.hubspot_id,
                    title=f"{contact.first_name} {contact.last_name}".strip(),
                    content=chunk['text'],
                    chunk_text=chunk['text'],
                    chunk_index=idx,
                    embedding=embedding,
                    metadata=chunk['metadata']
                )
                documents.append(doc)
                db.add(doc)
            
            # Mark contact as processed
            contact.is_processed = True
            contact.processed_at = func.now()
            
            db.commit()
            
            logger.info(f"Processed contact {contact.hubspot_id} into {len(documents)} chunks")
            return documents
        
        except Exception as e:
            logger.error(f"Error processing contact {contact.hubspot_id}: {e}")
            db.rollback()
            raise
    
    async def process_hubspot_note(
        self,
        db: Session,
        user_id: int,
        note: HubSpotNote
    ) -> List[Document]:
        """Process a HubSpot note into document chunks with embeddings"""
        try:
            # Get associated contact
            contact = db.query(HubSpotContact).filter(
                HubSpotContact.id == note.contact_id
            ).first()
            
            # Prepare note data
            note_data = {
                'hubspot_id': note.hubspot_id,
                'body': note.body,
                'created_by': note.created_by,
                'created_at': note.created_at,
            }
            
            contact_data = None
            if contact:
                contact_data = {
                    'hubspot_id': contact.hubspot_id,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'email': contact.email,
                }
            
            # Chunk the note
            chunks = chunking_service.chunk_hubspot_note(note_data, contact_data)
            
            if not chunks:
                logger.warning(f"No chunks generated for note {note.hubspot_id}")
                return []
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Create document records
            documents = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = Document(
                    user_id=user_id,
                    doc_type='hubspot_note',
                    source_id=note.hubspot_id,
                    title=f"Note about {contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip() if contact_data else "Note",
                    content=note.body,
                    chunk_text=chunk['text'],
                    chunk_index=idx,
                    embedding=embedding,
                    metadata=chunk['metadata']
                )
                documents.append(doc)
                db.add(doc)
            
            # Mark note as processed
            note.is_processed = True
            note.processed_at = func.now()
            
            db.commit()
            
            logger.info(f"Processed note {note.hubspot_id} into {len(documents)} chunks")
            return documents
        
        except Exception as e:
            logger.error(f"Error processing note {note.hubspot_id}: {e}")
            db.rollback()
            raise
    
    async def search_context(
        self,
        db: Session,
        user_id: int,
        query: str,
        doc_types: Optional[List[str]] = None,
        metadata_filters: Optional[Dict] = None
    ) -> Dict:
        """
        Search for relevant context given a query
        
        Returns:
            Dict with 'documents' list and 'formatted_context' string
        """
        documents = await vector_search_service.search_documents(
            db=db,
            user_id=user_id,
            query=query,
            doc_types=doc_types,
            metadata_filters=metadata_filters
        )
        
        formatted_context = vector_search_service.format_context_for_llm(documents)
        
        return {
            'documents': documents,
            'formatted_context': formatted_context,
            'document_count': len(documents)
        }
    
    async def batch_process_emails(
        self,
        db: Session,
        user_id: int,
        limit: int = 100
    ):
        """Process unprocessed emails in batch"""
        # Get unprocessed emails
        emails = db.query(Email).filter(
            Email.user_id == user_id,
            Email.is_processed == False
        ).limit(limit).all()
        
        logger.info(f"Processing {len(emails)} unprocessed emails for user {user_id}")
        
        for email in emails:
            try:
                await self.process_email(db, user_id, email)
            except Exception as e:
                logger.error(f"Error processing email {email.gmail_id}: {e}")
                continue
        
        logger.info(f"Completed batch processing for user {user_id}")
    
    async def batch_process_contacts(
        self,
        db: Session,
        user_id: int,
        limit: int = 100
    ):
        """Process unprocessed HubSpot contacts in batch"""
        contacts = db.query(HubSpotContact).filter(
            HubSpotContact.user_id == user_id,
            HubSpotContact.is_processed == False
        ).limit(limit).all()
        
        logger.info(f"Processing {len(contacts)} unprocessed contacts for user {user_id}")
        
        for contact in contacts:
            try:
                await self.process_hubspot_contact(db, user_id, contact)
            except Exception as e:
                logger.error(f"Error processing contact {contact.hubspot_id}: {e}")
                continue
        
        logger.info(f"Completed batch contact processing for user {user_id}")
    
    async def batch_process_notes(
        self,
        db: Session,
        user_id: int,
        limit: int = 100
    ):
        """Process unprocessed HubSpot notes in batch"""
        notes = db.query(HubSpotNote).filter(
            HubSpotNote.user_id == user_id,
            HubSpotNote.is_processed == False
        ).limit(limit).all()
        
        logger.info(f"Processing {len(notes)} unprocessed notes for user {user_id}")
        
        for note in notes:
            try:
                await self.process_hubspot_note(db, user_id, note)
            except Exception as e:
                logger.error(f"Error processing note {note.hubspot_id}: {e}")
                continue
        
        logger.info(f"Completed batch note processing for user {user_id}")

rag_pipeline = RAGPipeline()