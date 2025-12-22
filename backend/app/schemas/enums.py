from enum import Enum


class ScriptMode(str, Enum):
    INFORMATIONAL = "informational"
    LISTICAL = "listical"


class HookType(str, Enum):
    SHOCK = "shock"
    QUESTION = "question"
    NEGATIVE = "negative"
    STORY = "story"


class VectorType(str, Enum):
    FULL = "full"        # Full text for topic matching
    HOOK = "hook"        # Just the hook for style matching
    SKELETON = "skeleton"  # Structural skeleton (metadata)
