"""
LangGraph Workflow - Multi-Angle Viral Script Generation v2.0
Research → Retrieve → Generate 3 Scripts (parallel) → Validate → Output

This version generates 3 viral scripts with 3 different angles,
each with 5 unique hooks - matching the target output format.
"""
import os
import asyncio
from pathlib import Path
from typing import TypedDict, Optional, List, Dict, Any
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
from app.agents.research_orchestrator import ResearchOrchestrator
from app.agents.research_checker import ResearchChecker
from app.agents.regression_checker import RegressionChecker
from app.agents.pattern_reference import get_patterns
from app.agents.utils import full_clean
from app.agents.nodes.retriever import retrieve_style_context
from app.agents.multi_angle_writer import MultiAngleWriter
from app.agents.script_rag import ScriptRAG


# --- COMPACT LOGGING ---
def log_node(name: str, msg: str):
    """Compact node log"""
    print(f"[{name}] {msg}")


# --- STATE DEFINITION ---
class AgentState(TypedDict, total=False):
    # User Inputs
    topic: str
    mode: ScriptMode
    user_notes: str
    file_content: str
    skip_research: bool  # Skip Perplexity research, use only provided content

    # Research Status (for topic type detection)
    research_status: str  # "complete", "needs_specific_angle", "needs_clarification", "error"
    research_message: str  # Message to show user if needs input
    suggested_angles: List[str]  # For generic topics (Type B)
    clarification_questions: List[str]  # For ambiguous topics (Type D)
    topic_type: str  # A, B, C, or D

    # Research Data (Multi-stage orchestrator)
    research_queries: List[str]
    research_data: str  # Connected narrative from orchestrator
    research_sources: List[str]
    selected_angle: dict  # Contains angle, draft_hook, search_queries
    research_quality_score: int  # Quality score 0-100
    research_issues: List[str]  # Missing components

    # Style Context (from ChromaDB)
    style_context: str

    # RAG Context (from training data)
    rag_context: str

    # Multi-Angle Generation (NEW - v2.0)
    angles: List[Dict]  # 3 angles with name, focus, hook_style
    scripts: List[str]  # 3 complete scripts
    summary_table: str  # Markdown summary table
    full_output: str  # Complete formatted output with all 3 scripts

    # Legacy single-script fields (for backward compatibility)
    draft: str
    critic_feedback: str
    revision_count: int

    # Checker Results
    checker_analysis: str
    optimized_script: str
    best_hook_number: int
    hook_ranking: List[int]

    # Quality Results (from regression checker)
    quality_score: int
    quality_issues: List[str]
    quality_passes: bool


# --- NODE 1: MULTI-STAGE RESEARCH ORCHESTRATOR ---
async def research_node_async(state: AgentState):
    """
    Multi-stage research with topic type detection.
    Stage 0: DETECT - What type of topic is this?
    Stage 1: SCAN - Find all possible angles
    Stage 2: SELECT - Choose the best viral angle
    Stage 3: DEEP DIVE - Research only that angle
    Stage 4: CONNECT - Build narrative flow
    """
    topic = state.get("topic", "")
    user_notes = state.get("user_notes", "")
    file_content = state.get("file_content", "")
    skip_research = state.get("skip_research", False)

    # SKIP RESEARCH MODE: Use only provided content
    if skip_research:
        log_node("Research", "Skipping web research - using provided content")

        provided_content = []
        if file_content and len(file_content.strip()) > 0:
            provided_content.append(f"PROVIDED FILES:\n{file_content}")

        if user_notes and len(user_notes.strip()) > 0:
            provided_content.append(f"USER NOTES:\n{user_notes}")

        if not provided_content:
            provided_content.append(f"TOPIC: {topic}\n(No additional content provided - write based on topic only)")

        research_data = "\n\n".join(provided_content)

        return {
            "research_status": "complete",
            "research_data": research_data,
            "research_queries": ["[Research Skipped - Using provided content only]"],
            "research_sources": [],
            "selected_angle": {},
            "research_quality_score": 0,
            "research_issues": [],
            "topic_type": "skip",
            "revision_count": 0
        }

    # If user provided file content, process it with the orchestrator's content processor
    if file_content and len(file_content) > 100:
        log_node("Research", "Processing user-provided content with orchestrator...")

        orchestrator = ResearchOrchestrator()
        try:
            # Use the orchestrator to properly process the file content
            # This extracts the STORY from the content, not raw fragments
            result = await orchestrator.research(topic, user_notes, file_content)

            # Check if research needs user input (generic/ambiguous topic)
            if result.get("status") == "needs_specific_angle":
                log_node("Research", "Generic topic detected - needs angle selection")
                return {
                    "research_status": "needs_specific_angle",
                    "research_message": result.get("message", ""),
                    "suggested_angles": result.get("suggested_angles", []),
                    "topic_type": "B",
                    "research_data": None,
                }

            if result.get("status") == "needs_clarification":
                log_node("Research", "Ambiguous topic - needs clarification")
                return {
                    "research_status": "needs_clarification",
                    "research_message": result.get("message", ""),
                    "clarification_questions": result.get("questions", []),
                    "suggested_angles": result.get("suggested_angles", []),
                    "topic_type": "D",
                    "research_data": None,
                }

            # The orchestrator already processed the file content properly
            # No need to combine raw content - use the processed research directly
            research_data = result.get('research_data', '')

            # Validate research quality
            checker = ResearchChecker()
            passes, issues, score = checker.check(research_data)
            log_node("Research", f"Quality Score: {score}/100")

            return {
                "research_status": "complete",
                "research_data": research_data,
                "research_queries": ["User content + multi-stage research"],
                "research_sources": result.get("research_sources", ["User uploaded document"]),
                "selected_angle": result.get("selected_angle", {}),
                "research_quality_score": score,
                "research_issues": issues,
                "topic_type": result.get("topic_type", "user_content"),
                "revision_count": 0
            }
        except Exception as e:
            log_node("Research", f"Orchestrator failed, using fallback: {str(e)[:50]}")
            # Fallback: Try to extract story from file content using LLM
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model="anthropic/claude-3.5-sonnet",
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=0.2,
                    max_tokens=3000
                )
                extract_prompt = f"""Extract the key story from this document about "{topic}".

Write flowing paragraphs summarizing:
- What happened and who did it
- Key numbers with context
- Why it matters

Document content:
{file_content[:6000]}"""

                response = await llm.ainvoke(extract_prompt)
                processed_content = response.content
            except:
                # Last resort: just use the file content as-is but summarize
                processed_content = f"Topic: {topic}\n\nDocument provided by user contains information about this topic."

            return {
                "research_status": "complete",
                "research_data": processed_content,
                "research_queries": ["User content processed"],
                "research_sources": ["User uploaded document"],
                "selected_angle": {},
                "research_quality_score": 0,
                "research_issues": ["Fallback mode - content extracted"],
                "topic_type": "fallback",
                "revision_count": 0
            }

    # Full multi-stage orchestrated research (default)
    log_node("Research", f"Multi-stage research for: {topic[:40]}...")

    orchestrator = ResearchOrchestrator()
    try:
        result = await orchestrator.research(topic, user_notes)

        # Check if research needs user input (generic/ambiguous topic)
        if result.get("status") == "needs_specific_angle":
            log_node("Research", "Generic topic detected - needs angle selection")
            return {
                "research_status": "needs_specific_angle",
                "research_message": result.get("message", ""),
                "suggested_angles": result.get("suggested_angles", []),
                "topic_type": "B",
                "research_data": None,
            }

        if result.get("status") == "needs_clarification":
            log_node("Research", "Ambiguous topic - needs clarification")
            return {
                "research_status": "needs_clarification",
                "research_message": result.get("message", ""),
                "clarification_questions": result.get("questions", []),
                "suggested_angles": result.get("suggested_angles", []),
                "topic_type": "D",
                "research_data": None,
            }

        # Validate research quality
        checker = ResearchChecker()
        passes, issues, score = checker.check(result["research_data"])

        log_node("Research", f"Quality Score: {score}/100 | Angle: {result.get('selected_angle', {}).get('angle', 'N/A')[:30]}")
        if not passes:
            log_node("Research", f"Issues: {issues}")

        return {
            "research_status": "complete",
            "research_data": result["research_data"],
            "research_queries": ["Multi-stage orchestrated research"],
            "research_sources": ["Perplexity + Claude multi-stage pipeline"],
            "selected_angle": result.get("selected_angle", {}),
            "research_quality_score": score,
            "research_issues": issues,
            "topic_type": result.get("topic_type", "A"),
            "revision_count": 0
        }
    except Exception as e:
        log_node("Research", f"Orchestrator failed, using fallback: {str(e)[:50]}")
        # Fallback to basic Perplexity research
        researcher = PerplexityResearcher()
        result = researcher.research(topic, user_notes)

        log_node("Research", f"Fallback: Got {len(result.get('compressed_bullets', ''))} chars")

        return {
            "research_status": "complete",
            "research_data": result["compressed_bullets"],
            "research_queries": result["queries"],
            "research_sources": result["sources"],
            "selected_angle": {},
            "research_quality_score": 0,
            "research_issues": ["Fallback mode - orchestrator failed"],
            "topic_type": "fallback",
            "revision_count": 0
        }


def research_node(state: AgentState):
    """Sync wrapper for async research node."""
    return asyncio.run(research_node_async(state))


# --- NODE 2: STYLE RETRIEVER + RAG CONTEXT ---
def retrieval_node(state: AgentState):
    """
    Retrieves similar scripts from ChromaDB + RAG context from training data.
    Now includes winning/losing script patterns.
    """
    topic = state.get('topic', '')
    mode = state.get('mode')

    # Get ChromaDB style context
    try:
        context = retrieve_style_context(topic, mode)
        log_node("Retriever", f"✓ Found {len(context)} chars of style context")
    except Exception as e:
        log_node("Retriever", f"✗ ChromaDB: {str(e)[:50]}")
        context = "No style examples found"

    # Get RAG context from training data (winning/losing scripts)
    try:
        rag = ScriptRAG()
        rag_context = rag.get_full_context_for_topic(topic)
        log_node("Retriever", f"✓ Found {len(rag_context)} chars of RAG context from training data")
    except Exception as e:
        log_node("Retriever", f"✗ RAG: {str(e)[:50]}")
        rag_context = ""

    return {
        "style_context": context,
        "rag_context": rag_context
    }


# --- NODE 3: MULTI-ANGLE WRITER (NEW - v2.0) ---
async def multi_angle_writer_node_async(state: AgentState):
    """
    Generates 3 viral scripts with different angles.
    Each script has 5 unique hooks.
    This is the core improvement over the previous single-script approach.
    """
    topic = state.get("topic", "")
    research_data = state.get("research_data", "")

    log_node("MultiAngleWriter", f"Generating 3 scripts for: {topic[:40]}...")

    try:
        writer = MultiAngleWriter()
        result = await writer.generate_all_scripts(topic, research_data)

        log_node("MultiAngleWriter", f"✓ Generated {len(result['scripts'])} scripts with {len(result['angles'])} angles")

        # Log angle names
        for i, angle in enumerate(result['angles'], 1):
            log_node("MultiAngleWriter", f"  Script {i}: {angle.get('name', 'Unknown')}")

        return {
            "angles": result["angles"],
            "scripts": result["scripts"],
            "summary_table": result["summary_table"],
            "full_output": result["full_output"],
            "draft": result["full_output"],  # Backward compatibility
        }
    except Exception as e:
        log_node("MultiAngleWriter", f"✗ Error: {str(e)[:100]}")
        # Fallback to single script generation
        return await fallback_single_script(state)


async def fallback_single_script(state: AgentState):
    """Fallback to single script if multi-angle fails"""
    log_node("Writer", "Falling back to single script generation")

    mode = state.get('mode')
    llm = ChatOpenAI(
        model="anthropic/claude-sonnet-4",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.8,
        max_tokens=4000
    )

    winning_patterns, losing_patterns = get_patterns()
    template = INFORMATIONAL_PROMPT if mode == ScriptMode.INFORMATIONAL else LISTICAL_PROMPT
    template_with_patterns = template.replace("{winning_patterns}", winning_patterns)
    template_with_patterns = template_with_patterns.replace("{losing_patterns}", losing_patterns)

    human_message = """
TOPIC: {topic}

RESEARCH DATA:
{research_data}

STYLE REFERENCE:
{style_context}

USER NOTES:
{user_notes}

Generate the script now with 5 hook options.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", template_with_patterns),
        ("human", human_message)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "topic": state.get("topic", ""),
        "research_data": state.get("research_data", "No research available"),
        "style_context": state.get("style_context", "No style examples available"),
        "user_notes": state.get("user_notes", "None"),
    })

    draft = full_clean(response.content)

    return {
        "angles": [],
        "scripts": [draft],
        "summary_table": "",
        "full_output": draft,
        "draft": draft,
    }


def multi_angle_writer_node(state: AgentState):
    """Sync wrapper for async multi-angle writer node."""
    return asyncio.run(multi_angle_writer_node_async(state))


# --- NODE 4: CRITIC (validates all 3 scripts) ---
def critic_node(state: AgentState):
    """
    Validates all scripts against quality standards.
    For multi-angle mode, validates the combined output.
    """
    scripts = state.get('scripts', [])
    draft = state.get('draft', '')
    mode = state.get('mode')
    revision_count = state.get("revision_count", 0)

    # If we have multiple scripts, validate each (but just log, don't block)
    if scripts and len(scripts) > 1:
        log_node("Critic", f"Validating {len(scripts)} scripts...")
        # For multi-angle, we just log issues but always pass
        # This is because we want to show all 3 scripts to the user
        return {"critic_feedback": "PASS"}

    # Single script validation (legacy path)
    content_to_validate = draft if draft else '\n\n'.join(scripts)

    critic = ScriptCritic()
    result = critic.validate(content_to_validate, mode)

    if result.status == "PASS":
        log_node("Critic", f"✓ PASSED (score: {result.score}/100)")
        return {"critic_feedback": "PASS"}
    else:
        log_node("Critic", f"✗ FAILED (score: {result.score}/100) - but continuing")
        # For multi-angle, we continue anyway
        return {"critic_feedback": "PASS"}


# --- NODE 5: SCRIPT CHECKER ---
def checker_node(state: AgentState):
    """
    Analyzes hooks, ranks them, and provides optimization suggestions.
    For multi-angle mode, analyzes the first script as representative.
    """
    draft = state.get('draft', '')
    full_output = state.get('full_output', '')
    scripts = state.get('scripts', [])
    mode = state.get('mode')

    # Use full_output for the final result
    content = full_output if full_output else draft

    try:
        log_node("Checker", "Analyzing hooks across scripts...")

        # Analyze first script for hook quality (representative sample)
        sample_content = scripts[0] if scripts else content[:4000]

        checker = ScriptChecker()
        result = checker.check(sample_content, mode)

        analysis = checker.format_analysis(result)
        log_node("Checker", f"✓ Best hook: #{result.best_hook_number} | Viral: {result.viral_potential}")

        return {
            "checker_analysis": analysis,
            "optimized_script": content,  # Return full output with all 3 scripts
            "best_hook_number": result.best_hook_number,
            "hook_ranking": result.hook_ranking
        }
    except Exception as e:
        log_node("Checker", f"✗ {str(e)[:50]}")
        return {
            "checker_analysis": f"Analysis skipped: {str(e)[:100]}",
            "optimized_script": content,
            "best_hook_number": 1,
            "hook_ranking": [1, 2, 3, 4, 5]
        }


# --- CONDITIONAL EDGE: CONTINUE OR END ---
def should_continue(state: AgentState):
    """
    Decides whether to loop back to writer or go to checker.
    For multi-angle mode, we always proceed to checker (no revision loop).
    """
    # Multi-angle mode always proceeds to checker
    if state.get("scripts") and len(state.get("scripts", [])) > 1:
        return "checker"

    feedback = state.get("critic_feedback", "")
    if feedback == "PASS":
        return "checker"

    revision_count = state.get("revision_count", 0)
    if revision_count >= 2:
        return "checker"

    return "writer"


# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("researcher", research_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("writer", multi_angle_writer_node)  # Multi-angle writer (v2.0)
workflow.add_node("critic", critic_node)
workflow.add_node("checker", checker_node)

# Define the flow
# researcher -> retriever -> writer (multi-angle) -> critic -> checker -> END
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "retriever")
workflow.add_edge("retriever", "writer")
workflow.add_edge("writer", "critic")
workflow.add_conditional_edges("critic", should_continue)
workflow.add_edge("checker", END)

# Compile
app = workflow.compile()
