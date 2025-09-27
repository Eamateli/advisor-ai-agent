from typing import List, Dict, Optional, AsyncGenerator
import anthropic
from anthropic.types import MessageStreamEvent
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class ClaudeService:
    """Claude AI integration with streaming and tool calling"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 4096
    
    async def chat_stream(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream chat responses from Claude
        
        Yields events like:
        - {"type": "content", "text": "..."}
        - {"type": "tool_use", "tool": {...}}
        - {"type": "done"}
        """
        try:
            # Prepare messages (convert to Anthropic format)
            formatted_messages = self._format_messages(messages)
            
            # Create stream
            stream_kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": formatted_messages,
                "system": system_prompt,
                "temperature": temperature,
            }
            
            if tools:
                stream_kwargs["tools"] = tools
            
            # Stream response
            async with self.client.messages.stream(**stream_kwargs) as stream:
                async for event in stream:
                    # Parse different event types
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "text":
                            yield {"type": "content_start"}
                        elif block.type == "tool_use":
                            yield {
                                "type": "tool_use_start",
                                "tool_use_id": block.id,
                                "tool_name": block.name
                            }
                    
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield {
                                "type": "content",
                                "text": delta.text
                            }
                        elif delta.type == "input_json_delta":
                            yield {
                                "type": "tool_input",
                                "partial_json": delta.partial_json
                            }
                    
                    elif event.type == "content_block_stop":
                        yield {"type": "content_block_stop"}
                    
                    elif event.type == "message_stop":
                        # Get final message
                        final_message = await stream.get_final_message()
                        
                        # Extract tool uses
                        tool_uses = []
                        for block in final_message.content:
                            if block.type == "tool_use":
                                tool_uses.append({
                                    "id": block.id,
                                    "name": block.name,
                                    "input": block.input
                                })
                        
                        yield {
                            "type": "done",
                            "stop_reason": final_message.stop_reason,
                            "tool_uses": tool_uses
                        }
            
        except Exception as e:
            logger.error(f"Error in Claude stream: {e}")
            yield {"type": "error", "error": str(e)}
    
    async def chat(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """Non-streaming chat (for background tasks)"""
        try:
            formatted_messages = self._format_messages(messages)
            
            response_kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": formatted_messages,
                "system": system_prompt,
                "temperature": temperature,
            }
            
            if tools:
                response_kwargs["tools"] = tools
            
            response = self.client.messages.create(**response_kwargs)
            
            # Extract text and tool uses
            text_content = ""
            tool_uses = []
            
            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_uses.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            return {
                "text": text_content,
                "tool_uses": tool_uses,
                "stop_reason": response.stop_reason
            }
        
        except Exception as e:
            logger.error(f"Error in Claude chat: {e}")
            raise
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Format messages for Claude API"""
        formatted = []
        
        for msg in messages:
            role = msg.get("role")
            
            # Handle different content formats
            if "content" in msg:
                content = msg["content"]
                
                # If content is a string, keep it simple
                if isinstance(content, str):
                    formatted.append({
                        "role": role,
                        "content": content
                    })
                # If content is already list format (with tool results), use as-is
                elif isinstance(content, list):
                    formatted.append({
                        "role": role,
                        "content": content
                    })
            
            # Handle tool results
            elif "tool_results" in msg:
                formatted.append({
                    "role": "user",
                    "content": msg["tool_results"]
                })
        
        return formatted
    
    def create_tool_result_message(
        self,
        tool_use_id: str,
        result: Dict
    ) -> Dict:
        """Create a tool result message for Claude"""
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result)
                }
            ]
        }

claude_service = ClaudeService()