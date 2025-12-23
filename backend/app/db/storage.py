"""
Vector Storage Module - Supabase pgvector
Stores script embeddings for style learning and retrieval.
"""
import os
import uuid
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from supabase import create_client, Client

from app.schemas.enums import ScriptMode, VectorType, HookType


# ---------------------------
# Initialize Supabase Client
# ---------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize client only if credentials exist
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------
# Lazy Loading Embedding Model (saves ~300MB at startup)
# ---------------------------
_embedding_model = None


def get_embedding_model():
    """Lazy load the embedding model only when needed"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


# ---------------------------
# Fallback: In-memory storage for local dev
# ---------------------------
_fallback_storage: List[Dict] = []


class Collection:
    """Wrapper to provide consistent API for both Supabase and fallback"""

    def count(self) -> int:
        if supabase:
            try:
                result = supabase.table("script_vectors").select("id", count="exact").execute()
                return result.count or 0
            except Exception as e:
                print(f"[Storage] Count error: {e}")
                return 0
        return len(_fallback_storage)


collection = Collection()


def add_script_to_db(
    title: str,
    full_text: str,
    mode: ScriptMode,
    hook_type: HookType,
    skeleton_text: str,
    hook_text: str,
) -> str:
    """
    Saves 3 vectors for a single script upload:
    - Full text (Topic match)
    - Hook only (Style match)
    - Skeleton (Structure match)
    """
    # 1. Generate embeddings (lazy load model)
    model = get_embedding_model()
    embeddings = model.encode(
        [full_text, hook_text, skeleton_text]
    ).tolist()

    # 2. Generate script ID
    script_id = str(uuid.uuid4())

    # 3. Prepare records
    records = [
        {
            "id": f"{script_id}_full",
            "script_id": script_id,
            "title": title,
            "mode": mode.value,
            "hook_type": hook_type.value,
            "vector_type": VectorType.FULL.value,
            "content": full_text,
            "embedding": embeddings[0],
        },
        {
            "id": f"{script_id}_hook",
            "script_id": script_id,
            "title": title,
            "mode": mode.value,
            "hook_type": hook_type.value,
            "vector_type": VectorType.HOOK.value,
            "content": hook_text,
            "embedding": embeddings[1],
        },
        {
            "id": f"{script_id}_skel",
            "script_id": script_id,
            "title": title,
            "mode": mode.value,
            "hook_type": hook_type.value,
            "vector_type": VectorType.SKELETON.value,
            "content": skeleton_text,
            "embedding": embeddings[2],
        },
    ]

    # 4. Insert into Supabase or fallback
    if supabase:
        try:
            supabase.table("script_vectors").upsert(records).execute()
            print(f"[Storage] Added script {script_id} to Supabase")
        except Exception as e:
            print(f"[Storage] Insert error: {e}")
            _fallback_storage.extend(records)
    else:
        _fallback_storage.extend(records)
        print(f"[Storage] Added script {script_id} to fallback storage")

    return script_id


def query_similar(
    query_text: str,
    mode: Optional[ScriptMode] = None,
    vector_type: VectorType = VectorType.FULL,
    limit: int = 3
) -> List[Dict]:
    """
    Query similar scripts using vector similarity.
    """
    # Generate query embedding (lazy load model)
    model = get_embedding_model()
    query_embedding = model.encode([query_text])[0].tolist()

    if supabase:
        try:
            # Use Supabase RPC function for vector similarity search
            result = supabase.rpc(
                "match_scripts",
                {
                    "query_embedding": query_embedding,
                    "match_count": limit,
                    "filter_mode": mode.value if mode else None,
                    "filter_vector_type": vector_type.value
                }
            ).execute()
            return result.data or []
        except Exception as e:
            print(f"[Storage] Query error: {e}")
            return _query_fallback(query_embedding, mode, vector_type, limit)
    else:
        return _query_fallback(query_embedding, mode, vector_type, limit)


def _query_fallback(
    query_embedding: List[float],
    mode: Optional[ScriptMode],
    vector_type: VectorType,
    limit: int
) -> List[Dict]:
    """Fallback similarity search using cosine similarity"""
    import numpy as np

    if not _fallback_storage:
        return []

    # Filter by mode and vector type
    filtered = [
        r for r in _fallback_storage
        if r["vector_type"] == vector_type.value
        and (mode is None or r["mode"] == mode.value)
    ]

    if not filtered:
        return []

    # Calculate cosine similarity
    query_vec = np.array(query_embedding)
    similarities = []

    for record in filtered:
        doc_vec = np.array(record["embedding"])
        similarity = np.dot(query_vec, doc_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
        )
        similarities.append((record, similarity))

    # Sort by similarity and return top matches
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in similarities[:limit]]
