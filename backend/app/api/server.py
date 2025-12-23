import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env from backend directory (handles running from different directories)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Minimal startup log
print(f"[ScriptAI] Starting - API Key: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import PyPDF2
import io

from app.db.storage import collection, add_script_to_db
from app.schemas.enums import ScriptMode, HookType
from app.utils.skeleton_utils import generate_skeleton, extract_hook
from app.agents.graph import app as agent_app


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

# Allow all vercel.app subdomains for preview deployments
server.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Data Models --------
class TrainRequest(BaseModel):
    title: str
    script_content: str
    mode: ScriptMode
    hook_type: HookType


# -------- Endpoints --------
@server.get("/")
def health_check():
    count = collection.count()
    return {"status": "ok", "vectors_stored": count}


@server.post("/train_script")
def train_script(request: TrainRequest):
    print(f"[Train] {request.title} ({request.mode.value})")

    try:
        skeleton = generate_skeleton(request.script_content)
        hook_text = extract_hook(request.script_content)

        script_id = add_script_to_db(
            title=request.title,
            full_text=request.script_content,
            mode=request.mode,
            hook_type=request.hook_type,
            skeleton_text=skeleton,
            hook_text=hook_text,
        )

        print(f"[Train] ✓ Saved {script_id}")

        return {
            "status": "success",
            "script_id": script_id,
            "meta_preview": {
                "skeleton": skeleton,
                "mode": request.mode.value,
            },
        }
    except Exception as e:
        print(f"[Train] ✗ {str(e)}")
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
        return "\n\n".join(text_parts)
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"


@server.post("/generate_stream")
async def generate_stream(
    topic: str = Form(...),
    user_notes: str = Form(""),
    mode: ScriptMode = Form(...),
    files: List[UploadFile] = File(None),
    skip_research: bool = Form(False),
):
    # Log the request
    print(f"\n[Generate] Topic: {topic[:50]}... | Mode: {mode.value} | Skip Research: {skip_research}")

    # Read files BEFORE the generator (outside async generator)
    all_file_text = []
    if files:
        for file in files:
            if file and file.filename:
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
    if files:
        print(f"[Generate] Files loaded: {len(all_file_text)} ({len(file_content)} chars)")

    async def event_generator():
        start_time = time.time()

        try:
            # Send file reading status if files were provided
            if all_file_text:
                yield json.dumps({"type": "status", "message": f"Loaded {len(all_file_text)} file(s)..."}) + "\n"

            # 2. Init State
            initial_state = {
                "topic": topic,
                "mode": mode,
                "user_notes": user_notes,
                "file_content": file_content,
                "revision_count": 0,
                "skip_research": skip_research,
            }
            if skip_research:
                yield json.dumps({"type": "status", "message": f"Agent starting ({mode.value})..."}) + "\n"
            else:
                yield json.dumps({"type": "status", "message": "Stage 0: Detecting topic type..."}) + "\n"
            final_draft = ""
            checker_analysis = ""
            optimized_script = ""

            # 3. Stream Graph Events
            async for step in agent_app.astream(initial_state):
                for node, output in step.items():
                    if node == "researcher":
                        # Check research status first
                        research_status = output.get("research_status", "complete")

                        # Handle generic topic (needs angle selection)
                        if research_status == "needs_specific_angle":
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
                            yield json.dumps({"type": "research", "data": research_data}) + "\n"

                        # Send sources if available
                        sources = output.get("research_sources", [])
                        if sources:
                            yield json.dumps({"type": "sources", "data": sources}) + "\n"

                        # Send quality score if available
                        quality_score = output.get("research_quality_score", 0)
                        topic_type = output.get("topic_type", "A")
                        selected_angle = output.get("selected_angle", {})
                        angle_name = selected_angle.get("angle", "")[:50] if selected_angle else ""

                        if quality_score > 0:
                            yield json.dumps({
                                "type": "status",
                                "message": f"Research complete (Quality: {quality_score}/100)"
                            }) + "\n"
                        else:
                            yield json.dumps({"type": "status", "message": "Research complete..."}) + "\n"

                    if node == "retriever":
                        yield json.dumps({"type": "status", "message": "Analyzing trained styles..."}) + "\n"

                    if node == "writer":
                        # Check if multi-angle mode
                        if output.get("angles"):
                            angles = output.get("angles", [])
                            yield json.dumps({
                                "type": "angles",
                                "data": [{"name": a.get("name", ""), "focus": a.get("focus", "")} for a in angles]
                            }) + "\n"
                            yield json.dumps({"type": "status", "message": f"Generated 3 scripts with different angles..."}) + "\n"
                        else:
                            yield json.dumps({"type": "status", "message": "Claude is writing script..."}) + "\n"

                    if node == "critic":
                        if output.get("critic_feedback") == "PASS":
                            yield json.dumps({"type": "status", "message": "Script passed quality check!"}) + "\n"
                        else:
                            revision = output.get("revision_count", 1)
                            yield json.dumps({"type": "status", "message": f"Revision {revision}: Improving script..."}) + "\n"

                    if node == "checker":
                        yield json.dumps({"type": "status", "message": "Analyzing hooks & optimizing..."}) + "\n"
                        # Send checker analysis
                        if "checker_analysis" in output:
                            checker_analysis = output["checker_analysis"]
                            yield json.dumps({"type": "analysis", "data": checker_analysis}) + "\n"
                        # Send optimized script
                        if "optimized_script" in output:
                            optimized_script = output["optimized_script"]
                        # Send hook ranking
                        if "hook_ranking" in output:
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
                    if "angles" in output:
                        angles_list = output["angles"]
                    if "summary_table" in output:
                        summary_table = output["summary_table"]
                    if "full_output" in output:
                        full_output = output["full_output"]

            # 4. Final Result
            total_time = time.time() - start_time
            print(f"[Generate] ✓ Complete in {total_time:.1f}s | Draft: {len(final_draft)} chars")

            # Check if we have multi-angle output
            if 'scripts_list' in dir() and scripts_list and len(scripts_list) > 1:
                yield json.dumps({
                    "type": "result",
                    "data": {
                        "scripts": scripts_list,
                        "angles": angles_list if 'angles_list' in dir() else [],
                        "summary_table": summary_table if 'summary_table' in dir() else "",
                        "full_output": full_output if 'full_output' in dir() else final_draft,
                        "draft": final_draft,
                        "optimized": optimized_script if optimized_script else final_draft
                    }
                }) + "\n"
            else:
                yield json.dumps({
                    "type": "result",
                    "data": {
                        "draft": final_draft,
                        "optimized": optimized_script if optimized_script else final_draft
                    }
                }) + "\n"

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
