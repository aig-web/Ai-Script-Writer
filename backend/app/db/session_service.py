"""
Session Service - Manages session persistence with Supabase
Handles sessions, scripts, files, and chat messages
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client
from app.utils.logger import get_logger

# Initialize logger
log = get_logger("SessionDB", "💾")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        log.success("Supabase client initialized", {"url": SUPABASE_URL[:30] + "..."})
    except Exception as e:
        log.error(f"Supabase init failed: {str(e)}")
else:
    log.warn("Supabase not configured - session persistence disabled")


class SessionService:
    """Manages session data in Supabase"""

    @staticmethod
    def create_session(
        topic: str,
        mode: str,
        user_notes: str = "",
        research_data: str = "",
        research_sources: List[Dict] = None,
        topic_type: str = "A",
        skip_research: bool = False
    ) -> Optional[Dict]:
        """Create a new session and return its data"""
        if not supabase:
            log.warn("Supabase not configured - cannot create session")
            return None

        log.db_query("INSERT", "sessions", {"topic": topic[:30], "mode": mode})

        try:
            data = {
                "topic": topic,
                "mode": mode,
                "user_notes": user_notes,
                "research_data": research_data,
                "research_sources": research_sources or [],
                "topic_type": topic_type,
                "skip_research": skip_research
            }
            result = supabase.table("sessions").insert(data).execute()
            if result.data:
                session_id = result.data[0]['id']
                log.db_result("INSERT", "sessions")
                log.success(f"Session created: {session_id[:8]}")
                return result.data[0]
            log.warn("Session insert returned no data")
            return None
        except Exception as e:
            log.error(f"Create session failed: {str(e)}")
            return None

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Get a session by ID with all related data"""
        if not supabase:
            return None

        log.db_query("SELECT", "sessions", {"id": session_id[:8]})

        try:
            # Get session
            result = supabase.table("sessions").select("*").eq("id", session_id).execute()
            if not result.data:
                log.warn(f"Session not found: {session_id[:8]}")
                return None

            session = result.data[0]
            log.debug(f"Session found: {session_id[:8]}")

            # Get files
            log.db_query("SELECT", "session_files", {"session_id": session_id[:8]})
            files_result = supabase.table("session_files").select("*").eq("session_id", session_id).execute()
            session["files"] = files_result.data or []
            log.debug(f"Files loaded: {len(session['files'])}")

            # Get scripts
            log.db_query("SELECT", "session_scripts", {"session_id": session_id[:8]})
            scripts_result = supabase.table("session_scripts").select("*").eq("session_id", session_id).order("script_number").execute()
            session["scripts"] = scripts_result.data or []
            log.debug(f"Scripts loaded: {len(session['scripts'])}")

            # Get chat messages for all scripts
            log.db_query("SELECT", "chat_messages", {"session_id": session_id[:8]})
            chat_result = supabase.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            # Group by script_number
            chat_by_script = {1: [], 2: [], 3: []}
            for msg in (chat_result.data or []):
                script_num = msg.get("script_number", 1)
                if script_num in chat_by_script:
                    chat_by_script[script_num].append(msg)
            session["chat_history"] = chat_by_script
            total_messages = sum(len(msgs) for msgs in chat_by_script.values())
            log.debug(f"Chat messages loaded: {total_messages}")

            log.success(f"Session loaded: {session_id[:8]}", {
                "files": len(session["files"]),
                "scripts": len(session["scripts"]),
                "messages": total_messages
            })
            return session
        except Exception as e:
            log.error(f"Get session failed: {str(e)}")
            return None

    @staticmethod
    def list_sessions(limit: int = 50) -> List[Dict]:
        """List all sessions, most recent first"""
        if not supabase:
            return []

        log.db_query("SELECT", "sessions", {"limit": limit})

        try:
            result = supabase.table("sessions").select("id, topic, mode, created_at, updated_at").order("created_at", desc=True).limit(limit).execute()
            sessions = result.data or []
            log.db_result("SELECT", "sessions", len(sessions))
            return sessions
        except Exception as e:
            log.error(f"List sessions failed: {str(e)}")
            return []

    @staticmethod
    def update_session(session_id: str, updates: Dict) -> bool:
        """Update session fields"""
        if not supabase:
            return False

        log.db_query("UPDATE", "sessions", {"id": session_id[:8], "fields": list(updates.keys())})

        try:
            supabase.table("sessions").update(updates).eq("id", session_id).execute()
            log.db_result("UPDATE", "sessions")
            return True
        except Exception as e:
            log.error(f"Update session failed: {str(e)}")
            return False

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a session and all related data (cascades)"""
        if not supabase:
            return False

        log.db_query("DELETE", "sessions", {"id": session_id[:8]})

        try:
            supabase.table("sessions").delete().eq("id", session_id).execute()
            log.db_result("DELETE", "sessions")
            log.success(f"Session deleted: {session_id[:8]}")
            return True
        except Exception as e:
            log.error(f"Delete session failed: {str(e)}")
            return False

    @staticmethod
    def add_file(
        session_id: str,
        file_name: str,
        file_type: str,
        file_content: str,
        file_size: int = 0
    ) -> Optional[Dict]:
        """Add a file to a session"""
        if not supabase:
            return None

        log.db_query("INSERT", "session_files", {"session_id": session_id[:8], "file_name": file_name})

        try:
            data = {
                "session_id": session_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_content": file_content,
                "file_size": file_size
            }
            result = supabase.table("session_files").insert(data).execute()
            if result.data:
                log.db_result("INSERT", "session_files")
                log.success(f"File added: {file_name}")
                return result.data[0]
            return None
        except Exception as e:
            log.error(f"Add file failed: {str(e)}")
            return None

    @staticmethod
    def save_script(
        session_id: str,
        script_number: int,
        script_content: str,
        angle_name: str = "",
        angle_focus: str = "",
        angle_hook_style: str = ""
    ) -> Optional[Dict]:
        """Save or update a script for a session"""
        if not supabase:
            return None

        log.db_query("UPSERT", "session_scripts", {
            "session_id": session_id[:8],
            "script_number": script_number,
            "angle": angle_name[:20] if angle_name else "none"
        })

        try:
            data = {
                "session_id": session_id,
                "script_number": script_number,
                "script_content": script_content,
                "angle_name": angle_name,
                "angle_focus": angle_focus,
                "angle_hook_style": angle_hook_style
            }
            # Upsert to handle both insert and update
            result = supabase.table("session_scripts").upsert(
                data,
                on_conflict="session_id,script_number"
            ).execute()
            if result.data:
                log.db_result("UPSERT", "session_scripts")
                log.success(f"Script {script_number} saved ({len(script_content)} chars)")
                return result.data[0]
            return None
        except Exception as e:
            log.error(f"Save script failed: {str(e)}")
            return None

    @staticmethod
    def update_script(session_id: str, script_number: int, script_content: str) -> bool:
        """Update just the script content"""
        if not supabase:
            return False

        log.db_query("UPDATE", "session_scripts", {
            "session_id": session_id[:8],
            "script_number": script_number,
            "content_len": len(script_content)
        })

        try:
            supabase.table("session_scripts").update({
                "script_content": script_content
            }).eq("session_id", session_id).eq("script_number", script_number).execute()
            log.db_result("UPDATE", "session_scripts")
            return True
        except Exception as e:
            log.error(f"Update script failed: {str(e)}")
            return False

    @staticmethod
    def add_chat_message(
        session_id: str,
        script_number: int,
        role: str,
        content: str
    ) -> Optional[Dict]:
        """Add a chat message for a specific script"""
        if not supabase:
            return None

        log.db_query("INSERT", "chat_messages", {
            "session_id": session_id[:8],
            "script_number": script_number,
            "role": role,
            "content_len": len(content)
        })

        try:
            data = {
                "session_id": session_id,
                "script_number": script_number,
                "role": role,
                "content": content
            }
            result = supabase.table("chat_messages").insert(data).execute()
            if result.data:
                log.db_result("INSERT", "chat_messages")
                return result.data[0]
            return None
        except Exception as e:
            log.error(f"Add chat message failed: {str(e)}")
            return None

    @staticmethod
    def get_chat_history(session_id: str, script_number: int) -> List[Dict]:
        """Get chat history for a specific script"""
        if not supabase:
            return []

        log.db_query("SELECT", "chat_messages", {
            "session_id": session_id[:8],
            "script_number": script_number
        })

        try:
            result = supabase.table("chat_messages").select("*").eq("session_id", session_id).eq("script_number", script_number).order("created_at").execute()
            messages = result.data or []
            log.db_result("SELECT", "chat_messages", len(messages))
            return messages
        except Exception as e:
            log.error(f"Get chat history failed: {str(e)}")
            return []

    @staticmethod
    def find_session_by_topic(topic: str) -> Optional[Dict]:
        """Find the most recent session with matching topic"""
        if not supabase:
            return None

        log.db_query("SELECT", "sessions", {"topic": topic[:30]})

        try:
            result = supabase.table("sessions").select("*").eq("topic", topic).order("created_at", desc=True).limit(1).execute()
            if result.data:
                log.info(f"Found session for topic: {topic[:30]}")
                return SessionService.get_session(result.data[0]["id"])
            log.debug(f"No session found for topic: {topic[:30]}")
            return None
        except Exception as e:
            log.error(f"Find by topic failed: {str(e)}")
            return None


# Singleton instance
session_service = SessionService()
