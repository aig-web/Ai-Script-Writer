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

        # Note: India relevance is NOT required - only include if natural connection exists

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
        system_msg = f"""You're reviewing a script before it goes out.

Read it like a viewer would. Does it hold attention? Does it make sense? Does it feel authentic?

MODE: {mode.value.upper()}

## Things to Check

**Does the opening hook?**
Is there a reason to keep watching in the first 3 seconds? Or does it start slow?

**Is there rhythm?**
Short punchy lines in the opening? Or long sentences that lose momentum?

**Do the numbers land?**
Every number should have context. If there's a stat without comparison, flag it.

**Is there proof?**
A quote from someone credible? Something that makes this feel real, not just claims?

**Is the contrast clear?**
Can you quickly understand old way vs new way? Problems vs solutions?

**Does it zoom out?**
Is there a bigger picture? Industry impact? Or does it stay small?

**Does the insight land?**
Is there a sharp reframe at the end? Or generic fluff?

**Is the CTA engaging?**
Does the closing question make you want to respond? Or is it generic?

**Is the India angle natural?**
If there's an India connection - does it feel organic or forced?
If there's no connection - good, don't force one.

## Pre-Check Results
- Spam words found: {spam_words}
- Caps words found: {caps_words}
- Missing elements: {missing_elements}

## Scoring
- 85-100: Ship it - ready to post
- 70-84: Good - minor polish needed
- 50-69: Needs work - specific issues to fix
- Below 50: Major revision needed

## OUTPUT FORMAT
Return ONLY valid JSON:
{{"status": "PASS" or "FAIL", "score": 0-100, "spam_words_found": [], "caps_words_found": [], "missing_elements": [], "reasons": ["what's working well"], "feedback": "What needs work and how to fix it"}}"""

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
