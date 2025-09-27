"""
Tool definitions for the AI Agent

Each tool is defined in Anthropic's format with:
- name
- description
- input_schema (JSON schema)
"""

AGENT_TOOLS = [
    # RAG SEARCH TOOL
    {
        "name": "search_knowledge_base",
        "description": "Search through emails, HubSpot contacts, and notes to find relevant information. Use this to answer questions about clients, past conversations, or any stored data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific about what you're looking for."
                },
                "doc_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["email", "hubspot_contact", "hubspot_note"]
                    },
                    "description": "Optional filter by document type"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    
    # EMAIL TOOLS
    {
        "name": "search_emails",
        "description": "Search for specific emails by sender, subject, or date. Use this when you need to find particular email threads or check if someone has emailed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_email": {
                    "type": "string",
                    "description": "Search emails from this sender"
                },
                "subject_contains": {
                    "type": "string",
                    "description": "Search for emails with this text in subject"
                },
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to search (default 30)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "send_email",
        "description": "Send an email to one or more recipients. Use this to reach out to clients, send information, or reply to inquiries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recipient email addresses"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "thread_id": {
                    "type": "string",
                    "description": "Optional: Gmail thread ID to reply in thread"
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    
    # CALENDAR TOOLS
    {
        "name": "check_availability",
        "description": "Check calendar availability and find free time slots. Use this before scheduling meetings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)"
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to check (default 7)",
                    "default": 7
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Meeting duration in minutes (default 60)",
                    "default": 60
                }
            },
            "required": ["start_date"]
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new calendar event. Use this after confirming a meeting time with someone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Event title/summary"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in ISO format"
                },
                "end_time": {
                    "type": "string",
                    "description": "End time in ISO format"
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee emails"
                },
                "description": {
                    "type": "string",
                    "description": "Event description"
                }
            },
            "required": ["summary", "start_time", "end_time"]
        }
    },
    {
        "name": "search_calendar_events",
        "description": "Search for calendar events by keyword or attendee. Use this to find when meetings are scheduled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (event title, attendee name, etc.)"
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "How many days ahead to search (default 30)",
                    "default": 30
                }
            },
            "required": ["query"]
        }
    },
    
    # HUBSPOT TOOLS
    {
        "name": "search_hubspot_contacts",
        "description": "Search for contacts in HubSpot by email or name. Use this to find client information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Email address or name to search for"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_hubspot_contact",
        "description": "Create a new contact in HubSpot. Use this when someone new reaches out and isn't already in the system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Contact email address"
                },
                "first_name": {
                    "type": "string",
                    "description": "First name"
                },
                "last_name": {
                    "type": "string",
                    "description": "Last name"
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number"
                },
                "company": {
                    "type": "string",
                    "description": "Company name"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "add_hubspot_note",
        "description": "Add a note to a HubSpot contact. Use this to document interactions, decisions, or important information about a client.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "HubSpot contact ID"
                },
                "note_body": {
                    "type": "string",
                    "description": "Note content"
                }
            },
            "required": ["contact_id", "note_body"]
        }
    },
    
    # TASK MANAGEMENT
    {
        "name": "create_task",
        "description": "Create a task for tracking multi-step operations. Use this when you need to remember something for later or wait for a response.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "context": {
                    "type": "object",
                    "description": "Any context needed to complete the task later"
                }
            },
            "required": ["description"]
        }
    },
    {
        "name": "update_task",
        "description": "Update a task's status or memory. Use this to track progress on ongoing operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "Task ID to update"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "waiting", "completed", "failed"],
                    "description": "New task status"
                },
                "memory": {
                    "type": "object",
                    "description": "Updated task memory/context"
                }
            },
            "required": ["task_id", "status"]
        }
    },
    
    # INSTRUCTION MANAGEMENT
    {
        "name": "save_instruction",
        "description": "Save an ongoing instruction or rule. Use this when the user gives you standing instructions like 'always do X when Y happens'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instruction": {
                    "type": "string",
                    "description": "The instruction to remember"
                },
                "trigger_type": {
                    "type": "string",
                    "enum": ["email", "calendar", "hubspot_contact", "hubspot_note", "always"],
                    "description": "What should trigger this instruction"
                }
            },
            "required": ["instruction", "trigger_type"]
        }
    }
]

def get_tool_by_name(name: str):
    """Get tool definition by name"""
    for tool in AGENT_TOOLS:
        if tool["name"] == name:
            return tool
    return None