"""
Script Critic - Validates scripts against Vibhay quality standards
"""
import os
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


class CriticResponse(BaseModel):
    status: Literal["PASS", "FAIL"]
    reasons: List[str]
    feedback: str
    score: int = Field(ge=0, le=100)


class ScriptCritic:
    def __init__(self):
        # Use GPT-4o for fast, accurate validation
        self.llm = ChatOpenAI(
            model="openai/gpt-4o",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0
        )
        self.structured_llm = self.llm.with_structured_output(CriticResponse)

    def validate(self, draft: str, mode: ScriptMode) -> CriticResponse:
        system_msg = f"""
You are a Quality Critic for viral Instagram Reel scripts (v5.0).

MODE: {mode.value.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURAL REQUIREMENTS (Hard Fail if missing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **HOOK OPTIONS SECTION**
   - Must contain "## HOOK OPTIONS" header
   - Must have exactly 5 hook variants (HOOK 1 through HOOK 5)
   - ALL hooks must follow same formula: [Person/Company] + [Action Verb] + [Specific Detail]
   - NO type labels (NO "Quote-Based", "Contrarian", etc.)

2. **FINAL SCRIPT SECTION**
   - Must contain "## FINAL SCRIPT" header
   - Must use one of the generated hooks
   - Body should be 120-150 words

3. **NO VISUAL TAGS**
   - Script should NOT contain <visual> tags
   - Pure text script only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOOK FORMULA CHECK (Critical)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each hook must:
- Start with a person/company name
- Use action verbs: dropped, released, built, rejected, forced, is secretly building, quietly started
- Include specific detail (number, company name, outcome)
- Be 10-20 words
- NO ALL-CAPS words (except acronyms like AI, API, CEO)
- NO spam words: DESTROYED, PANICKING, TERRIFYING, CHAOS, INSANE, EXPOSED, BACKSTABBED, SHOCKING

Example correct hooks:
- "Mark Zuckerberg panicked so hard that he tried to buy a company with zero products for $32 billion dollars."
- "Sam Altman is secretly building a powerful AI model that's already crushing the top AI models."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTENT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. **WORD COUNT**
   - FINAL SCRIPT body: 120-150 words total

5. **NO GREETINGS**
   - Must NOT start with "Hello", "Hey", "Welcome", etc.
   - Hook is the first line

6. **MODE ADHERENCE**
   - INFORMATIONAL: Body flows as paragraphs
   - LISTICAL: Body uses numbered format (1., 2., 3., 4., 5.)

7. **VIRAL ELEMENTS**
   - At least one direct quote in "quotation marks"
   - Specific numbers (not rounded)
   - India relevance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Score 80-100: PASS (All requirements met)
- Score 60-79: PASS with notes
- Score 0-59: FAIL (Missing critical elements or has spam words)

Return PASS only if score >= 60.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "DRAFT TO REVIEW:\n\n{draft}")
        ])

        chain = prompt | self.structured_llm
        return chain.invoke({"draft": draft})
