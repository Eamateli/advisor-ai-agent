from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from fastapi import Request
from app.models.user import User
from app.models.task import Task, TaskStatus, Instruction
from app.services.hybrid_search import hybrid_search_service
from app.integrations.gmail_service import GmailService
from app.integrations.calendar_service import CalendarService
from app.integrations.hubspot_service import HubSpotService
from app.core.auth import get_google_credentials, get_hubspot_token
from app.core.audit import audit_logger
from app.models.consent import consent_manager

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Execute agent tools with security checks"""
    
    def __init__(self, db: Session, user: User, request: Request = None):
        self.db = db
        self.user = user
        self.request = request
    
    async def execute(self, tool_name: str, tool_input: Dict) -> Dict[str, Any]:
        """Execute a tool with security checks"""
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            
            # Check consent for sensitive tools
            sensitive_tools = {
                "send_email", "create_calendar_event", "create_hubspot_contact", 
                "add_hubspot_note", "create_task"
            }
            
            if tool_name in sensitive_tools:
                is_allowed, reason = consent_manager.check_consent(
                    db=self.db,
                    user_id=self.user.id,
                    action_type=tool_name
                )
                
                if not is_allowed:
                    return {
                        "success": False,
                        "error": f"Consent required: {reason}",
                        "requires_consent": True,
                        "action_type": tool_name
                    }
            
            # Execute tool
            result = await self._execute_tool(tool_name, tool_input)
            
            # Audit logging
            audit_logger.log_tool_execution(
                db=self.db,
                user_id=self.user.id,
                user_email=self.user.email,
                tool_name=tool_name,
                tool_input=tool_input,
                result=result,
                status="success" if result.get("success") else "failure",
                error=result.get("error"),
                ip_address=self.request.client.host if self.request else None,
                user_agent=self.request.headers.get("user-agent") if self.request else None
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            
            # Audit the error
            audit_logger.log_tool_execution(
                db=self.db,
                user_id=self.user.id,
                user_email=self.user.email,
                tool_name=tool_name,
                tool_input=tool_input,
                result={"success": False, "error": str(e)},
                status="failure",
                error=str(e),
                ip_address=self.request.client.host if self.request else None,
                user_agent=self.request.headers.get("user-agent") if self.request else None
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """Internal tool execution"""
        
        # Route to appropriate handler
        if tool_name == "search_knowledge_base":
            return await self._search_knowledge_base(tool_input)
        
        elif tool_name == "search_emails":
            return await self._search_emails(tool_input)
        
        elif tool_name == "send_email":
            return await self._send_email(tool_input)
        
        elif tool_name == "check_availability":
            return await self._check_availability(tool_input)
        
        elif tool_name == "create_calendar_event":
            return await self._create_calendar_event(tool_input)
        
        elif tool_name == "search_calendar_events":
            return await self._search_calendar_events(tool_input)
        
        elif tool_name == "search_hubspot_contacts":
            return await self._search_hubspot_contacts(tool_input)
        
        elif tool_name == "create_hubspot_contact":
            return await self._create_hubspot_contact(tool_input)
        
        elif tool_name == "add_hubspot_note":
            return await self._add_hubspot_note(tool_input)
        
        elif tool_name == "create_task":
            return await self._create_task(tool_input)
        
        elif tool_name == "update_task":
            return await self._update_task(tool_input)
        
        elif tool_name == "save_instruction":
            return await self._save_instruction(tool_input)
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    
    # RAG TOOL
    async def _search_knowledge_base(self, input_data: Dict) -> Dict:
        """Search RAG knowledge base"""
        query = input_data["query"]
        doc_types = input_data.get("doc_types")
        limit = input_data.get("limit", 10)
        
        documents = await hybrid_search_service.hybrid_search(
            db=self.db,
            user_id=self.user.id,
            query=query,
            doc_types=doc_types,
            limit=limit
        )
        
        from app.services.vector_search import vector_search_service
        formatted_context = vector_search_service.format_context_for_llm(documents)
        
        return {
            "success": True,
            "result": {
                "context": formatted_context,
                "document_count": len(documents)
            }
        }
    
    # EMAIL TOOLS
    async def _search_emails(self, input_data: Dict) -> Dict:
        """Search emails"""
        creds = await get_google_credentials(self.user, self.db)
        gmail = GmailService(creds)
        
        from_email = input_data.get("from_email")
        subject_contains = input_data.get("subject_contains")
        days_back = input_data.get("days_back", 30)
        after_date = datetime.now() - timedelta(days=days_back)
        
        emails = await gmail.search_emails(
            from_email=from_email,
            subject_contains=subject_contains,
            after_date=after_date,
            max_results=20
        )
        
        formatted_emails = []
        for email in emails:
            formatted_emails.append({
                "subject": email.get("subject"),
                "from": f"{email.get('from_name')} <{email.get('from_email')}>",
                "date": str(email.get("date")),
                "snippet": email.get("snippet")
            })
        
        return {
            "success": True,
            "result": {
                "emails": formatted_emails,
                "count": len(emails)
            }
        }
    
    async def _send_email(self, input_data: Dict) -> Dict:
        """Send email"""
        creds = await get_google_credentials(self.user, self.db)
        gmail = GmailService(creds)
        
        to = input_data["to"]
        subject = input_data["subject"]
        body = input_data["body"]
        thread_id = input_data.get("thread_id")
        
        result = await gmail.send_email(
            to=to,
            subject=subject,
            body=body,
            thread_id=thread_id
        )
        
        return {
            "success": True,
            "result": {
                "message": f"Email sent to {', '.join(to)}",
                "message_id": result.get("id")
            }
        }
    
    # CALENDAR TOOLS
    async def _check_availability(self, input_data: Dict) -> Dict:
        """Check calendar availability"""
        creds = await get_google_credentials(self.user, self.db)
        calendar = CalendarService(creds)
        
        start_date_str = input_data["start_date"]
        days_ahead = input_data.get("days_ahead", 7)
        duration_minutes = input_data.get("duration_minutes", 60)
        
        start_date = datetime.fromisoformat(start_date_str)
        end_date = start_date + timedelta(days=days_ahead)
        
        free_slots = await calendar.get_free_slots(
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration_minutes
        )
        
        return {
            "success": True,
            "result": {
                "free_slots": free_slots[:10],
                "total_slots": len(free_slots)
            }
        }
    
    async def _create_calendar_event(self, input_data: Dict) -> Dict:
        """Create calendar event"""
        creds = await get_google_credentials(self.user, self.db)
        calendar = CalendarService(creds)
        
        summary = input_data["summary"]
        start_time = datetime.fromisoformat(input_data["start_time"])
        end_time = datetime.fromisoformat(input_data["end_time"])
        attendees = input_data.get("attendees", [])
        description = input_data.get("description")
        
        event = await calendar.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            description=description
        )
        
        return {
            "success": True,
            "result": {
                "message": f"Event '{summary}' created",
                "event_id": event.get("event_id"),
                "meeting_link": event.get("meeting_link")
            }
        }
    
    async def _search_calendar_events(self, input_data: Dict) -> Dict:
        """Search calendar events"""
        creds = await get_google_credentials(self.user, self.db)
        calendar = CalendarService(creds)
        
        query = input_data["query"]
        events = await calendar.search_events(query, max_results=10)
        
        formatted_events = []
        for event in events:
            formatted_events.append({
                "summary": event.get("summary"),
                "start_time": str(event.get("start_time")),
                "attendees": [a["email"] for a in event.get("attendees", [])]
            })
        
        return {
            "success": True,
            "result": {
                "events": formatted_events,
                "count": len(events)
            }
        }
    
    # HUBSPOT TOOLS
    async def _search_hubspot_contacts(self, input_data: Dict) -> Dict:
        """Search HubSpot contacts"""
        token = await get_hubspot_token(self.user, self.db)
        hubspot = HubSpotService(token)
        
        query = input_data["query"]
        
        if "@" in query:
            contact = await hubspot.get_contact_by_email(query)
            contacts = [contact] if contact else []
        else:
            contacts = await hubspot.search_contacts(query)
        
        formatted_contacts = []
        for contact in contacts:
            formatted_contacts.append({
                "id": contact.get("hubspot_id"),
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "email": contact.get("email"),
                "company": contact.get("company")
            })
        
        return {
            "success": True,
            "result": {
                "contacts": formatted_contacts,
                "count": len(contacts)
            }
        }
    
    async def _create_hubspot_contact(self, input_data: Dict) -> Dict:
        """Create HubSpot contact"""
        token = await get_hubspot_token(self.user, self.db)
        hubspot = HubSpotService(token)
        
        contact = await hubspot.create_contact(
            email=input_data["email"],
            first_name=input_data.get("first_name"),
            last_name=input_data.get("last_name"),
            phone=input_data.get("phone"),
            company=input_data.get("company")
        )
        
        return {
            "success": True,
            "result": {
                "message": f"Contact created: {contact.get('email')}",
                "contact_id": contact.get("hubspot_id")
            }
        }
    
    async def _add_hubspot_note(self, input_data: Dict) -> Dict:
        """Add HubSpot note"""
        token = await get_hubspot_token(self.user, self.db)
        hubspot = HubSpotService(token)
        
        contact_id = input_data["contact_id"]
        note_body = input_data["note_body"]
        
        note = await hubspot.create_note(contact_id, note_body)
        
        return {
            "success": True,
            "result": {
                "message": "Note added to contact",
                "note_id": note.get("hubspot_id")
            }
        }
    
    # TASK MANAGEMENT
    async def _create_task(self, input_data: Dict) -> Dict:
        """Create task for tracking"""
        task = Task(
            user_id=self.user.id,
            description=input_data["description"],
            status=TaskStatus.PENDING,
            memory=input_data.get("context", {})
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return {
            "success": True,
            "result": {
                "message": "Task created",
                "task_id": task.id
            }
        }
    
    async def _update_task(self, input_data: Dict) -> Dict:
        """Update task"""
        task_id = input_data["task_id"]
        status = input_data["status"]
        memory = input_data.get("memory")
        
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == self.user.id
        ).first()
        
        if not task:
            return {
                "success": False,
                "error": "Task not found"
            }
        
        task.status = TaskStatus[status.upper()]
        if memory:
            task.memory = memory
        
        if status == "completed":
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "success": True,
            "result": {
                "message": f"Task {task_id} updated to {status}"
            }
        }
    
    # INSTRUCTION MANAGEMENT
    async def _save_instruction(self, input_data: Dict) -> Dict:
        """Save ongoing instruction"""
        instruction = Instruction(
            user_id=self.user.id,
            instruction=input_data["instruction"],
            trigger_type=input_data["trigger_type"],
            is_active=True
        )
        
        self.db.add(instruction)
        self.db.commit()
        self.db.refresh(instruction)
        
        return {
            "success": True,
            "result": {
                "message": "Instruction saved",
                "instruction_id": instruction.id
            }
        }