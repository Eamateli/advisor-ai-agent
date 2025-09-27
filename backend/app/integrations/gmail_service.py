from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from datetime import datetime, timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GmailService:
    """Gmail API integration with retry logic and rate limiting"""
    
    def __init__(self, credentials: Credentials):
        self.service = build('gmail', 'v1', credentials=credentials)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_messages(
        self,
        max_results: int = 100,
        query: str = "",
        page_token: Optional[str] = None
    ) -> Dict:
        """
        Fetch messages with pagination
        
        Query examples:
        - "is:unread" - unread messages
        - "from:example@email.com" - from specific sender
        - "after:2024/01/01" - messages after date
        - "has:attachment" - with attachments
        """
        try:
            result = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query,
                pageToken=page_token
            ).execute()
            
            messages = result.get('messages', [])
            next_page_token = result.get('nextPageToken')
            
            logger.info(f"Fetched {len(messages)} messages")
            
            return {
                'messages': messages,
                'next_page_token': next_page_token
            }
        
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_message_detail(self, message_id: str) -> Dict:
        """Get full message details including body"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Parse message into structured format
            parsed = self._parse_message(message)
            return parsed
        
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise
    
    def _parse_message(self, message: Dict) -> Dict:
        """Parse Gmail API message into clean format"""
        headers = message.get('payload', {}).get('headers', [])
        
        # Extract headers
        subject = self._get_header(headers, 'Subject')
        from_email = self._get_header(headers, 'From')
        to_emails = self._get_header(headers, 'To')
        cc_emails = self._get_header(headers, 'Cc')
        date_str = self._get_header(headers, 'Date')
        
        # Parse sender
        from_name, from_addr = self._parse_email_address(from_email)
        
        # Parse date
        date = self._parse_date(date_str)
        
        # Extract body
        body_text, body_html = self._extract_body(message.get('payload', {}))
        
        # Get labels
        labels = message.get('labelIds', [])
        
        return {
            'gmail_id': message['id'],
            'thread_id': message.get('threadId'),
            'subject': subject,
            'from_email': from_addr,
            'from_name': from_name,
            'to_emails': self._parse_email_list(to_emails),
            'cc_emails': self._parse_email_list(cc_emails),
            'body_text': body_text,
            'body_html': body_html,
            'snippet': message.get('snippet', ''),
            'date': date,
            'labels': labels,
            'is_read': 'UNREAD' not in labels,
            'is_important': 'IMPORTANT' in labels
        }
    
    def _extract_body(self, payload: Dict) -> tuple:
        """Extract text and HTML body from message payload"""
        body_text = ""
        body_html = ""
        
        # Check if simple message
        if 'body' in payload and payload['body'].get('data'):
            data = payload['body']['data']
            decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            mime_type = payload.get('mimeType', '')
            if 'text/plain' in mime_type:
                body_text = decoded
            elif 'text/html' in mime_type:
                body_html = decoded
                body_text = self._html_to_text(decoded)
        
        # Check if multipart
        elif 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if 'body' in part and part['body'].get('data'):
                    data = part['body']['data']
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    
                    if mime_type == 'text/plain':
                        body_text = decoded
                    elif mime_type == 'text/html':
                        body_html = decoded
                        if not body_text:
                            body_text = self._html_to_text(decoded)
                
                # Recursive for nested parts
                elif 'parts' in part:
                    nested_text, nested_html = self._extract_body(part)
                    if not body_text:
                        body_text = nested_text
                    if not body_html:
                        body_html = nested_html
        
        return body_text, body_html
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Get header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""
    
    def _parse_email_address(self, email_str: str) -> tuple:
        """Parse 'Name <email@example.com>' format"""
        if not email_str:
            return "", ""
        
        if '<' in email_str and '>' in email_str:
            name = email_str.split('<')[0].strip().strip('"')
            email = email_str.split('<')[1].split('>')[0].strip()
            return name, email
        else:
            return "", email_str.strip()
    
    def _parse_email_list(self, email_str: str) -> List[str]:
        """Parse comma-separated email list"""
        if not email_str:
            return []
        
        emails = []
        for part in email_str.split(','):
            _, email = self._parse_email_address(part)
            if email:
                emails.append(email)
        return emails
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string"""
        if not date_str:
            return None
        
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        cc: Optional[List[str]] = None,
        is_html: bool = False
    ) -> Dict:
        """
        Send email with optional threading
        
        Args:
            to: List of recipient emails
            subject: Email subject
            body: Email body (text or HTML)
            thread_id: Gmail thread ID to reply in thread
            cc: Optional CC recipients
            is_html: If True, body is HTML
        """
        try:
            # Create message
            if is_html:
                message = MIMEMultipart('alternative')
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(body)
            
            message['To'] = ', '.join(to)
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            # Add threading headers if replying
            if thread_id:
                # Get original message to extract Message-ID
                try:
                    original = self.service.users().messages().get(
                        userId='me',
                        id=thread_id,
                        format='metadata',
                        metadataHeaders=['Message-ID']
                    ).execute()
                    
                    headers = original.get('payload', {}).get('headers', [])
                    original_message_id = self._get_header(headers, 'Message-ID')
                    
                    if original_message_id:
                        message['In-Reply-To'] = original_message_id
                        message['References'] = original_message_id
                except Exception as e:
                    logger.warning(f"Could not get original message for threading: {e}")
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            send_request = {'raw': raw}
            if thread_id:
                send_request['threadId'] = thread_id
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_request
            ).execute()
            
            logger.info(f"Sent email to {to}, message_id: {sent_message['id']}")
            return sent_message
        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_emails(
        self,
        from_email: Optional[str] = None,
        subject_contains: Optional[str] = None,
        after_date: Optional[datetime] = None,
        has_attachment: bool = False,
        max_results: int = 50
    ) -> List[Dict]:
        """Search emails with filters"""
        
        # Build query
        query_parts = []
        
        if from_email:
            query_parts.append(f"from:{from_email}")
        
        if subject_contains:
            query_parts.append(f"subject:{subject_contains}")
        
        if after_date:
            date_str = after_date.strftime("%Y/%m/%d")
            query_parts.append(f"after:{date_str}")
        
        if has_attachment:
            query_parts.append("has:attachment")
        
        query = " ".join(query_parts)
        
        # Fetch messages
        result = await self.fetch_messages(max_results=max_results, query=query)
        
        # Get full details for each message
        messages = []
        for msg in result['messages']:
            try:
                detail = await self.get_message_detail(msg['id'])
                messages.append(detail)
            except Exception as e:
                logger.error(f"Error getting message detail: {e}")
                continue
        
        return messages
    
    async def batch_sync_emails(
        self,
        days_back: int = 30,
        max_emails: int = 500
    ) -> List[Dict]:
        """
        Batch sync recent emails for RAG indexing
        
        Args:
            days_back: How many days back to sync
            max_emails: Maximum number of emails to sync
        """
        after_date = datetime.now() - timedelta(days=days_back)
        date_str = after_date.strftime("%Y/%m/%d")
        
        logger.info(f"Starting batch sync for emails after {date_str}")
        
        all_messages = []
        page_token = None
        
        while len(all_messages) < max_emails:
            result = await self.fetch_messages(
                max_results=min(100, max_emails - len(all_messages)),
                query=f"after:{date_str}",
                page_token=page_token
            )
            
            # Get details for each message
            for msg in result['messages']:
                try:
                    detail = await self.get_message_detail(msg['id'])
                    all_messages.append(detail)
                except Exception as e:
                    logger.error(f"Error getting message: {e}")
                    continue
            
            page_token = result.get('next_page_token')
            if not page_token:
                break
        
        logger.info(f"Batch sync complete: {len(all_messages)} emails")
        return all_messages