import re


def generate_skeleton(text: str) -> str:
    """
    Analyzes text to create a structural fingerprint.
    Output Example: "HOOK_LEN:12 | BLOCKS:6 | LIST:False"
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "EMPTY"

    # 1. Analyze Hook (First non-empty line)
    hook = lines[0]
    hook_word_count = len(hook.split())

    # 2. Analyze Structure (Paragraphs vs List Items)
    # Heuristic: Count lines starting with numbers (1.) or bullets (- or *)
    list_items = len([
        l for l in lines
        if re.match(r"^(\d+\.|-|\*)\s+", l)
    ])
    total_blocks = len(lines)

    # If more than 33% of lines look like list items, classify as listical structure
    is_listical = list_items > (total_blocks / 3)

    # 3. Construct String Representation
    skeleton = (
        f"HOOK_LEN:{hook_word_count} | "
        f"BLOCKS:{total_blocks} | "
        f"LIST:{is_listical}"
    )
    return skeleton


def extract_hook(text: str) -> str:
    """Returns just the first 2 lines (max ~300 chars)"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return "\n".join(lines[:2])[:300]
