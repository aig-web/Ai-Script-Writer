"""
Script Chat Agent - Handles per-script chat for editing/rewriting
Uses Claude to either edit specific parts or rewrite entire script based on user request
"""
import os
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class ScriptChatAgent:
    """
    Handles chat interactions for script editing.
    Claude decides whether to edit specific parts or rewrite the whole script.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="anthropic/claude-sonnet-4",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=4000
        )

    def _get_system_prompt(self) -> str:
        """System prompt for script editing chat"""
        return """You are an expert viral Instagram Reels scriptwriter and editor.

You're helping the user refine their script through chat.

**CRITICAL OUTPUT FORMAT:**
You MUST structure your response in exactly TWO parts:

1. **CHAT MESSAGE** (1-2 sentences max): A brief, conversational response explaining what you did.
2. **UPDATED SCRIPT**: The complete updated script wrapped in markers.

Example format:
---
I've made the hook more shocking and added specific numbers for credibility.

<UPDATED_SCRIPT>
[Your complete updated script here with all hooks and content]
</UPDATED_SCRIPT>
---

**RULES:**
- The chat message should be SHORT (1-2 sentences only)
- Always include <UPDATED_SCRIPT> tags even if script unchanged
- The script inside tags must be COMPLETE (all 5 hooks + full script)
- Keep scripts 150-200 words
- Use short, punchy sentences (8-12 words)
- Include pattern interrupts ("But here's where it gets interesting...")
- End with engagement question + value-based CTA
- No banned words in caps (DESTROYED, PANICKING, etc.)
- No bullet points in the spoken script

If user asks a question without requesting edits, still include <UPDATED_SCRIPT> tags with the unchanged script."""

    async def chat(
        self,
        user_message: str,
        current_script: str,
        chat_history: List[Dict] = None,
        angle_info: Dict = None
    ) -> str:
        """
        Process a chat message and return the response.

        Args:
            user_message: The user's request
            current_script: The current version of the script
            chat_history: Previous messages in this chat
            angle_info: Optional angle details (name, focus, hook_style)

        Returns:
            The assistant's response (explanation + updated script)
        """
        # Build context
        context_parts = []

        if angle_info:
            context_parts.append(f"**SCRIPT ANGLE:** {angle_info.get('name', 'Unknown')}")
            if angle_info.get('focus'):
                context_parts.append(f"**FOCUS:** {angle_info.get('focus')}")

        context_parts.append(f"\n**CURRENT SCRIPT:**\n{current_script}")

        context = "\n".join(context_parts)

        # Build messages
        messages = [
            SystemMessage(content=self._get_system_prompt())
        ]

        # Add chat history if exists
        if chat_history:
            for msg in chat_history[-6:]:  # Last 6 messages for context
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(SystemMessage(content=f"[Previous response]: {msg['content'][:500]}..."))

        # Add current context and user message
        full_user_message = f"{context}\n\n**USER REQUEST:**\n{user_message}"
        messages.append(HumanMessage(content=full_user_message))

        # Get response
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            print(f"[ScriptChat] Error: {e}")
            return f"Sorry, I encountered an error processing your request. Please try again.\n\nError: {str(e)}"

    def extract_updated_script(self, response: str, original_script: str) -> str:
        """
        Extract the updated script from the response.
        Looks for <UPDATED_SCRIPT> tags first, then falls back to other markers.
        """
        # First, try to extract from <UPDATED_SCRIPT> tags (preferred format)
        if "<UPDATED_SCRIPT>" in response and "</UPDATED_SCRIPT>" in response:
            start = response.find("<UPDATED_SCRIPT>") + len("<UPDATED_SCRIPT>")
            end = response.find("</UPDATED_SCRIPT>")
            if start < end:
                return response[start:end].strip()

        # Fallback: Check for common script markers
        markers = [
            "**FULL SCRIPT:**",
            "**SCRIPT:**",
            "**UPDATED SCRIPT:**",
            "**REVISED SCRIPT:**",
            "**CORRECTED SCRIPT:**",
            "### SCRIPT",
            "## SCRIPT",
        ]

        response_lower = response.lower()

        for marker in markers:
            if marker.lower() in response_lower:
                idx = response_lower.find(marker.lower())
                if idx != -1:
                    script_section = response[idx + len(marker):]
                    # Try to find end markers
                    end_markers = ["---", "**END**", "\n\n---"]
                    for end in end_markers:
                        if end in script_section:
                            end_idx = script_section.find(end)
                            return script_section[:end_idx].strip()
                    return script_section.strip()

        # If response contains "Hook 1:" it's likely the full script
        if "Hook 1:" in response or "HOOK OPTIONS:" in response.upper():
            # Try to extract just the script part
            if "Hook 1:" in response:
                idx = response.find("Hook 1:")
                return response[idx:].strip()
            return response

        # Return original if we can't extract
        return original_script

    def extract_chat_message(self, response: str) -> str:
        """
        Extract just the chat message part (before the script).
        Returns a short, clean message for the chat UI.
        """
        # If using <UPDATED_SCRIPT> tags, get everything before
        if "<UPDATED_SCRIPT>" in response:
            chat_part = response.split("<UPDATED_SCRIPT>")[0].strip()
            # Remove any trailing markers
            chat_part = chat_part.rstrip("-").strip()
            if chat_part:
                return chat_part

        # Fallback: Look for script markers and get text before
        markers = ["**FULL SCRIPT:**", "**SCRIPT:**", "**UPDATED SCRIPT:**",
                   "**REVISED SCRIPT:**", "**CORRECTED SCRIPT:**", "Hook 1:"]

        for marker in markers:
            if marker in response:
                chat_part = response.split(marker)[0].strip()
                chat_part = chat_part.rstrip("-").strip()
                if chat_part and len(chat_part) > 10:
                    return chat_part

        # If no clear separation, return first 200 chars as summary
        if len(response) > 200:
            # Find a sentence break
            for end_char in [". ", "! ", "? "]:
                if end_char in response[:250]:
                    idx = response[:250].rfind(end_char)
                    return response[:idx+1].strip()
            return response[:200].strip() + "..."

        return response


# Singleton instance
script_chat_agent = ScriptChatAgent()
