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


# Deep Research Prompt v8.0 - EXHAUSTIVE Research (no script generation)
DEEP_RESEARCH_PROMPT = """You are an elite investigative researcher specializing in tech news for viral Instagram Reels content. Your job is to gather EXHAUSTIVE, fact-based research - aim for 80-100+ individual facts.

## YOUR MISSION

Research the given topic DEEPLY and extract EVERYTHING you can find:
- 30-50 specific numbers and statistics
- 15-20 direct quotes from different people
- 20-30 surprising/hook-worthy facts
- 10-15 comparison/contrast points
- 10-15 India-specific data points

Previous research gave only 15-25 facts. That's NOT ENOUGH. We need QUANTITY.

---

## WHAT TO FIND (Be exhaustive)

### 1. NUMBERS (Find 30-50 different numbers)
- Revenue, funding, valuation (all rounds)
- User counts, growth rates, market size
- Costs, prices, savings
- Percentages, rankings, comparisons
- Time durations, dates, milestones
- Employee counts, office locations

### 2. QUOTES (Find 15-20 quotes)
From: CEO, founders, executives, investors, analysts, competitors, customers, experts

### 3. HOOK-WORTHY FACTS (Find 20-30)
- Counter-intuitive facts
- Secret strategies
- Failure/comeback stories
- Controversial decisions
- First-ever achievements
- Record-breaking stats

### 4. PEOPLE (Profile 3-5 key people)
- Full name, title, background
- Previous roles, education
- Notable achievements
- Direct quotes

### 5. INDIA ANGLE (Only if naturally relevant)
NOTE: Only include if there's a GENUINE connection (Indian founders, Indian market impact, ₹ pricing).
Don't force India angle if no natural connection.
If relevant:
- Indian market size in ₹
- Indian users/customers
- Indian pricing
- Indian competitors

### 6. TIMELINE (Find 10+ dates)
- Founding, launches, funding rounds
- Key announcements, pivots
- Future planned dates

---

## OUTPUT FORMAT (Aim for 2000+ words)

### RAW NUMBERS & STATISTICS (List 30-50)
1. [Number] - [What it represents]
2. [Number] - [What it represents]
(Continue for 30-50 numbers)

### DIRECT QUOTES (List 15-20)
1. "[Exact quote]" — [Person], [Title], [Context]
2. "[Exact quote]" — [Person], [Title], [Context]
(Continue for 15-20 quotes)

### HOOK-WORTHY FACTS (List 20-30)
1. [Surprising fact]
2. [Counter-intuitive insight]
(Continue for 20-30 facts)

### KEY PEOPLE PROFILES
**Person 1:** [Name, Title, Background, Key Quote]
**Person 2:** [Name, Title, Background, Key Quote]
(Profile 3-5 people)

### INDIA RELEVANCE (Only if natural connection)
NOTE: Only include if genuine connection exists. Leave empty if forced.
If relevant:
- Market size: [₹ amount]
- Indian users: [Number]
- Indian pricing: [₹ prices]

### TIMELINE (List 10+ dates)
- [Date]: [Event]
- [Date]: [Event]
(Continue for 10+ dates)

### COMPARISONS
| Metric | This | Competitor | Industry Avg |
(Include 5-10 comparison rows)

### CONTROVERSY/DRAMA
1. [Drama point]
2. [Controversy]
(List all dramatic elements)

### FUTURE PREDICTIONS
1. [Prediction] - [Source]
2. [Prediction] - [Source]

---

## CRITICAL: QUANTITY OVER SUMMARY

Do NOT summarize. Do NOT condense. List EVERY fact, number, and quote you find.
The scriptwriter needs 80-100+ individual data points to choose from.

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
            max_tokens=8000  # Increased for exhaustive research output
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
