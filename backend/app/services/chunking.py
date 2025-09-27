from typing import List, Dict
import re
from bs4 import BeautifulSoup
import html2text
from app.core.config import settings
import tiktoken
import logging

logger = logging.getLogger(__name__)

class ChunkingService:
    """Handles text chunking for embeddings with advanced strategies"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
        # Initialize tokenizer for token-based chunking
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
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
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}, using char estimate")
            return len(text) // 4  # Rough estimate: 1 token ≈ 4 chars
    
    def chunk_text(self, text: str, doc_metadata: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks (basic strategy)
        
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
                    'tokens': self.count_tokens(chunk_text),
                    'doc_metadata': doc_metadata or {}
                })
                
                # Start new chunk with overlap
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
                'tokens': self.count_tokens(chunk_text),
                'doc_metadata': doc_metadata or {}
            })
        
        return chunks
    
    def semantic_chunk(self, text: str, doc_metadata: Dict = None, max_tokens: int = 400) -> List[Dict]:
        """
        Semantic chunking: Split on semantic boundaries (paragraphs, sections)
        
        Better for preserving context and meaning.
        """
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.count_tokens(para)
            
            # If paragraph alone exceeds max, split it recursively
            if para_tokens > max_tokens:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'length': len(chunk_text),
                        'tokens': self.count_tokens(chunk_text),
                        'doc_metadata': doc_metadata or {}
                    })
                    current_chunk = []
                    current_tokens = 0
                
                # Recursively split large paragraph by sentences
                sentence_chunks = self.recursive_chunk(para, doc_metadata, max_tokens)
                chunks.extend(sentence_chunks)
            
            # If adding paragraph exceeds limit, save current chunk
            elif current_tokens + para_tokens > max_tokens and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'length': len(chunk_text),
                    'tokens': self.count_tokens(chunk_text),
                    'doc_metadata': doc_metadata or {}
                })
                current_chunk = [para]
                current_tokens = para_tokens
            
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'length': len(chunk_text),
                'tokens': self.count_tokens(chunk_text),
                'doc_metadata': doc_metadata or {}
            })
        
        return chunks
    
    def recursive_chunk(self, text: str, doc_metadata: Dict = None, max_tokens: int = 400) -> List[Dict]:
        """
        Recursive chunking: Try multiple separators in order
        
        Order: Paragraphs -> Sentences -> Words
        """
        if not text or len(text.strip()) == 0:
            return []
        
        text_tokens = self.count_tokens(text)
        
        # If text fits in one chunk, return it
        if text_tokens <= max_tokens:
            return [{
                'text': text,
                'length': len(text),
                'tokens': text_tokens,
                'doc_metadata': doc_metadata or {}
            }]
        
        chunks = []
        
        # Try splitting by paragraphs first
        if '\n\n' in text:
            paragraphs = re.split(r'\n\s*\n', text)
            current_chunk = []
            current_tokens = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                para_tokens = self.count_tokens(para)
                
                if current_tokens + para_tokens > max_tokens and current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'length': len(chunk_text),
                        'tokens': self.count_tokens(chunk_text),
                        'doc_metadata': doc_metadata or {}
                    })
                    current_chunk = []
                    current_tokens = 0
                
                # If single paragraph is too large, split by sentences
                if para_tokens > max_tokens:
                    if current_chunk:
                        chunk_text = '\n\n'.join(current_chunk)
                        chunks.append({
                            'text': chunk_text,
                            'length': len(chunk_text),
                            'tokens': self.count_tokens(chunk_text),
                            'doc_metadata': doc_metadata or {}
                        })
                        current_chunk = []
                        current_tokens = 0
                    
                    # Recursively split by sentences
                    sentence_chunks = self._split_by_sentences(para, doc_metadata, max_tokens)
                    chunks.extend(sentence_chunks)
                else:
                    current_chunk.append(para)
                    current_tokens += para_tokens
            
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'length': len(chunk_text),
                    'tokens': self.count_tokens(chunk_text),
                    'doc_metadata': doc_metadata or {}
                })
        
        # If no paragraphs, try sentences
        else:
            chunks = self._split_by_sentences(text, doc_metadata, max_tokens)
        
        return chunks
    
    def _split_by_sentences(self, text: str, doc_metadata: Dict, max_tokens: int) -> List[Dict]:
        """Split text by sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'length': len(chunk_text),
                    'tokens': self.count_tokens(chunk_text),
                    'doc_metadata': doc_metadata or {}
                })
                current_chunk = []
                current_tokens = 0
            
            # If single sentence too large, split by words (last resort)
            if sentence_tokens > max_tokens:
                word_chunks = self._split_by_words(sentence, doc_metadata, max_tokens)
                chunks.extend(word_chunks)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'length': len(chunk_text),
                'tokens': self.count_tokens(chunk_text),
                'doc_metadata': doc_metadata or {}
            })
        
        return chunks
    
    def _split_by_words(self, text: str, doc_metadata: Dict, max_tokens: int) -> List[Dict]:
        """Split text by words (last resort for very long sentences)"""
        words = text.split()
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self.count_tokens(word)
            
            if current_tokens + word_tokens > max_tokens and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'length': len(chunk_text),
                    'tokens': self.count_tokens(chunk_text),
                    'doc_metadata': doc_metadata or {}
                })
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(word)
            current_tokens += word_tokens
        
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'length': len(chunk_text),
                'tokens': self.count_tokens(chunk_text),
                'doc_metadata': doc_metadata or {}
            })
        
        return chunks
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to prevent XSS and injection"""
        if not text:
            return ""
        
        # Remove any HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        
        # Remove potentially dangerous characters
        text = text.replace('\x00', '')  # Null bytes
        
        # Limit length to prevent DoS
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    def chunk_email(self, email_data: Dict, strategy: str = 'semantic') -> List[Dict]:
        """Chunk an email with doc_metadata using specified strategy"""
        # Clean HTML body
        body = self.clean_html(email_data.get('body_html', '')) or email_data.get('body_text', '')
        
        # Sanitize inputs to prevent XSS
        subject = self._sanitize_text(email_data.get('subject', ''))
        from_email = self._sanitize_text(email_data.get('from_email', ''))
        from_name = self._sanitize_text(email_data.get('from_name', ''))
        
        # Create rich context for each chunk
        full_text = f"Subject: {subject}\n"
        full_text += f"From: {from_name} <{from_email}>\n"
        full_text += f"Date: {email_data.get('date', '')}\n\n"
        full_text += body
        
        doc_metadata = {
            'type': 'email',
            'gmail_id': email_data.get('gmail_id'),
            'subject': subject,
            'from_email': from_email,
            'from_name': from_name,
            'date': str(email_data.get('date', '')),
            'to_emails': email_data.get('to_emails', []),
        }
        
        # Use appropriate chunking strategy
        if strategy == 'semantic':
            chunks = self.semantic_chunk(full_text, doc_metadata)
        elif strategy == 'recursive':
            chunks = self.recursive_chunk(full_text, doc_metadata)
        else:
            chunks = self.chunk_text(full_text, doc_metadata)
        
        return chunks
    
    def chunk_hubspot_contact(self, contact_data: Dict) -> List[Dict]:
        """Chunk a HubSpot contact with doc_metadata"""
        # Build contact description with sanitized inputs
        text_parts = []
        
        first_name = self._sanitize_text(contact_data.get('first_name', ''))
        last_name = self._sanitize_text(contact_data.get('last_name', ''))
        email = self._sanitize_text(contact_data.get('email', ''))
        phone = self._sanitize_text(contact_data.get('phone', ''))
        company = self._sanitize_text(contact_data.get('company', ''))
        
        if first_name or last_name:
            text_parts.append(f"Contact: {first_name} {last_name}".strip())
        if email:
            text_parts.append(f"Email: {email}")
        if phone:
            text_parts.append(f"Phone: {phone}")
        if company:
            text_parts.append(f"Company: {company}")
        
        # Add custom properties (sanitized)
        properties = contact_data.get('properties', {})
        for key, value in properties.items():
            if value and key not in ['firstname', 'lastname', 'email', 'phone', 'company']:
                formatted_key = self._sanitize_text(key.replace('_', ' ').title())
                formatted_value = self._sanitize_text(str(value))
                text_parts.append(f"{formatted_key}: {formatted_value}")
        
        full_text = '\n'.join(text_parts)
        
        doc_metadata = {
            'type': 'hubspot_contact',
            'hubspot_id': contact_data.get('hubspot_id'),
            'contact_name': f"{first_name} {last_name}".strip(),
            'contact_email': email,
            'company': company,
        }
        
        # Contacts are usually short, use semantic chunking
        chunks = self.semantic_chunk(full_text, doc_metadata, max_tokens=300)
        return chunks
    
    def chunk_hubspot_note(self, note_data: Dict, contact_data: Dict = None) -> List[Dict]:
        """Chunk a HubSpot note with doc_metadata"""
        body = self._sanitize_text(note_data.get('body', ''))
        
        # Add contact context
        if contact_data:
            first_name = self._sanitize_text(contact_data.get('first_name', ''))
            last_name = self._sanitize_text(contact_data.get('last_name', ''))
            contact_name = f"{first_name} {last_name}".strip()
            full_text = f"Note about {contact_name}:\n{body}"
        else:
            full_text = f"Note:\n{body}"
        
        doc_metadata = {
            'type': 'hubspot_note',
            'hubspot_id': note_data.get('hubspot_id'),
            'created_by': self._sanitize_text(note_data.get('created_by', '')),
            'created_at': str(note_data.get('created_at', '')),
        }
        
        if contact_data:
            first_name = self._sanitize_text(contact_data.get('first_name', ''))
            last_name = self._sanitize_text(contact_data.get('last_name', ''))
            doc_metadata['contact_name'] = f"{first_name} {last_name}".strip()
            doc_metadata['contact_email'] = self._sanitize_text(contact_data.get('email', ''))
            doc_metadata['contact_hubspot_id'] = contact_data.get('hubspot_id')
        
        # Use semantic chunking for notes
        chunks = self.semantic_chunk(full_text, doc_metadata, max_tokens=300)
        return chunks

chunking_service = ChunkingService()