from typing import List, Dict, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
from app.models.user import User
from app.models.chat import ChatMessage, MessageRole
from app.models.task import Task, TaskStatus, Instruction
from app.services.claude_service import claude_service
from app.agents.tools import AGENT_TOOLS
from app.agents.tool_executor import ToolExecutor
from app.agents.prompts import build_full_system_prompt

logger = logging.getLogger(__name__)

class FinancialAdvisorAgent:
    """Main AI Agent orchestrator"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tool_executor = ToolExecutor(db, user)
    
    async def chat_stream(
        self,
        user_message: str,
        conversation_history: List[ChatMessage] = None,
        max_turns: int = 10
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream chat responses with tool calling loop
        
        This implements the agent reasoning loop:
        1. Get user message
        2. Claude responds (may include tool calls)
        3. Execute tools
        4. Give results back to Claude
        5. Repeat until Claude gives final answer
        """
        
        # Save user message
        user_msg = ChatMessage(
            user_id=self.user.id,
            role=MessageRole.USER,
            content=user_message
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        
        # Build system prompt with context
        ongoing_instructions = self._get_ongoing_instructions()
        active_tasks = self._get_active_tasks()
        
        system_prompt = build_full_system_prompt(
            user_name=self.user.full_name,
            ongoing_instructions=ongoing_instructions,
            active_tasks=active_tasks
        )
        
        # Build conversation messages
        messages = self._build_messages(conversation_history)
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Agent loop
        turn_count = 0
        assistant_response = ""
        tool_calls_made = []
        
        while turn_count < max_turns:
            turn_count += 1
            logger.info(f"Agent turn {turn_count}/{max_turns}")
            
            # Stream Claude's response
            tool_uses = []
            current_text = ""
            
            async for event in claude_service.chat_stream(
                messages=messages,
                system_prompt=system_prompt,
                tools=AGENT_TOOLS,
                temperature=0.7
            ):
                event_type = event.get("type")
                
                if event_type == "content":
                    # Stream text to user
                    text = event.get("text", "")
                    current_text += text
                    yield {
                        "type": "content",
                        "text": text
                    }
                
                elif event_type == "tool_use_start":
                    # Notify user of tool use
                    tool_name = event.get("tool_name")
                    yield {
                        "type": "tool_use_start",
                        "tool_name": tool_name
                    }
                
                elif event_type == "done":
                    tool_uses = event.get("tool_uses", [])
                    stop_reason = event.get("stop_reason")
                    
                    # If no tool uses, we're done
                    if not tool_uses or stop_reason == "end_turn":
                        assistant_response = current_text
                        
                        # Save assistant message
                        assistant_msg = ChatMessage(
                            user_id=self.user.id,
                            role=MessageRole.ASSISTANT,
                            content=assistant_response,
                            tool_calls=tool_calls_made if tool_calls_made else None
                        )
                        self.db.add(assistant_msg)
                        self.db.commit()
                        
                        yield {
                            "type": "done",
                            "message": assistant_response
                        }
                        return
            
            # Execute tools if any
            if not tool_uses:
                break
            
            logger.info(f"Executing {len(tool_uses)} tools")
            
            # Add Claude's response with tool uses to messages
            messages.append({
                "role": "assistant",
                "content": [
                    {"type": "text", "text": current_text}
                ] + [
                    {
                        "type": "tool_use",
                        "id": tu["id"],
                        "name": tu["name"],
                        "input": tu["input"]
                    }
                    for tu in tool_uses
                ]
            })
            
            # Execute each tool
            tool_results_content = []
            
            for tool_use in tool_uses:
                tool_name = tool_use["name"]
                tool_input = tool_use["input"]
                tool_use_id = tool_use["id"]
                
                # Execute tool
                result = await self.tool_executor.execute(tool_name, tool_input)
                
                # Track for saving
                tool_calls_made.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": result
                })
                
                # Add result to message
                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result)
                })
                
                # Stream tool result to user
                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "result": result
                }
            
            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results_content
            })
            
            # Continue loop - Claude will see tool results and respond
        
        # If we hit max turns, save what we have
        if assistant_response:
            assistant_msg = ChatMessage(
                user_id=self.user.id,
                role=MessageRole.ASSISTANT,
                content=assistant_response or "I've completed the requested actions.",
                tool_calls=tool_calls_made if tool_calls_made else None
            )
            self.db.add(assistant_msg)
            self.db.commit()
        
        yield {
            "type": "done",
            "message": assistant_response or "Task completed."
        }
    
    async def chat(self, user_message: str) -> str:
        """Non-streaming chat (for background tasks)"""
        
        ongoing_instructions = self._get_ongoing_instructions()
        active_tasks = self._get_active_tasks()
        
        system_prompt = build_full_system_prompt(
            user_name=self.user.full_name,
            ongoing_instructions=ongoing_instructions,
            active_tasks=active_tasks
        )
        
        messages = [{"role": "user", "content": user_message}]
        
        # Simple loop for non-streaming
        turn_count = 0
        max_turns = 10
        
        while turn_count < max_turns:
            turn_count += 1
            
            response = await claude_service.chat(
                messages=messages,
                system_prompt=system_prompt,
                tools=AGENT_TOOLS
            )
            
            text = response["text"]
            tool_uses = response["tool_uses"]
            
            if not tool_uses:
                return text
            
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": [
                    {"type": "text", "text": text}
                ] + [
                    {
                        "type": "tool_use",
                        "id": tu["id"],
                        "name": tu["name"],
                        "input": tu["input"]
                    }
                    for tu in tool_uses
                ]
            })
            
            # Execute tools
            tool_results_content = []
            
            for tool_use in tool_uses:
                result = await self.tool_executor.execute(
                    tool_use["name"],
                    tool_use["input"]
                )
                
                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use["id"],
                    "content": str(result)
                })
            
            # Add tool results
            messages.append({
                "role": "user",
                "content": tool_results_content
            })
        
        return "Task completed."
    
    async def proactive_check(self, event_type: str, event_data: Dict) -> bool:
        """
        Check if agent should proactively respond to an event
        
        Returns True if action was taken
        """
        from app.agents.prompts import PROACTIVE_SYSTEM_PROMPT
        
        # Get relevant instructions
        instructions = self.db.query(Instruction).filter(
            Instruction.user_id == self.user.id,
            Instruction.is_active == True,
            Instruction.trigger_type.in_([event_type, "always"])
        ).all()
        
        if not instructions:
            return False
        
        # Build prompt
        instructions_text = "\n".join([
            f"- {inst.instruction}" for inst in instructions
        ])
        
        system_prompt = PROACTIVE_SYSTEM_PROMPT.format(
            instructions=instructions_text,
            event_details=str(event_data)
        )
        
        # Ask Claude if it should act
        response = await claude_service.chat(
            messages=[{"role": "user", "content": "Should I take action?"}],
            system_prompt=system_prompt,
            tools=AGENT_TOOLS
        )
        
        # If Claude says no action, return
        if "NO_ACTION" in response["text"]:
            logger.info("Proactive check: No action needed")
            return False
        
        # Otherwise, execute tool calls
        logger.info("Proactive check: Taking action!")
        
        for tool_use in response["tool_uses"]:
            await self.tool_executor.execute(
                tool_use["name"],
                tool_use["input"]
            )
        
        # Save as system message
        system_msg = ChatMessage(
            user_id=self.user.id,
            role=MessageRole.SYSTEM,
            content=f"[Proactive] {response['text']}"
        )
        self.db.add(system_msg)
        self.db.commit()
        
        return True
    
    def _get_ongoing_instructions(self) -> List[Instruction]:
        """Get active ongoing instructions"""
        return self.db.query(Instruction).filter(
            Instruction.user_id == self.user.id,
            Instruction.is_active == True
        ).all()
    
    def _get_active_tasks(self) -> List[Task]:
        """Get active tasks"""
        return self.db.query(Task).filter(
            Task.user_id == self.user.id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING])
        ).all()
    
    def _build_messages(
        self,
        conversation_history: List[ChatMessage] = None
    ) -> List[Dict]:
        """Build message history for Claude"""
        
        if not conversation_history:
            # Get recent messages from database
            conversation_history = self.db.query(ChatMessage).filter(
                ChatMessage.user_id == self.user.id
            ).order_by(desc(ChatMessage.created_at)).limit(20).all()
            
            conversation_history = list(reversed(conversation_history))
        
        messages = []
        
        for msg in conversation_history:
            if msg.role == MessageRole.SYSTEM:
                continue  # Skip system messages
            
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        return messages

def create_agent(db: Session, user: User) -> FinancialAdvisorAgent:
    """Factory function to create agent"""
    return FinancialAdvisorAgent(db, user)