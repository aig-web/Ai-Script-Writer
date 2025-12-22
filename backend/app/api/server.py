import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory (handles running from different directories)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Print to confirm API key is loaded (remove in production)
print(f"[DEBUG] API Key loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

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
import os
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
        return {
            "status": "success",
            "script_id": script_id,
            "meta_preview": {
                "skeleton": skeleton,
                "mode": request.mode.value,
            },
        }
    except Exception as e:
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
    skip_research: bool = Form(False),  # NEW: Option to skip Tavily research
):
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

    async def event_generator():
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
                "skip_research": skip_research,  # Pass to graph
            }
            yield json.dumps({"type": "status", "message": f"Agent starting ({mode.value})..."}) + "\n"
            final_draft = ""
            checker_analysis = ""
            optimized_script = ""

            # 3. Stream Graph Events
            async for step in agent_app.astream(initial_state):
                for node, output in step.items():
                    if node == "researcher":
                        # Send research data
                        yield json.dumps({"type": "research", "data": output.get("research_data", "")}) + "\n"
                        # Send sources if available
                        sources = output.get("research_sources", [])
                        if sources:
                            yield json.dumps({"type": "sources", "data": sources}) + "\n"
                        yield json.dumps({"type": "status", "message": "Perplexity research complete..."}) + "\n"

                    if node == "retriever":
                        yield json.dumps({"type": "status", "message": "Analyzing trained styles..."}) + "\n"

                    if node == "writer":
                        yield json.dumps({"type": "status", "message": "Claude is writing script..."}) + "\n"

                    if node == "critic":
                        if output.get("critic_feedback") == "PASS":
                            yield json.dumps({"type": "status", "message": "Script passed quality check!"}) + "\n"
                        else:
                            revision = output.get("revision_count", 1)
                            yield json.dumps({"type": "status", "message": f"Revision {revision}: Improving script..."}) + "\n"

                    if node == "checker":
                        yield json.dumps({"type": "status", "message": "Analyzing hooks & optimizing script..."}) + "\n"
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

                    # Capture latest draft
                    if "draft" in output:
                        final_draft = output["draft"]

            # 4. Final Result - Send both original draft and optimized version
            yield json.dumps({
                "type": "result",
                "data": {
                    "draft": final_draft,
                    "optimized": optimized_script if optimized_script else final_draft
                }
            }) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
