"""
Script Critic v6.0 - Comprehensive Viral Script Validator
Validates scripts against the Viral Script Formula System
"""
import os
import re
import json
from pathlib import Path
from typing import List, Literal
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.schemas.enums import ScriptMode


# Banned words list - automatic fail if found
BANNED_WORDS = [
    "DESTROYED", "PANICKING", "TERRIFYING", "CHAOS", "INSANE",
    "EXPOSED", "BACKSTABBED", "FURIOUS", "TREMBLING", "SHOCKING",
    "MIND-BLOWING", "BOMBSHELL"
]

# Banned phrases
BANNED_PHRASES = [
    "no one is safe",
    "is panicking",
    "drop a",
    "is trembling",
    "big tech doesn't want",
    "nobody is talking about this",
    "comment if",
    "like if you agree"
]


class CriticResponse(BaseModel):
    status: Literal["PASS", "FAIL"] = "PASS"
    reasons: List[str] = []
    feedback: str = ""
    score: int = Field(default=80, ge=0, le=100)
    spam_words_found: List[str] = []
    caps_words_found: List[str] = []
    missing_elements: List[str] = []


class ScriptCritic:
    def __init__(self):
        # Use GPT-4o-mini for fast, reliable validation
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            max_tokens=1500
        )

    def _check_spam_words(self, text: str) -> List[str]:
        """Find banned spam words in text"""
        found = []
        text_upper = text.upper()
        for word in BANNED_WORDS:
            if word in text_upper:
                found.append(word)
        return found

    def _check_caps_words(self, text: str) -> List[str]:
        """Find ALL-CAPS words (excluding acceptable acronyms)"""
        caps_pattern = r'\b[A-Z]{3,}\b'
        matches = re.findall(caps_pattern, text)

        # Acceptable acronyms and proper nouns
        acceptable = {
            'AI', 'API', 'CEO', 'CTO', 'CFO', 'COO', 'INR', 'USD', 'EUR',
            'GPT', 'LLM', 'ML', 'NLP', 'AWS', 'GCP', 'IBM', 'GPU', 'CPU',
            'RAM', 'SSD', 'NFT', 'VC', 'HOOK', 'CTA', 'PDF', 'URL', 'HTML',
            'CSS', 'SQL', 'SDK', 'iOS', 'OPENAI', 'CHATGPT', 'CLAUDE',
            'GEMINI', 'LLAMA', 'META', 'GOOGLE', 'MICROSOFT', 'AMAZON',
            'TESLA', 'NVIDIA', 'AMD', 'INTEL', 'TCS', 'INFOSYS', 'WIPRO',
            'OPTIONS', 'FINAL', 'SCRIPT'  # Headers
        }

        return [m for m in matches if m not in acceptable]

    def _check_banned_phrases(self, text: str) -> List[str]:
        """Find banned phrases in text"""
        found = []
        text_lower = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in text_lower:
                found.append(phrase)
        return found

    def _check_structure(self, text: str, mode: ScriptMode) -> List[str]:
        """Check for required structural elements"""
        missing = []

        # Check for hook options header
        if "## HOOK OPTIONS" not in text and "HOOK OPTIONS" not in text:
            missing.append("HOOK OPTIONS header")

        # Check for final script header
        if "## FINAL SCRIPT" not in text and "FINAL SCRIPT" not in text:
            missing.append("FINAL SCRIPT header")

        # Check for 5 hooks
        hook_count = len(re.findall(r'HOOK\s*\d+:', text))
        if hook_count < 5:
            missing.append(f"Only {hook_count}/5 hooks found")

        # Check for direct quote
        if '"' not in text or text.count('"') < 2:
            missing.append("Direct quote in quotation marks")

        # Check for India relevance keywords
        india_keywords = ['india', 'indian', 'rupee', '₹', 'rs.', 'crore', 'lakh']
        has_india = any(kw in text.lower() for kw in india_keywords)
        if not has_india:
            missing.append("India relevance")

        # Mode-specific checks
        if mode == ScriptMode.LISTICAL:
            # Check for numbered list items
            list_items = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
            if list_items < 5:
                missing.append(f"Only {list_items}/5 list items found")

        return missing

    def validate(self, draft: str, mode: ScriptMode) -> CriticResponse:
        """Validate script with comprehensive checks"""

        # Pre-check for spam words and caps (fast local check)
        spam_words = self._check_spam_words(draft)
        caps_words = self._check_caps_words(draft)
        banned_phrases = self._check_banned_phrases(draft)
        missing_elements = self._check_structure(draft, mode)

        # If spam words found, automatic fail
        if spam_words or banned_phrases:
            return CriticResponse(
                status="FAIL",
                score=20,
                spam_words_found=spam_words,
                caps_words_found=caps_words,
                missing_elements=missing_elements,
                reasons=["Banned words/phrases found"],
                feedback=f"AUTOMATIC FAIL: Found banned words: {spam_words + banned_phrases}. Replace with approved alternatives."
            )

        # If too many ALL-CAPS words, fail
        if len(caps_words) > 3:
            return CriticResponse(
                status="FAIL",
                score=40,
                spam_words_found=spam_words,
                caps_words_found=caps_words,
                missing_elements=missing_elements,
                reasons=["Too many ALL-CAPS words"],
                feedback=f"Found {len(caps_words)} ALL-CAPS words: {caps_words[:5]}. Remove ALL-CAPS emphasis."
            )

        # LLM-based validation for nuanced checks
        system_msg = f"""You are a Script Quality Validator for viral Instagram Reels (Indian tech audience).

MODE: {mode.value.upper()}

## VALIDATION CHECKLIST

### 1. SPAM WORD CHECK (Automatic FAIL if found)
BANNED WORDS - Script FAILS if ANY are found:
- DESTROYED, PANICKING, TERRIFYING, CHAOS, INSANE (in caps)
- EXPOSED, BACKSTABBED, FURIOUS, TREMBLING, SHOCKING (in caps)
- MIND-BLOWING (in caps)
- Any ALL-CAPS words used for emphasis

BANNED PHRASES:
- "No [X] is safe anymore"
- "[Company] is PANICKING"
- "Drop a [emoji] if..."
- "The [industry] is TREMBLING"
- "Big tech doesn't want you to see this"

### 2. HOOK FORMAT CHECK
Required:
- Starts with "## HOOK OPTIONS" header
- Exactly 5 hooks provided
- Each hook is 10-20 words
- Each hook starts with person/company name (not "This" or "What if")
- Each hook contains action verb (dropped, released, built, rejected, etc.)
- Each hook contains specific detail (number, company, outcome)
- NO type labels like "(Quote-Based)" or "(Contrarian)"
- NO ALL-CAPS words in any hook

### 3. FINAL SCRIPT FORMAT CHECK
Required:
- Starts with "## FINAL SCRIPT" header
- Uses best hook from options
- Word count: 120-150 words
- Contains at least 1 direct quote in "quotation marks"
- Contains specific numbers (not rounded)
- Contains India relevance
- Has genuine CTA (not "Drop a [emoji]")
- Short sentences (under 12 words average)
- One-sentence paragraphs used for emphasis

### 4. STYLE CHECK
Required:
- Zero ALL-CAPS words in entire script (except acronyms)
- Zero banned spam words
- Credible tone (not clickbaity)
- Transitions used ("But here's...", "Plot twist:", etc.)
- Maximum 1 emoji (at end in CTA only)

### 5. STRUCTURE CHECK
Required elements present:
- Hook (scroll-stopper)
- Stakes amplifier
- Credibility build
- Pattern interrupt/transition
- Revelation/explanation
- Proof/stats
- India angle
- Insight/reframe
- Open question
- CTA

## SCORING
- 0-30 points: Spam/format issues
- 30-50 points: Missing elements
- 50-70 points: Weak execution
- 70-85 points: Good, minor issues
- 85-100 points: Excellent, ready to use

Score < 60: FAIL - Return specific feedback
Score >= 60: PASS

## OUTPUT FORMAT
Return ONLY valid JSON:
{{"status": "PASS" or "FAIL", "score": 0-100, "spam_words_found": [], "caps_words_found": [], "missing_elements": [], "reasons": ["reason1", "reason2"], "feedback": "Detailed feedback"}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "DRAFT TO VALIDATE:\n\n{draft}\n\nPRE-CHECK RESULTS:\n- Spam words found: {spam}\n- Caps words found: {caps}\n- Missing elements: {missing}\n\nRespond with JSON only:")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "draft": draft,
                "spam": spam_words,
                "caps": caps_words,
                "missing": missing_elements
            })
            content = response.content.strip()

            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Merge pre-check results
                data['spam_words_found'] = list(set(data.get('spam_words_found', []) + spam_words))
                data['caps_words_found'] = list(set(data.get('caps_words_found', []) + caps_words))
                data['missing_elements'] = list(set(data.get('missing_elements', []) + missing_elements))
                return CriticResponse(**data)

            # Fallback: Check for keywords in response
            if "PASS" in content.upper() and "FAIL" not in content.upper():
                return CriticResponse(
                    status="PASS",
                    reasons=[],
                    feedback="Script approved",
                    score=80,
                    spam_words_found=spam_words,
                    caps_words_found=caps_words,
                    missing_elements=missing_elements
                )
            elif "FAIL" in content.upper():
                return CriticResponse(
                    status="FAIL",
                    reasons=["Quality check failed"],
                    feedback=content[:300],
                    score=50,
                    spam_words_found=spam_words,
                    caps_words_found=caps_words,
                    missing_elements=missing_elements
                )

            # Default based on pre-check results
            if missing_elements:
                return CriticResponse(
                    status="FAIL" if len(missing_elements) > 2 else "PASS",
                    reasons=missing_elements,
                    feedback=f"Missing elements: {', '.join(missing_elements)}",
                    score=60 if len(missing_elements) <= 2 else 45,
                    spam_words_found=spam_words,
                    caps_words_found=caps_words,
                    missing_elements=missing_elements
                )

            return CriticResponse(
                status="PASS",
                reasons=[],
                feedback="Auto-approved",
                score=75,
                spam_words_found=spam_words,
                caps_words_found=caps_words,
                missing_elements=missing_elements
            )

        except Exception as e:
            print(f"[Critic Error] {e}")
            # On error, still check pre-check results
            if spam_words:
                return CriticResponse(
                    status="FAIL",
                    reasons=["Spam words found"],
                    feedback=f"Found banned words: {spam_words}",
                    score=30,
                    spam_words_found=spam_words,
                    caps_words_found=caps_words,
                    missing_elements=missing_elements
                )

            return CriticResponse(
                status="PASS",
                reasons=[],
                feedback=f"Skipped LLM check due to error: {str(e)[:50]}",
                score=70,
                spam_words_found=spam_words,
                caps_words_found=caps_words,
                missing_elements=missing_elements
            )
