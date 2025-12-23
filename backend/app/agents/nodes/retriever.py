"""
Style Retriever Node v8.3
Retrieves similar script examples from the vector database for style reference.
Uses AI to extract RELEVANT parts, not just truncated full scripts.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from app.db.storage import query_similar
from app.schemas.enums import ScriptMode, VectorType


# Use fast model for extraction
_extractor_llm = None


def get_extractor():
    """Lazy load the extractor LLM"""
    global _extractor_llm
    if _extractor_llm is None:
        _extractor_llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=500
        )
    return _extractor_llm


def extract_relevant_parts(script: str, topic: str) -> str:
    """
    Use AI to extract the RELEVANT parts of a script for the current topic.
    Instead of truncating, intelligently pull out useful elements.
    """
    if len(script) < 200:
        return script

    llm = get_extractor()

    prompt = f"""Extract the most relevant and reusable elements from this past script for a NEW script about: "{topic}"

PAST SCRIPT:
{script[:1500]}

EXTRACT (in 100-150 words):
1. Hook structure that worked (first line pattern)
2. Transition phrases used mid-script
3. Number presentation style
4. Closing/CTA approach
5. Any analogies or comparisons that were effective

Format as brief notes, not full sentences. Focus on TECHNIQUE, not content."""

    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"[Retriever] Extraction failed: {e}")
        # Fallback to truncation
        return script[:400]


def retrieve_style_context(topic: str, mode: ScriptMode) -> str:
    """
    Retrieves diverse style examples from vector storage.
    Uses AI to extract relevant parts instead of blind truncation.

    NOTE:
    We intentionally do NOT filter by 'hook_type' here.
    In v1, we want broad structure matching based on Mode.
    'hook_type' is stored in metadata for future analytics or
    specific 'Rewrite Hook' features.
    """
    # Query for similar full-text examples
    full_results = query_similar(
        query_text=topic,
        mode=mode,
        vector_type=VectorType.FULL,
        limit=4
    )

    # Query for similar hooks
    hook_results = query_similar(
        query_text=topic,
        mode=mode,
        vector_type=VectorType.HOOK,
        limit=4
    )

    # Combine and deduplicate by script_id
    seen_scripts = set()
    style_examples = []

    # Extract relevant parts from full examples
    for result in full_results:
        sid = result.get("script_id")
        if sid and sid not in seen_scripts:
            seen_scripts.add(sid)
            content = result.get("content", "")
            if content:
                # Use AI to extract relevant parts
                extracted = extract_relevant_parts(content, topic)
                style_examples.append({
                    "type": "full_script",
                    "content": extracted
                })
            if len(style_examples) >= 2:
                break

    # Add hook examples (these are already short)
    for result in hook_results:
        sid = result.get("script_id")
        if sid and sid not in seen_scripts:
            seen_scripts.add(sid)
            content = result.get("content", "")[:300]
            if content:
                style_examples.append({
                    "type": "hook",
                    "content": content
                })
            if len(style_examples) >= 3:
                break

    if not style_examples:
        return "No prior examples found. Use a generic viral structure."

    # Format Output
    output_parts = []

    for i, example in enumerate(style_examples, 1):
        if example["type"] == "full_script":
            output_parts.append(f"--- STYLE TECHNIQUES FROM PAST SCRIPT {i} ---")
            output_parts.append(example["content"])
        else:
            output_parts.append(f"--- HOOK EXAMPLE {i} ---")
            output_parts.append(example["content"])
        output_parts.append("")

    return "\n".join(output_parts)
