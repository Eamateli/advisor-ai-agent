from typing import List, Dict, Optional
import httpx
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class HubSpotService:
    """HubSpot CRM API integration"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_contacts(
        self,
        limit: int = 100,
        after: Optional[str] = None,
        properties: Optional[List[str]] = None
    ) -> Dict:
        """
        Get contacts with pagination
        
        Args:
            limit: Number of contacts per page (max 100)
            after: Pagination cursor
            properties: List of properties to retrieve
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            
            params = {"limit": limit}
            
            if after:
                params["after"] = after
            
            if properties:
                params["properties"] = ",".join(properties)
            else:
                # Default properties
                params["properties"] = "firstname,lastname,email,phone,company,lifecyclestage,createdate,lastmodifieddate"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
            
            contacts = []
            for result in data.get('results', []):
                contacts.append(self._format_contact(result))
            
            logger.info(f"Retrieved {len(contacts)} contacts")
            
            return {
                'contacts': contacts,
                'paging': data.get('paging', {})
            }
        
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Get contact by email address"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            
            body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email
                            }
                        ]
                    }
                ],
                "properties": ["firstname", "lastname", "email", "phone", "company"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=body)
                response.raise_for_status()
                data = response.json()
            
            results = data.get('results', [])
            
            if results:
                return self._format_contact(results[0])
            
            return None
        
        except Exception as e:
            logger.error(f"Error searching contact by email: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        additional_properties: Optional[Dict] = None
    ) -> Dict:
        """Create new contact in HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            
            properties = {"email": email}
            
            if first_name:
                properties["firstname"] = first_name
            if last_name:
                properties["lastname"] = last_name
            if phone:
                properties["phone"] = phone
            if company:
                properties["company"] = company
            
            if additional_properties:
                properties.update(additional_properties)
            
            body = {"properties": properties}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=body)
                response.raise_for_status()
                data = response.json()
            
            logger.info(f"Created contact: {data['id']}")
            return self._format_contact(data)
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                logger.warning(f"Contact with email {email} already exists")
                # Try to get existing contact
                return await self.get_contact_by_email(email)
            raise
        
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def update_contact(
        self,
        contact_id: str,
        properties: Dict
    ) -> Dict:
        """Update contact properties"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            
            body = {"properties": properties}
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=body)
                response.raise_for_status()
                data = response.json()
            
            logger.info(f"Updated contact: {contact_id}")
            return self._format_contact(data)
        
        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_contact_notes(self, contact_id: str) -> List[Dict]:
        """Get all notes for a contact"""
        try:
            # First get associated notes
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}/associations/notes"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                associations = response.json()
            
            note_ids = [assoc['id'] for assoc in associations.get('results', [])]
            
            if not note_ids:
                return []
            
            # Get note details
            notes = []
            for note_id in note_ids:
                note = await self._get_note(note_id)
                if note:
                    notes.append(note)
            
            logger.info(f"Retrieved {len(notes)} notes for contact {contact_id}")
            return notes
        
        except Exception as e:
            logger.error(f"Error getting contact notes: {e}")
            raise
    
    async def _get_note(self, note_id: str) -> Optional[Dict]:
        """Get single note details"""
        try:
            url = f"{self.base_url}/crm/v3/objects/notes/{note_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
            
            return self._format_note(data)
        
        except Exception as e:
            logger.error(f"Error getting note {note_id}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_note(
        self,
        contact_id: str,
        note_body: str
    ) -> Dict:
        """Create note and associate with contact"""
        try:
            # Create note
            url = f"{self.base_url}/crm/v3/objects/notes"
            
            body = {
                "properties": {
                    "hs_note_body": note_body,
                    "hs_timestamp": datetime.utcnow().isoformat() + 'Z'
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=body)
                response.raise_for_status()
                note_data = response.json()
            
            note_id = note_data['id']
            
            # Associate note with contact
            assoc_url = f"{self.base_url}/crm/v3/objects/notes/{note_id}/associations/contacts/{contact_id}/note_to_contact"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(assoc_url, headers=self.headers)
                response.raise_for_status()
            
            logger.info(f"Created note {note_id} for contact {contact_id}")
            return self._format_note(note_data)
        
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_activity(
        self,
        contact_id: str,
        activity_type: str,
        subject: str,
        body: Optional[str] = None
    ) -> Dict:
        """
        Create activity (task, email, meeting, note)
        
        Args:
            contact_id: HubSpot contact ID
            activity_type: 'task', 'email', 'meeting', or 'note'
            subject: Activity subject/title
            body: Activity description
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{activity_type}s"
            
            properties = {
                "hs_timestamp": datetime.utcnow().isoformat() + 'Z'
            }
            
            if activity_type == 'note':
                properties["hs_note_body"] = body or subject
            elif activity_type == 'email':
                properties["hs_email_subject"] = subject
                properties["hs_email_text"] = body or ""
            elif activity_type == 'task':
                properties["hs_task_subject"] = subject
                properties["hs_task_body"] = body or ""
            elif activity_type == 'meeting':
                properties["hs_meeting_title"] = subject
                properties["hs_meeting_body"] = body or ""
            
            body_data = {"properties": properties}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=body_data)
                response.raise_for_status()
                activity_data = response.json()
            
            activity_id = activity_data['id']
            
            # Associate with contact
            assoc_url = f"{self.base_url}/crm/v3/objects/{activity_type}s/{activity_id}/associations/contacts/{contact_id}/{activity_type}_to_contact"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(assoc_url, headers=self.headers)
                response.raise_for_status()
            
            logger.info(f"Created {activity_type} {activity_id} for contact {contact_id}")
            return activity_data
        
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_contacts(
        self,
        query: str,
        property_to_search: str = "email"
    ) -> List[Dict]:
        """Search contacts by property"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            
            body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": property_to_search,
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }
                        ]
                    }
                ],
                "properties": ["firstname", "lastname", "email", "phone", "company"],
                "limit": 50
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=body)
                response.raise_for_status()
                data = response.json()
            
            contacts = []
            for result in data.get('results', []):
                contacts.append(self._format_contact(result))
            
            logger.info(f"Found {len(contacts)} contacts matching '{query}'")
            return contacts
        
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            raise
    
    async def batch_sync_contacts(
        self,
        limit: int = 500
    ) -> List[Dict]:
        """Batch sync all contacts for RAG indexing"""
        logger.info("Starting batch contact sync")
        
        all_contacts = []
        after = None
        
        while len(all_contacts) < limit:
            result = await self.get_contacts(
                limit=min(100, limit - len(all_contacts)),
                after=after
            )
            
            all_contacts.extend(result['contacts'])
            
            paging = result.get('paging', {})
            after = paging.get('next', {}).get('after')
            
            if not after:
                break
        
        logger.info(f"Batch sync complete: {len(all_contacts)} contacts")
        return all_contacts
    
    async def batch_sync_notes(
        self,
        contact_ids: List[str]
    ) -> List[Dict]:
        """Batch sync notes for multiple contacts"""
        logger.info(f"Starting batch note sync for {len(contact_ids)} contacts")
        
        all_notes = []
        
        for contact_id in contact_ids:
            try:
                notes = await self.get_contact_notes(contact_id)
                all_notes.extend(notes)
            except Exception as e:
                logger.error(f"Error syncing notes for contact {contact_id}: {e}")
                continue
        
        logger.info(f"Batch note sync complete: {len(all_notes)} notes")
        return all_notes
    
    def _format_contact(self, contact_data: Dict) -> Dict:
        """Format HubSpot contact into clean structure"""
        props = contact_data.get('properties', {})
        
        return {
            'hubspot_id': contact_data['id'],
            'email': props.get('email'),
            'first_name': props.get('firstname'),
            'last_name': props.get('lastname'),
            'phone': props.get('phone'),
            'company': props.get('company'),
            'lifecycle_stage': props.get('lifecyclestage'),
            'created_at': props.get('createdate'),
            'updated_at': props.get('lastmodifieddate'),
            'properties': props  # Store all properties
        }
    
    def _format_note(self, note_data: Dict) -> Dict:
        """Format HubSpot note into clean structure"""
        props = note_data.get('properties', {})
        
        return {
            'hubspot_id': note_data['id'],
            'body': props.get('hs_note_body'),
            'created_at': props.get('hs_timestamp') or props.get('createdate'),
            'created_by': props.get('hubspot_owner_id'),
            'updated_at': props.get('hs_lastmodifieddate')
        }