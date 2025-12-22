"""
Style Retriever Node
Retrieves similar script examples from the vector database for style reference.
"""
from app.db.storage import query_similar
from app.schemas.enums import ScriptMode, VectorType


def retrieve_style_context(topic: str, mode: ScriptMode) -> str:
    """
    Retrieves diverse style examples from vector storage.
    Filters out duplicates by checking Script ID.

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
        limit=6
    )

    # Query for similar hooks
    hook_results = query_similar(
        query_text=topic,
        mode=mode,
        vector_type=VectorType.HOOK,
        limit=6
    )

    # Combine and deduplicate by script_id
    seen_scripts = set()
    selected_docs = []

    # First add full examples
    for result in full_results:
        sid = result.get("script_id")
        if sid and sid not in seen_scripts:
            seen_scripts.add(sid)
            content = result.get("content", "")[:500]
            selected_docs.append(content)
            if len(selected_docs) >= 2:
                break

    # Then add hook examples
    for result in hook_results:
        sid = result.get("script_id")
        if sid and sid not in seen_scripts:
            seen_scripts.add(sid)
            content = result.get("content", "")[:300]
            selected_docs.append(f"HOOK: {content}")
            if len(selected_docs) >= 3:
                break

    if not selected_docs:
        return "No prior examples found. Use a generic viral structure."

    # Format Output
    context = ""
    for i, doc in enumerate(selected_docs, 1):
        context += f"--- STYLE EXAMPLE {i} ---\n{doc}\n\n"

    return context
