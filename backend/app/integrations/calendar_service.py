from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import pytz

logger = logging.getLogger(__name__)

class CalendarService:
    """Google Calendar API integration"""
    
    def __init__(self, credentials: Credentials):
        self.service = build('calendar', 'v3', credentials=credentials)
        self.calendar_id = 'primary'  # User's primary calendar
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_free_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 60,
        timezone: str = 'America/Denver'
    ) -> List[Dict]:
        """
        Get available time slots in calendar
        
        Args:
            start_date: Start of search window
            end_date: End of search window
            duration_minutes: Desired meeting duration
            timezone: Timezone for results
        """
        try:
            # Get busy times using freebusy API
            body = {
                "timeMin": start_date.isoformat() + 'Z',
                "timeMax": end_date.isoformat() + 'Z',
                "items": [{"id": self.calendar_id}],
                "timeZone": timezone
            }
            
            freebusy = self.service.freebusy().query(body=body).execute()
            busy_times = freebusy['calendars'][self.calendar_id].get('busy', [])
            
            # Convert busy times to datetime objects
            busy_periods = []
            for period in busy_times:
                start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                busy_periods.append({'start': start, 'end': end})
            
            # Generate free slots
            free_slots = self._find_free_slots(
                start_date,
                end_date,
                busy_periods,
                duration_minutes,
                timezone
            )
            
            logger.info(f"Found {len(free_slots)} free slots")
            return free_slots
        
        except Exception as e:
            logger.error(f"Error getting free slots: {e}")
            raise
    
    def _find_free_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        busy_periods: List[Dict],
        duration_minutes: int,
        timezone_str: str
    ) -> List[Dict]:
        """Find free slots between busy periods"""
        
        tz = pytz.timezone(timezone_str)
        duration = timedelta(minutes=duration_minutes)
        
        # Define working hours (9 AM to 5 PM)
        working_start_hour = 9
        working_end_hour = 17
        
        free_slots = []
        current = start_date
        
        while current < end_date:
            # Skip to next working day if needed
            if current.hour < working_start_hour:
                current = current.replace(hour=working_start_hour, minute=0, second=0)
            
            # Check if we're past working hours
            if current.hour >= working_end_hour:
                # Move to next day
                current = (current + timedelta(days=1)).replace(
                    hour=working_start_hour, 
                    minute=0, 
                    second=0
                )
                continue
            
            # Skip weekends
            if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
                days_to_monday = 7 - current.weekday()
                current = (current + timedelta(days=days_to_monday)).replace(
                    hour=working_start_hour,
                    minute=0,
                    second=0
                )
                continue
            
            slot_end = current + duration
            
            # Check if slot is within working hours
            if slot_end.hour > working_end_hour or (
                slot_end.hour == working_end_hour and slot_end.minute > 0
            ):
                # Move to next day
                current = (current + timedelta(days=1)).replace(
                    hour=working_start_hour,
                    minute=0,
                    second=0
                )
                continue
            
            # Check if slot conflicts with busy period
            is_free = True
            for busy in busy_periods:
                if (current < busy['end'] and slot_end > busy['start']):
                    is_free = False
                    # Jump to end of busy period
                    current = busy['end']
                    break
            
            if is_free:
                free_slots.append({
                    'start': current.isoformat(),
                    'end': slot_end.isoformat(),
                    'start_formatted': current.strftime('%A, %B %d at %I:%M %p'),
                    'duration_minutes': duration_minutes
                })
                # Move to next slot (30 min intervals)
                current += timedelta(minutes=30)
            
        return free_slots
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = 'America/Denver'
    ) -> Dict:
        """
        Create calendar event
        
        Args:
            summary: Event title
            start_time: Event start
            end_time: Event end
            attendees: List of attendee emails
            description: Event description
            location: Event location
            timezone: Timezone for event
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
                # Send invites
                event['sendUpdates'] = 'all'
            
            # Add Google Meet link
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"meet-{start_time.timestamp()}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Created event: {created_event['id']}")
            return self._format_event(created_event)
        
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update existing calendar event"""
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if summary:
                event['summary'] = summary
            
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            
            if description:
                event['description'] = description
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Updated event: {event_id}")
            return self._format_event(updated_event)
        
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def delete_event(self, event_id: str):
        """Delete calendar event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Deleted event: {event_id}")
        
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_upcoming_events(
        self,
        max_results: int = 10,
        days_ahead: int = 7
    ) -> List[Dict]:
        """Get upcoming events"""
        try:
            now = datetime.utcnow()
            time_max = now + timedelta(days=days_ahead)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = [self._format_event(event) for event in events]
            
            logger.info(f"Retrieved {len(formatted_events)} upcoming events")
            return formatted_events
        
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_events(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict]:
        """Search events by text query"""
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            formatted_events = [self._format_event(event) for event in events]
            
            logger.info(f"Found {len(formatted_events)} events matching '{query}'")
            return formatted_events
        
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            raise
    
    def _format_event(self, event: Dict) -> Dict:
        """Format Calendar API event into clean structure"""
        
        # Parse start/end times
        start = event.get('start', {})
        end = event.get('end', {})
        
        start_time = None
        end_time = None
        is_all_day = False
        
        if 'dateTime' in start:
            start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
        elif 'date' in start:
            # All-day event
            start_time = datetime.fromisoformat(start['date'])
            end_time = datetime.fromisoformat(end['date'])
            is_all_day = True
        
        # Parse attendees
        attendees = []
        for attendee in event.get('attendees', []):
            attendees.append({
                'email': attendee.get('email'),
                'response_status': attendee.get('responseStatus'),
                'organizer': attendee.get('organizer', False)
            })
        
        # Get meeting link
        meeting_link = None
        if 'conferenceData' in event:
            entry_points = event['conferenceData'].get('entryPoints', [])
            for entry in entry_points:
                if entry.get('entryPointType') == 'video':
                    meeting_link = entry.get('uri')
                    break
        
        return {
            'event_id': event['id'],
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start_time': start_time,
            'end_time': end_time,
            'is_all_day': is_all_day,
            'attendees': attendees,
            'meeting_link': meeting_link,
            'status': event.get('status'),
            'html_link': event.get('htmlLink'),
            'created': datetime.fromisoformat(event['created'].replace('Z', '+00:00')),
            'updated': datetime.fromisoformat(event['updated'].replace('Z', '+00:00'))
        }