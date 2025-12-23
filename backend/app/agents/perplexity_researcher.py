"""
Perplexity Deep Research Agent v7.0
Focused on RESEARCH ONLY - gathering facts, quotes, and data
The Writer node (Claude) handles script generation
"""
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# Deep Research Prompt v7.0 - Research ONLY (no script generation)
DEEP_RESEARCH_PROMPT = """You are an elite investigative researcher specializing in tech news for viral Instagram Reels content. Your job is to gather comprehensive, fact-based research that will be used by a scriptwriter.

## YOUR MISSION

Research the given topic deeply and extract:
1. **Hook-worthy facts** - Surprising, specific, verifiable claims
2. **Specific numbers** - Exact figures, not rounded (e.g., "$32.4 billion" not "about $30 billion")
3. **Direct quotes** - From key people involved, with attribution
4. **Credentials/background** - Who are the key people, their achievements
5. **India relevance** - Cost savings in ₹, accessibility for Indian market, local opportunities
6. **Timeline/context** - When did this happen, what led to it
7. **Bigger picture insights** - What does this mean for the industry

---

## RESEARCH QUALITY STANDARDS

### NUMBERS MUST BE:
- Specific: $32.4 billion, not "billions"
- Contextual: "That's 3x what Netflix spent last year"
- Verifiable: From credible sources

### QUOTES MUST BE:
- Direct quotes in "quotation marks"
- Attributed: "As [Person] said..."
- Impactful: Quotes that reveal insight or create curiosity

### FACTS MUST BE:
- Recent: Prefer news from the last 3-6 months
- Surprising: Something most people don't know
- Actionable: Why should the viewer care?

---

## OUTPUT FORMAT

Provide your research in this EXACT format:

## RESEARCH FINDINGS

### KEY PERSON/COMPANY PROFILE
- **Name:** [Full name]
- **Role:** [Current position]
- **Credentials:** [Past achievements, companies founded, notable work]
- **Why they matter:** [1-2 sentences on their significance]

### HOOK-WORTHY FACTS (5-7 facts)
1. [Surprising fact with specific number]
2. [Unexpected development or decision]
3. [Contrast or comparison that creates curiosity]
4. [Financial/impact metric]
5. [India-specific angle or relevance]
6. [Timeline fact - when this happened]
7. [Future implication or prediction]

### DIRECT QUOTES (2-3 quotes)
1. "[Exact quote]" — [Person Name], [Context of when/where said]
2. "[Exact quote]" — [Person Name], [Context]
3. "[Exact quote]" — [Person Name], [Context]

### SPECIFIC NUMBERS & METRICS
- [Metric 1]: [Exact number with context]
- [Metric 2]: [Exact number with context]
- [Metric 3]: [Exact number with context]
- [Metric 4]: [Exact number with context]

### INDIA RELEVANCE
- **Cost impact:** [How much Indian developers/users save in ₹]
- **Accessibility:** [Is it free? Available in India?]
- **Local opportunity:** [What can Indian creators/developers do with this]
- **Market comparison:** [How this compares to Indian alternatives]

### THE BIGGER PICTURE
- [What this means for the industry - 2-3 sentences]
- [Why this matters now - timing significance]
- [Prediction or future implication]

### TIMELINE
- [When did this start/happen]
- [Key milestones]
- [What's next]

---

## RESEARCH PRIORITIES

Focus on finding:
1. **The "wait, what?" fact** - Something that stops scrolling
2. **The credibility anchor** - Why we should trust this person/company
3. **The money angle** - Cost, savings, investment, valuation
4. **The India hook** - Direct relevance to Indian audience
5. **The quote goldmine** - Words directly from key people
6. **The contrast** - Before vs after, expected vs reality

---

## AVOID

- Vague statements without numbers
- Rounded figures ("about 1 million" → find exact number)
- Old news (prefer last 3-6 months)
- Unattributed claims
- Generic insights anyone could guess

---

NOW RESEARCH THE FOLLOWING TOPIC:"""


class PerplexityResearcher:
    """
    Deep Research Agent v7.0 using Perplexity via OpenRouter.
    Focused on gathering comprehensive research data.
    Script generation is handled separately by Claude.
    """

    def __init__(self):
        # Use Perplexity sonar-pro through OpenRouter
        self.llm = ChatOpenAI(
            model="perplexity/sonar-pro",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.2,  # Lower for more factual responses
            max_tokens=4000
        )

    def search(self, query: str) -> str:
        """Execute deep Perplexity search via OpenRouter."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", DEEP_RESEARCH_PROMPT),
            ("human", "{query}")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"query": query})
            return response.content
        except Exception as e:
            print(f"[Perplexity v7.0] Error: {e}")
            return f"[Research error: {str(e)[:100]}]"

    def research(self, topic: str, user_notes: str = "") -> Dict:
        """
        Deep research pipeline v7.0.
        Gathers comprehensive research data for the writer node.
        """
        main_query = f"""## TOPIC TO RESEARCH:

{topic}

{f'## ADDITIONAL CONTEXT/REQUIREMENTS:\n{user_notes}' if user_notes else ''}

---

Research this topic thoroughly. Find:
- The most surprising/hook-worthy facts
- Specific numbers and metrics
- Direct quotes from key people
- India relevance (cost savings in ₹, accessibility)
- The bigger picture / why this matters now

Provide detailed, factual research that a scriptwriter can use to create a viral Instagram Reel."""

        content = self.search(main_query)

        return {
            "queries": [f"Deep Research v7.0: {topic[:50]}..."],
            "raw_results": [],
            "compressed_bullets": content,
            "sources": []
        }
