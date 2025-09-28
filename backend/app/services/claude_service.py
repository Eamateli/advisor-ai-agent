from typing import List, Dict, Optional, AsyncGenerator
import anthropic
from app.core.config import settings
import logging
import json
import re

logger = logging.getLogger(__name__)

class ClaudeService:
    """Claude AI integration with simulated tool calling through prompting"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 4096
    
    async def chat_stream(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[Dict, None]:
        """Stream chat responses from Claude with simulated tool support"""
        try:
            formatted_messages = self._format_messages(messages)
            
            # If tools are provided, add them to the system prompt
            if tools:
                tools_prompt = self._create_tools_prompt(tools)
                enhanced_system = f"{system_prompt}\n\n{tools_prompt}"
            else:
                enhanced_system = system_prompt
            
            # Stream the response
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=formatted_messages,
                system=enhanced_system,
                temperature=temperature
            ) as stream:
                full_response = ""
                for event in stream:
                    if event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            text = event.delta.text
                            full_response += text
                            yield {"type": "content", "text": text}
                    elif event.type == 'message_stop':
                        # Parse for tool calls in the response
                        tool_uses = self._extract_tool_calls(full_response)
                        yield {
                            "type": "done",
                            "stop_reason": "end_turn",
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
        """Non-streaming chat with simulated tool support"""
        try:
            formatted_messages = self._format_messages(messages)
            
            # If tools are provided, add them to the system prompt
            if tools:
                tools_prompt = self._create_tools_prompt(tools)
                enhanced_system = f"{system_prompt}\n\n{tools_prompt}"
            else:
                enhanced_system = system_prompt
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=formatted_messages,
                system=enhanced_system,
                temperature=temperature
            )
            
            text_content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    text_content += block.text
            
            # Parse for tool calls
            tool_uses = self._extract_tool_calls(text_content)
            
            return {
                "text": text_content,
                "tool_uses": tool_uses,
                "stop_reason": response.stop_reason if hasattr(response, 'stop_reason') else None
            }
        
        except Exception as e:
            logger.error(f"Error in Claude chat: {e}")
            raise
    
    def _create_tools_prompt(self, tools: List[Dict]) -> str:
        """Create a prompt that instructs Claude to use tools"""
        tools_desc = "You have access to the following tools:\n\n"
        
        for tool in tools:
            tools_desc += f"Tool: {tool['name']}\n"
            tools_desc += f"Description: {tool['description']}\n"
            tools_desc += f"Parameters: {json.dumps(tool.get('input_schema', {}).get('properties', {}), indent=2)}\n\n"
        
        tools_desc += """
When you need to use a tool, respond with:
<tool_use>
{"name": "tool_name", "input": {parameters}}
</tool_use>

Then continue with your response or wait for the tool result.
"""
        return tools_desc
    
    def _extract_tool_calls(self, text: str) -> List[Dict]:
        """Extract tool calls from the response text"""
        tool_uses = []
        
        # Find all tool_use blocks
        pattern = r'<tool_use>\s*(.*?)\s*</tool_use>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                tool_data = json.loads(match)
                tool_uses.append({
                    "id": f"tool_{len(tool_uses)}",
                    "name": tool_data.get("name"),
                    "input": tool_data.get("input", {})
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool use: {match}")
        
        return tool_uses
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Format messages for Claude API"""
        formatted = []
        
        for msg in messages:
            role = msg.get("role")
            
            # Skip system messages (they go in the system parameter)
            if role == "system":
                continue
            
            if "content" in msg:
                content = msg["content"]
                
                # Handle string content
                if isinstance(content, str):
                    formatted.append({
                        "role": role,
                        "content": content
                    })
                # Handle list content (tool results, etc.)
                elif isinstance(content, list):
                    # Convert to string representation for now
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            elif item.get("type") == "tool_result":
                                text_parts.append(f"Tool result: {item.get('content', '')}")
                    
                    if text_parts:
                        formatted.append({
                            "role": role,
                            "content": "\n".join(text_parts)
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
            "content": f"Tool result for {tool_use_id}: {json.dumps(result)}"
        }

claude_service = ClaudeService()