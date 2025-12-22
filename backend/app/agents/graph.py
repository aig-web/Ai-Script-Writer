"""
LangGraph Workflow - Vibhay Pro-Tier Script Generation
Research → Retrieve → Write (Claude) → Critique → Loop/Output
"""
import os
from pathlib import Path
from typing import TypedDict, Optional, List
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.enums import ScriptMode
from app.agents.prompts import INFORMATIONAL_PROMPT, LISTICAL_PROMPT
from app.agents.critic import ScriptCritic
from app.agents.script_checker import ScriptChecker
from app.agents.perplexity_researcher import PerplexityResearcher
from app.agents.nodes.retriever import retrieve_style_context


# --- SAFE STATE DEFINITION ---
class AgentState(TypedDict, total=False):
    # User Inputs
    topic: str
    mode: ScriptMode
    user_notes: str
    file_content: str
    skip_research: bool  # Skip Perplexity research, use only provided content

    # Research Data
    research_queries: List[str]
    research_data: str  # Compressed bullets
    research_sources: List[str]

    # Style Context (from ChromaDB)
    style_context: str

    # Generation
    draft: str
    critic_feedback: str
    revision_count: int

    # Checker Results
    checker_analysis: str
    optimized_script: str
    best_hook_number: int
    hook_ranking: List[int]


# --- NODE 1: PERPLEXITY RESEARCHER ---
def research_node(state: AgentState):
    """
    Uses Perplexity sonar-pro via OpenRouter for deep web research.
    Can be skipped if user wants to use only provided content.
    """
    topic = state.get("topic", "")
    user_notes = state.get("user_notes", "")
    file_content = state.get("file_content", "")
    skip_research = state.get("skip_research", False)

    # SKIP RESEARCH MODE: Use only provided content
    if skip_research:
        # Use file content and user notes as the research data
        provided_content = []

        if file_content and len(file_content.strip()) > 0:
            provided_content.append(f"PROVIDED FILES:\n{file_content}")

        if user_notes and len(user_notes.strip()) > 0:
            provided_content.append(f"USER NOTES:\n{user_notes}")

        if not provided_content:
            provided_content.append(f"TOPIC: {topic}\n(No additional content provided - write based on topic only)")

        research_data = "\n\n".join(provided_content)

        return {
            "research_data": research_data,
            "research_queries": ["[Research Skipped - Using provided content only]"],
            "research_sources": [],
            "revision_count": 0
        }

    # If user provided file content, combine with Perplexity research
    if file_content and len(file_content) > 100:
        researcher = PerplexityResearcher()
        research_result = researcher.research(topic, user_notes)

        # Combine file content with web research
        combined_research = f"""
USER PROVIDED CONTENT:
{file_content[:5000]}

WEB RESEARCH (Latest Updates from Perplexity):
{research_result['compressed_bullets']}
"""
        return {
            "research_data": combined_research,
            "research_queries": research_result["queries"],
            "research_sources": research_result["sources"],
            "revision_count": 0
        }

    # Full Perplexity research (default)
    researcher = PerplexityResearcher()
    result = researcher.research(topic, user_notes)

    return {
        "research_data": result["compressed_bullets"],
        "research_queries": result["queries"],
        "research_sources": result["sources"],
        "revision_count": 0
    }


# --- NODE 2: STYLE RETRIEVER ---
def retrieval_node(state: AgentState):
    """
    Retrieves similar scripts from ChromaDB for style reference.
    """
    context = retrieve_style_context(state['topic'], state['mode'])
    return {"style_context": context}


# --- NODE 3: CLAUDE SCRIPT WRITER ---
def writer_node(state: AgentState):
    """
    Uses Claude 3.5 Sonnet via OpenRouter for final script generation.
    Claude is the best for creative, nuanced writing.
    """
    # CLAUDE 3.5 SONNET via OpenRouter
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",  # Claude for final output
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.8,  # Slightly higher for creativity
        max_tokens=2000
    )

    # Select the appropriate Vibhay formula
    template = INFORMATIONAL_PROMPT if state['mode'] == ScriptMode.INFORMATIONAL else LISTICAL_PROMPT

    # Build the human message with all context
    human_message = """
TOPIC: {topic}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REAL-TIME RESEARCH (From Perplexity):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{research_data}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE EXAMPLES (From Training Database):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{style_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER NOTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{user_notes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITIC FEEDBACK (If revision):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{feedback}

NOW GENERATE THE SCRIPT FOLLOWING THE VIBHAY FORMULA EXACTLY.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        ("human", human_message)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "topic": state.get("topic", ""),
        "research_data": state.get("research_data", "No research available"),
        "style_context": state.get("style_context", "No style examples available"),
        "user_notes": state.get("user_notes", "None"),
        "feedback": state.get("critic_feedback", "First draft - no feedback yet")
    })

    return {"draft": response.content}


# --- NODE 4: CRITIC ---
def critic_node(state: AgentState):
    """
    Validates the script against Vibhay quality standards.
    """
    critic = ScriptCritic()
    result = critic.validate(state['draft'], state['mode'])

    if result.status == "PASS":
        return {"critic_feedback": "PASS"}
    else:
        feedback = f"FAILED CHECKS: {result.reasons}\n\nREQUIRED FIXES: {result.feedback}"
        return {
            "critic_feedback": feedback,
            "revision_count": state.get("revision_count", 0) + 1
        }


# --- NODE 5: SCRIPT CHECKER ---
def checker_node(state: AgentState):
    """
    Analyzes hooks, ranks them, and creates optimized version.
    Uses GPT-4o-mini for fast, reliable analysis.
    """
    try:
        checker = ScriptChecker()
        result = checker.check(state['draft'], state['mode'])

        # Format the analysis for display
        analysis = checker.format_analysis(result)

        return {
            "checker_analysis": analysis,
            "optimized_script": result.optimized_script,
            "best_hook_number": result.best_hook_number,
            "hook_ranking": result.hook_ranking
        }
    except Exception as e:
        # On error, return original draft
        print(f"[Checker Node Error] {e}")
        return {
            "checker_analysis": f"Analysis skipped: {str(e)[:100]}",
            "optimized_script": state['draft'],
            "best_hook_number": 1,
            "hook_ranking": [1, 2, 3, 4, 5]
        }


# --- CONDITIONAL EDGE: CONTINUE OR END ---
def should_continue(state: AgentState):
    """
    Decides whether to loop back to writer or go to checker.
    """
    if state.get("critic_feedback") == "PASS":
        return "checker"  # Go to checker for optimization

    # Max 2 revision attempts
    if state.get("revision_count", 0) >= 2:
        return "checker"  # Still go to checker even if max revisions

    return "writer"


# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("researcher", research_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)
workflow.add_node("checker", checker_node)

# Define the flow
# researcher -> retriever -> writer -> critic -> (loop or checker) -> END
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "retriever")
workflow.add_edge("retriever", "writer")
workflow.add_edge("writer", "critic")
workflow.add_conditional_edges("critic", should_continue)
workflow.add_edge("checker", END)

# Compile
app = workflow.compile()
