from typing import List, Dict
import re
from bs4 import BeautifulSoup
import html2text
from app.core.config import settings

class ChunkingService:
    """Handles text chunking for embeddings"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
    
    def clean_html(self, html: str) -> str:
        """Convert HTML to clean text"""
        if not html:
            return ""
        
        # Convert HTML to markdown-style text
        text = self.html_converter.handle(html)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Strategy:
        1. Split by sentences to avoid breaking mid-sentence
        2. Create chunks of ~CHUNK_SIZE characters
        3. Add CHUNK_OVERLAP to maintain context
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'length': len(chunk_text),
                    'metadata': metadata or {}
                })
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'length': len(chunk_text),
                'metadata': metadata or {}
            })
        
        return chunks
    
    def chunk_email(self, email_data: Dict) -> List[Dict]:
        """Chunk an email with metadata"""
        # Clean HTML body
        body = self.clean_html(email_data.get('body_html', '')) or email_data.get('body_text', '')
        
        # Create rich context for each chunk
        subject = email_data.get('subject', '')
        from_email = email_data.get('from_email', '')
        from_name = email_data.get('from_name', '')
        date = email_data.get('date', '')
        
        # Prepend subject and metadata to body for better context
        full_text = f"Subject: {subject}\n"
        full_text += f"From: {from_name} <{from_email}>\n"
        full_text += f"Date: {date}\n\n"
        full_text += body
        
        metadata = {
            'type': 'email',
            'gmail_id': email_data.get('gmail_id'),
            'subject': subject,
            'from_email': from_email,
            'from_name': from_name,
            'date': str(date),
            'to_emails': email_data.get('to_emails', []),
        }
        
        chunks = self.chunk_text(full_text, metadata)
        return chunks
    
    def chunk_hubspot_contact(self, contact_data: Dict) -> List[Dict]:
        """Chunk a HubSpot contact with metadata"""
        # Build contact description
        text_parts = []
        
        first_name = contact_data.get('first_name', '')
        last_name = contact_data.get('last_name', '')
        email = contact_data.get('email', '')
        phone = contact_data.get('phone', '')
        company = contact_data.get('company', '')
        
        if first_name or last_name:
            text_parts.append(f"Contact: {first_name} {last_name}".strip())
        if email:
            text_parts.append(f"Email: {email}")
        if phone:
            text_parts.append(f"Phone: {phone}")
        if company:
            text_parts.append(f"Company: {company}")
        
        # Add custom properties
        properties = contact_data.get('properties', {})
        for key, value in properties.items():
            if value and key not in ['firstname', 'lastname', 'email', 'phone', 'company']:
                formatted_key = key.replace('_', ' ').title()
                text_parts.append(f"{formatted_key}: {value}")
        
        full_text = '\n'.join(text_parts)
        
        metadata = {
            'type': 'hubspot_contact',
            'hubspot_id': contact_data.get('hubspot_id'),
            'contact_name': f"{first_name} {last_name}".strip(),
            'contact_email': email,
            'company': company,
        }
        
        # Contacts are usually short, but chunk anyway for consistency
        chunks = self.chunk_text(full_text, metadata)
        return chunks
    
    def chunk_hubspot_note(self, note_data: Dict, contact_data: Dict = None) -> List[Dict]:
        """Chunk a HubSpot note with metadata"""
        body = note_data.get('body', '')
        
        # Add contact context
        if contact_data:
            first_name = contact_data.get('first_name', '')
            last_name = contact_data.get('last_name', '')
            contact_name = f"{first_name} {last_name}".strip()
            full_text = f"Note about {contact_name}:\n{body}"
        else:
            full_text = f"Note:\n{body}"
        
        metadata = {
            'type': 'hubspot_note',
            'hubspot_id': note_data.get('hubspot_id'),
            'created_by': note_data.get('created_by'),
            'created_at': str(note_data.get('created_at', '')),
        }
        
        if contact_data:
            metadata['contact_name'] = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
            metadata['contact_email'] = contact_data.get('email')
            metadata['contact_hubspot_id'] = contact_data.get('hubspot_id')
        
        chunks = self.chunk_text(full_text, metadata)
        return chunks

chunking_service = ChunkingService()