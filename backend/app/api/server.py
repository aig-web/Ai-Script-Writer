import os
import time
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env from backend directory (handles running from different directories)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import centralized logger
from app.utils.logger import server_log, session_log, chat_log

# Startup logging
server_log.info("=" * 50)
server_log.info("ScriptAI Pro Backend v2.0 Starting")
server_log.info(f"API Key: {'✓ Configured' if os.getenv('OPENAI_API_KEY') else '✗ Missing'}")
server_log.info(f"Supabase URL: {'✓ Configured' if os.getenv('SUPABASE_URL') else '✗ Missing'}")
server_log.info(f"Supabase Key: {'✓ Configured' if os.getenv('SUPABASE_KEY') else '✗ Missing'}")
server_log.info("=" * 50)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import PyPDF2
import io

from app.db.storage import collection, add_script_to_db
from app.db.session_service import session_service
from app.schemas.enums import ScriptMode, HookType
from app.utils.skeleton_utils import generate_skeleton, extract_hook
from app.agents.graph import app as agent_app
from app.agents.script_chat import script_chat_agent


server = FastAPI(title="ScriptAI Pro Backend")

# CORS - Allow localhost and Vercel deployments
allowed_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]

# Add Vercel domains dynamically from environment
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")
    server_log.info(f"CORS: Added Vercel URL {vercel_url}")

# Allow all vercel.app subdomains for preview deployments
server.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server_log.success("Server initialized successfully")


# -------- Data Models --------
class TrainRequest(BaseModel):
    title: str
    script_content: str
    mode: ScriptMode
    hook_type: HookType


# -------- Endpoints --------
@server.get("/")
@server.head("/")
def health_check():
    """Health check endpoint - supports GET and HEAD for uptime monitors"""
    count = collection.count()
    server_log.debug(f"Health check: {count} vectors stored")
    return {"status": "ok", "vectors_stored": count}


@server.post("/train_script")
def train_script(request: TrainRequest):
    """Train a new script into the vector database"""
    request_id = str(uuid.uuid4())[:8]
    server_log.start(f"Train script: {request.title}", {"mode": request.mode.value, "request_id": request_id})

    try:
        server_log.step("Generating skeleton")
        skeleton = generate_skeleton(request.script_content)

        server_log.step("Extracting hook")
        hook_text = extract_hook(request.script_content)

        server_log.step("Saving to vector DB")
        script_id = add_script_to_db(
            title=request.title,
            full_text=request.script_content,
            mode=request.mode,
            hook_type=request.hook_type,
            skeleton_text=skeleton,
            hook_text=hook_text,
        )

        server_log.success(f"Script trained: {script_id}", {"skeleton_len": len(skeleton)})

        return {
            "status": "success",
            "script_id": script_id,
            "meta_preview": {
                "skeleton": skeleton,
                "mode": request.mode.value,
            },
        }
    except Exception as e:
        server_log.error(f"Train failed: {str(e)}", exc=e)
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF file bytes"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        result = "\n\n".join(text_parts)
        server_log.debug(f"PDF extracted: {len(pdf_reader.pages)} pages, {len(result)} chars")
        return result
    except Exception as e:
        server_log.error(f"PDF extraction failed: {str(e)}")
        return f"[PDF extraction error: {str(e)}]"


@server.post("/generate_stream")
async def generate_stream(
    topic: str = Form(...),
    user_notes: str = Form(""),
    mode: ScriptMode = Form(...),
    files: List[UploadFile] = File(None),
    skip_research: bool = Form(False),
):
    """Generate viral scripts with streaming response"""
    request_id = str(uuid.uuid4())[:8]
    server_log.set_request_id(request_id)

    server_log.info("=" * 40)
    server_log.start("Script Generation", {
        "request_id": request_id,
        "topic": topic[:50] + "..." if len(topic) > 50 else topic,
        "mode": mode.value,
        "skip_research": skip_research,
        "files_count": len(files) if files else 0
    })

    # Read files BEFORE the generator (outside async generator)
    all_file_text = []
    if files:
        for file in files:
            if file and file.filename:
                server_log.step(f"Reading file: {file.filename}")
                content = await file.read()

                # Handle PDF files
                if file.filename.lower().endswith('.pdf'):
                    text = extract_text_from_pdf(content)
                    all_file_text.append(f"--- {file.filename} ---\n{text}")
                else:
                    # Text files (txt, md, etc.)
                    text = content.decode("utf-8", errors="ignore")
                    all_file_text.append(f"--- {file.filename} ---\n{text}")

    file_content = "\n\n".join(all_file_text) if all_file_text else ""
    if files and all_file_text:
        server_log.success(f"Files loaded: {len(all_file_text)} files, {len(file_content)} chars")

    async def event_generator():
        start_time = time.time()
        scripts_list = []
        angles_list = []
        summary_table = ""
        full_output = ""

        try:
            # Send file reading status if files were provided
            if all_file_text:
                yield json.dumps({"type": "status", "message": f"Loaded {len(all_file_text)} file(s)..."}) + "\n"

            # Init State
            initial_state = {
                "topic": topic,
                "mode": mode,
                "user_notes": user_notes,
                "file_content": file_content,
                "revision_count": 0,
                "skip_research": skip_research,
            }

            server_log.step("Initializing agent state")

            if skip_research:
                yield json.dumps({"type": "status", "message": f"Agent starting ({mode.value})..."}) + "\n"
            else:
                yield json.dumps({"type": "status", "message": "Stage 0: Detecting topic type..."}) + "\n"

            final_draft = ""
            checker_analysis = ""
            optimized_script = ""

            # Stream Graph Events
            server_log.step("Starting graph execution")
            async for step in agent_app.astream(initial_state):
                for node, output in step.items():
                    node_time = time.time() - start_time
                    server_log.debug(f"Node completed: {node} @ {node_time:.1f}s", {"output_keys": list(output.keys())})

                    if node == "researcher":
                        # Check research status first
                        research_status = output.get("research_status", "complete")
                        server_log.info(f"Research status: {research_status}")

                        # Handle generic topic (needs angle selection)
                        if research_status == "needs_specific_angle":
                            server_log.warn("Topic needs angle selection")
                            yield json.dumps({
                                "type": "needs_input",
                                "input_type": "angle_selection",
                                "message": output.get("research_message", "This topic is too generic. Please select a specific angle."),
                                "options": output.get("suggested_angles", []),
                                "topic_type": "B"
                            }) + "\n"
                            yield json.dumps({"type": "status", "message": "Waiting for angle selection..."}) + "\n"
                            return  # Stop here - frontend will re-submit with selected angle

                        # Handle ambiguous topic (needs clarification)
                        if research_status == "needs_clarification":
                            server_log.warn("Topic needs clarification")
                            yield json.dumps({
                                "type": "needs_input",
                                "input_type": "clarification",
                                "message": output.get("research_message", "This topic is too broad. Please clarify."),
                                "questions": output.get("clarification_questions", []),
                                "options": output.get("suggested_angles", []),
                                "topic_type": "D"
                            }) + "\n"
                            yield json.dumps({"type": "status", "message": "Waiting for clarification..."}) + "\n"
                            return  # Stop here - frontend will re-submit with clarification

                        # Normal flow - send research data
                        research_data = output.get("research_data", "")
                        if research_data:
                            server_log.success(f"Research data received: {len(research_data)} chars")
                            yield json.dumps({"type": "research", "data": research_data}) + "\n"

                        # Send sources if available
                        sources = output.get("research_sources", [])
                        if sources:
                            server_log.info(f"Research sources: {len(sources)}")
                            yield json.dumps({"type": "sources", "data": sources}) + "\n"

                        # Send quality score if available
                        quality_score = output.get("research_quality_score", 0)
                        topic_type = output.get("topic_type", "A")
                        selected_angle = output.get("selected_angle", {})
                        angle_name = selected_angle.get("angle", "")[:50] if selected_angle else ""

                        server_log.info(f"Research quality: {quality_score}/100, Topic type: {topic_type}")

                        # User-friendly status messages based on quality
                        if quality_score >= 80:
                            yield json.dumps({"type": "status", "message": "Research complete - excellent data found"}) + "\n"
                        elif quality_score >= 60:
                            yield json.dumps({"type": "status", "message": "Research complete - good data found"}) + "\n"
                        elif quality_score >= 40:
                            yield json.dumps({"type": "status", "message": "Research complete - basic data found"}) + "\n"
                        else:
                            yield json.dumps({"type": "status", "message": "Research complete"}) + "\n"

                    if node == "retriever":
                        server_log.info("Style retrieval completed")
                        yield json.dumps({"type": "status", "message": "Analyzing trained styles..."}) + "\n"

                    if node == "writer":
                        # Check if multi-angle mode
                        if output.get("angles"):
                            angles = output.get("angles", [])
                            server_log.success(f"Generated {len(angles)} angles")
                            for i, a in enumerate(angles):
                                server_log.debug(f"  Angle {i+1}: {a.get('name', 'Unknown')}")
                            yield json.dumps({
                                "type": "angles",
                                "data": [{"name": a.get("name", ""), "focus": a.get("focus", "")} for a in angles]
                            }) + "\n"
                            yield json.dumps({"type": "status", "message": f"Generated 3 scripts with different angles..."}) + "\n"
                        else:
                            server_log.info("Single script mode")
                            yield json.dumps({"type": "status", "message": "Claude is writing script..."}) + "\n"

                    if node == "critic":
                        feedback = output.get("critic_feedback", "")
                        server_log.info(f"Critic feedback: {feedback}")
                        if feedback == "PASS":
                            yield json.dumps({"type": "status", "message": "Script passed quality check!"}) + "\n"
                        else:
                            revision = output.get("revision_count", 1)
                            yield json.dumps({"type": "status", "message": f"Revision {revision}: Improving script..."}) + "\n"

                    if node == "checker":
                        server_log.info("Hook analysis completed")
                        yield json.dumps({"type": "status", "message": "Analyzing hooks & optimizing..."}) + "\n"
                        # Send checker analysis
                        if "checker_analysis" in output:
                            checker_analysis = output["checker_analysis"]
                            yield json.dumps({"type": "analysis", "data": checker_analysis}) + "\n"
                        # Send optimized script
                        if "optimized_script" in output:
                            optimized_script = output["optimized_script"]
                            server_log.debug(f"Optimized script: {len(optimized_script)} chars")
                        # Send hook ranking
                        if "hook_ranking" in output:
                            server_log.info(f"Best hook: #{output.get('best_hook_number', 1)}")
                            yield json.dumps({
                                "type": "hook_ranking",
                                "data": {
                                    "ranking": output["hook_ranking"],
                                    "best": output.get("best_hook_number", 1)
                                }
                            }) + "\n"

                    # Capture latest draft and multi-angle data
                    if "draft" in output:
                        final_draft = output["draft"]

                    # Capture multi-angle specific data
                    if "scripts" in output:
                        scripts_list = output["scripts"]
                        server_log.info(f"Scripts captured: {len(scripts_list)}")
                    if "angles" in output:
                        angles_list = output["angles"]
                    if "summary_table" in output:
                        summary_table = output["summary_table"]
                    if "full_output" in output:
                        full_output = output["full_output"]

            # Final Result
            total_time = time.time() - start_time
            server_log.info("=" * 40)
            server_log.success(f"Generation complete!", {
                "duration": f"{total_time:.1f}s",
                "scripts": len(scripts_list) if scripts_list else 1,
                "draft_chars": len(final_draft)
            })

            # Check if we have multi-angle output
            if scripts_list and len(scripts_list) > 1:
                server_log.info(f"Sending multi-angle result: {len(scripts_list)} scripts")
                yield json.dumps({
                    "type": "result",
                    "data": {
                        "scripts": scripts_list,
                        "angles": angles_list if angles_list else [],
                        "summary_table": summary_table if summary_table else "",
                        "full_output": full_output if full_output else final_draft,
                        "draft": final_draft,
                        "optimized": optimized_script if optimized_script else final_draft
                    }
                }) + "\n"
            else:
                server_log.info("Sending single script result")
                yield json.dumps({
                    "type": "result",
                    "data": {
                        "draft": final_draft,
                        "optimized": optimized_script if optimized_script else final_draft
                    }
                }) + "\n"

        except Exception as e:
            server_log.error(f"Generation failed: {str(e)}", exc=e)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# ============================================
# SESSION MANAGEMENT ENDPOINTS (Version 2.0)
# ============================================

class SessionCreate(BaseModel):
    topic: str
    mode: str = "informational"
    user_notes: str = ""
    research_data: str = ""
    research_sources: List[dict] = []
    topic_type: str = "A"
    skip_research: bool = False


class ScriptSave(BaseModel):
    session_id: str
    script_number: int
    script_content: str
    angle_name: str = ""
    angle_focus: str = ""
    angle_hook_style: str = ""


class ChatMessage(BaseModel):
    session_id: str
    script_number: int
    message: str


@server.post("/sessions")
async def create_session(request: SessionCreate):
    """Create a new session"""
    session_log.start("Create session", {"topic": request.topic[:30], "mode": request.mode})
    try:
        session = session_service.create_session(
            topic=request.topic,
            mode=request.mode,
            user_notes=request.user_notes,
            research_data=request.research_data,
            research_sources=request.research_sources,
            topic_type=request.topic_type,
            skip_research=request.skip_research
        )
        if not session:
            # Return a mock session ID so frontend can continue
            session_log.warn("Supabase not configured - returning local session")
            return {"id": "local-session", "topic": request.topic, "mode": request.mode}
        session_log.success(f"Session created: {session.get('id', 'unknown')[:8]}")
        return session
    except Exception as e:
        session_log.error(f"Create failed: {str(e)}", exc=e)
        return {"id": "local-session", "topic": request.topic, "mode": request.mode}


@server.get("/sessions")
async def list_sessions(limit: int = 50):
    """List all sessions (most recent first)"""
    session_log.debug(f"List sessions (limit={limit})")
    try:
        sessions = session_service.list_sessions(limit=limit)
        session_log.info(f"Found {len(sessions)} sessions")
        return {"sessions": sessions}
    except Exception as e:
        session_log.error(f"List failed: {str(e)}")
        return {"sessions": []}


@server.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a session with all related data (files, scripts, chat)"""
    session_log.debug(f"Get session: {session_id[:8] if len(session_id) > 8 else session_id}")
    try:
        if session_id == "local-session":
            session_log.info("Returning empty local session")
            return {"id": "local-session", "topic": "", "scripts": [], "chat_history": {}}
        session = session_service.get_session(session_id)
        if not session:
            session_log.warn(f"Session not found: {session_id[:8]}")
            raise HTTPException(status_code=404, detail="Session not found")
        session_log.success(f"Session loaded: {session_id[:8]}", {
            "scripts": len(session.get("scripts", [])),
            "files": len(session.get("files", []))
        })
        return session
    except HTTPException:
        raise
    except Exception as e:
        session_log.error(f"Get failed: {str(e)}")
        raise HTTPException(status_code=404, detail="Session not found")


@server.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all related data"""
    session_log.start(f"Delete session: {session_id[:8] if len(session_id) > 8 else session_id}")
    try:
        if session_id == "local-session":
            session_log.info("Local session - nothing to delete")
            return {"status": "deleted"}
        success = session_service.delete_session(session_id)
        if not success:
            session_log.warn(f"Session not found: {session_id[:8]}")
            return {"status": "not_found"}
        session_log.success(f"Session deleted: {session_id[:8]}")
        return {"status": "deleted"}
    except Exception as e:
        session_log.error(f"Delete failed: {str(e)}")
        return {"status": "error"}


@server.post("/sessions/{session_id}/files")
async def add_session_file(
    session_id: str,
    file: UploadFile = File(...)
):
    """Add a file to a session"""
    session_log.start(f"Add file to session", {"session": session_id[:8], "filename": file.filename})
    content = await file.read()

    # Handle PDF files
    if file.filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(content)
    else:
        text = content.decode("utf-8", errors="ignore")

    session_log.debug(f"File content extracted: {len(text)} chars")

    file_data = session_service.add_file(
        session_id=session_id,
        file_name=file.filename,
        file_type=file.content_type or "text/plain",
        file_content=text,
        file_size=len(content)
    )

    if not file_data:
        session_log.error("Failed to save file")
        raise HTTPException(status_code=500, detail="Failed to save file")

    session_log.success(f"File saved: {file.filename}")
    return file_data


@server.post("/sessions/scripts")
async def save_script(request: ScriptSave):
    """Save or update a script for a session"""
    session_log.start(f"Save script", {
        "session": request.session_id[:8] if len(request.session_id) > 8 else request.session_id,
        "script_number": request.script_number,
        "angle": request.angle_name[:20] if request.angle_name else "none"
    })
    try:
        if request.session_id == "local-session":
            session_log.info("Local session - skipping DB save")
            return {"session_id": request.session_id, "script_number": request.script_number, "status": "local"}
        script = session_service.save_script(
            session_id=request.session_id,
            script_number=request.script_number,
            script_content=request.script_content,
            angle_name=request.angle_name,
            angle_focus=request.angle_focus,
            angle_hook_style=request.angle_hook_style
        )
        if not script:
            session_log.warn("Script save returned None")
            return {"session_id": request.session_id, "script_number": request.script_number, "status": "failed"}
        session_log.success(f"Script {request.script_number} saved")
        return script
    except Exception as e:
        session_log.error(f"Save script failed: {str(e)}")
        return {"session_id": request.session_id, "script_number": request.script_number, "status": "error"}


@server.put("/sessions/{session_id}")
async def update_session(session_id: str, updates: dict):
    """Update session fields"""
    session_log.start(f"Update session: {session_id[:8]}", {"fields": list(updates.keys())})
    success = session_service.update_session(session_id, updates)
    if not success:
        session_log.error("Update failed")
        raise HTTPException(status_code=500, detail="Failed to update session")
    session_log.success("Session updated")
    return {"status": "updated"}


# ============================================
# CHAT ENDPOINTS (Version 2.0)
# ============================================

class LocalChatMessage(BaseModel):
    """Chat message for local mode (no Supabase required)"""
    script_content: str
    message: str
    script_number: int = 1
    angle_name: str = ""
    angle_focus: str = ""


@server.post("/chat/local")
async def chat_local(request: LocalChatMessage):
    """
    Chat with Claude about a script - NO DATABASE REQUIRED.
    Frontend sends the script content directly.
    """
    chat_log.start("Local chat request", {
        "script": request.script_number,
        "message_len": len(request.message),
        "script_len": len(request.script_content)
    })

    if not request.script_content:
        chat_log.error("No script content provided")
        return {
            "response": "Please provide script content to edit.",
            "updated_script": "",
            "script_changed": False
        }

    angle_info = {
        "name": request.angle_name,
        "focus": request.angle_focus
    } if request.angle_name else None

    # Get Claude's response
    chat_log.step("Calling Claude for local chat")
    start_time = time.time()
    try:
        full_response = await script_chat_agent.chat(
            user_message=request.message,
            current_script=request.script_content,
            chat_history=[],  # No history in local mode
            angle_info=angle_info
        )
        duration = (time.time() - start_time) * 1000
        chat_log.success(f"Claude response received", {"duration_ms": f"{duration:.0f}", "response_len": len(full_response)})

        # Extract updated script (the full script content)
        updated_script = script_chat_agent.extract_updated_script(full_response, request.script_content)
        script_changed = updated_script != request.script_content

        # Extract just the chat message (short response for chat UI)
        chat_message = script_chat_agent.extract_chat_message(full_response)

        if script_changed:
            chat_log.info("Script was modified by Claude")
        else:
            chat_log.info("No script changes detected")

        return {
            "response": chat_message,  # Short message for chat panel
            "updated_script": updated_script,  # Full script for main view
            "script_changed": script_changed
        }
    except Exception as e:
        chat_log.error(f"Local chat failed: {str(e)}", exc=e)
        return {
            "response": f"Error: {str(e)}",
            "updated_script": request.script_content,
            "script_changed": False
        }


@server.post("/chat")
async def chat_with_script(request: ChatMessage):
    """
    Chat with Claude about a specific script.
    Claude will edit or rewrite based on the user's request.
    """
    chat_log.start("Chat request", {
        "session": request.session_id[:8] if len(request.session_id) > 8 else request.session_id,
        "script": request.script_number,
        "message_len": len(request.message)
    })

    # Handle local session - redirect to use local chat
    if request.session_id == "local-session":
        chat_log.warn("Session is local - use /chat/local endpoint instead")
        return {
            "response": "For local mode, please use the /chat/local endpoint with script content.",
            "updated_script": "",
            "script_changed": False
        }

    # Get the session and current script
    try:
        chat_log.step("Loading session")
        session = session_service.get_session(request.session_id)
    except Exception as e:
        chat_log.error(f"Session lookup failed: {str(e)}")
        return {
            "response": "Could not load session. Supabase may not be configured correctly.",
            "updated_script": "",
            "script_changed": False
        }

    if not session:
        chat_log.error("Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # Find the current script
    scripts = session.get("scripts", [])
    current_script = None
    angle_info = None

    for s in scripts:
        if s.get("script_number") == request.script_number:
            current_script = s.get("script_content", "")
            angle_info = {
                "name": s.get("angle_name", ""),
                "focus": s.get("angle_focus", ""),
                "hook_style": s.get("angle_hook_style", "")
            }
            break

    if not current_script:
        chat_log.error(f"Script {request.script_number} not found in session")
        raise HTTPException(status_code=404, detail=f"Script {request.script_number} not found")

    chat_log.info(f"Script found: {len(current_script)} chars, Angle: {angle_info.get('name', 'unknown')}")

    # Get chat history for this script
    chat_history = session.get("chat_history", {}).get(request.script_number, [])
    chat_log.debug(f"Chat history: {len(chat_history)} messages")

    # Save user message to DB
    chat_log.step("Saving user message")
    session_service.add_chat_message(
        session_id=request.session_id,
        script_number=request.script_number,
        role="user",
        content=request.message
    )

    # Get Claude's response
    chat_log.step("Calling Claude for response")
    start_time = time.time()
    full_response = await script_chat_agent.chat(
        user_message=request.message,
        current_script=current_script,
        chat_history=chat_history,
        angle_info=angle_info
    )
    duration = (time.time() - start_time) * 1000
    chat_log.success(f"Claude response received", {"duration_ms": f"{duration:.0f}", "response_len": len(full_response)})

    # Extract the short chat message for display
    chat_message = script_chat_agent.extract_chat_message(full_response)

    # Save assistant message to DB (save the short message, not the full response)
    chat_log.step("Saving assistant message")
    session_service.add_chat_message(
        session_id=request.session_id,
        script_number=request.script_number,
        role="assistant",
        content=chat_message
    )

    # Try to extract updated script and save it
    chat_log.step("Checking for script updates")
    updated_script = script_chat_agent.extract_updated_script(full_response, current_script)
    script_changed = updated_script != current_script

    if script_changed:
        chat_log.info("Script was modified - saving update")
        session_service.update_script(
            session_id=request.session_id,
            script_number=request.script_number,
            script_content=updated_script
        )
        chat_log.success(f"Script {request.script_number} updated")
    else:
        chat_log.info("No script changes detected")

    return {
        "response": chat_message,  # Short message for chat panel
        "updated_script": updated_script,  # Full script for main view
        "script_changed": script_changed
    }


@server.get("/sessions/{session_id}/chat/{script_number}")
async def get_chat_history(session_id: str, script_number: int):
    """Get chat history for a specific script"""
    chat_log.debug(f"Get chat history: session={session_id[:8]}, script={script_number}")
    history = session_service.get_chat_history(session_id, script_number)
    chat_log.info(f"Returned {len(history)} messages")
    return {"messages": history}
