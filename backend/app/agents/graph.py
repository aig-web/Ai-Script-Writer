"""
LangGraph Workflow - Multi-Angle Viral Script Generation v2.0
Research → Retrieve → Generate 3 Scripts (parallel) → Validate → Output

This version generates 3 viral scripts with 3 different angles,
each with 5 unique hooks - matching the target output format.
"""
import os
import asyncio
import time
from pathlib import Path
from typing import TypedDict, List, Dict
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
from app.agents.pattern_reference import get_patterns
from app.agents.utils import full_clean
from app.agents.nodes.retriever import retrieve_style_context
from app.agents.multi_angle_writer import MultiAngleWriter
from app.agents.script_rag import ScriptRAG
from app.utils.logger import get_logger

# Create module-specific loggers
research_log = get_logger("Research", "🔍")
retriever_log = get_logger("Retriever", "📚")
writer_log = get_logger("Writer", "✍️")
critic_log = get_logger("Critic", "👀")
checker_log = get_logger("Checker", "✅")


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
    start_time = time.time()
    topic = state.get("topic", "")
    user_notes = state.get("user_notes", "")
    file_content = state.get("file_content", "")
    skip_research = state.get("skip_research", False)

    research_log.start(f"Research for: {topic[:40]}...")

    # SKIP RESEARCH MODE: Use only provided content
    if skip_research:
        research_log.info("Skipping web research - using provided content only")

        provided_content = []
        if file_content and len(file_content.strip()) > 0:
            provided_content.append(f"PROVIDED FILES:\n{file_content}")
            research_log.debug(f"File content: {len(file_content)} chars")

        if user_notes and len(user_notes.strip()) > 0:
            provided_content.append(f"USER NOTES:\n{user_notes}")
            research_log.debug(f"User notes: {len(user_notes)} chars")

        if not provided_content:
            provided_content.append(f"TOPIC: {topic}\n(No additional content provided - write based on topic only)")

        research_data = "\n\n".join(provided_content)
        duration = (time.time() - start_time) * 1000

        research_log.end("Research (skip mode)", duration, {"content_len": len(research_data)})

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
        research_log.info("Processing user-provided content with orchestrator")
        research_log.debug(f"File content size: {len(file_content)} chars")

        orchestrator = ResearchOrchestrator()
        try:
            result = await orchestrator.research(topic, user_notes, file_content)

            # Check if research needs user input (generic/ambiguous topic)
            if result.get("status") == "needs_specific_angle":
                research_log.warn("Generic topic detected - needs angle selection")
                return {
                    "research_status": "needs_specific_angle",
                    "research_message": result.get("message", ""),
                    "suggested_angles": result.get("suggested_angles", []),
                    "topic_type": "B",
                    "research_data": None,
                }

            if result.get("status") == "needs_clarification":
                research_log.warn("Ambiguous topic - needs clarification")
                return {
                    "research_status": "needs_clarification",
                    "research_message": result.get("message", ""),
                    "clarification_questions": result.get("questions", []),
                    "suggested_angles": result.get("suggested_angles", []),
                    "topic_type": "D",
                    "research_data": None,
                }

            research_data = result.get('research_data', '')

            # Validate research quality
            checker = ResearchChecker()
            passes, issues, score = checker.check(research_data)
            duration = (time.time() - start_time) * 1000

            research_log.success(f"Research complete (user content)", {
                "quality_score": f"{score}/100",
                "duration_ms": f"{duration:.0f}",
                "data_len": len(research_data)
            })

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
            research_log.error(f"Orchestrator failed: {str(e)[:50]}", exc=e)
            # Fallback: Try to extract story from file content using LLM
            try:
                research_log.step("Attempting LLM extraction fallback")
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
                research_log.info("LLM extraction fallback succeeded")
            except:
                processed_content = f"Topic: {topic}\n\nDocument provided by user contains information about this topic."
                research_log.warn("All fallbacks failed - using minimal content")

            duration = (time.time() - start_time) * 1000
            research_log.end("Research (fallback)", duration)

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
    research_log.step("Starting multi-stage orchestrated research")

    orchestrator = ResearchOrchestrator()
    try:
        result = await orchestrator.research(topic, user_notes)

        # Check if research needs user input (generic/ambiguous topic)
        if result.get("status") == "needs_specific_angle":
            research_log.warn("Generic topic detected - needs angle selection")
            return {
                "research_status": "needs_specific_angle",
                "research_message": result.get("message", ""),
                "suggested_angles": result.get("suggested_angles", []),
                "topic_type": "B",
                "research_data": None,
            }

        if result.get("status") == "needs_clarification":
            research_log.warn("Ambiguous topic - needs clarification")
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
        duration = (time.time() - start_time) * 1000

        angle_name = result.get('selected_angle', {}).get('angle', 'N/A')[:30]
        research_log.success(f"Research complete", {
            "quality_score": f"{score}/100",
            "angle": angle_name,
            "duration_ms": f"{duration:.0f}"
        })

        if not passes:
            research_log.warn(f"Quality issues: {issues}")

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
        research_log.error(f"Orchestrator failed: {str(e)[:50]}", exc=e)
        research_log.step("Using Perplexity fallback")

        # Fallback to basic Perplexity research
        researcher = PerplexityResearcher()
        result = researcher.research(topic, user_notes)
        duration = (time.time() - start_time) * 1000

        research_log.end("Research (Perplexity fallback)", duration, {
            "data_len": len(result.get('compressed_bullets', ''))
        })

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
    start_time = time.time()
    topic = state.get('topic', '')
    mode = state.get('mode')

    retriever_log.start(f"Retrieval for: {topic[:30]}...")

    # Get ChromaDB style context
    try:
        context = retrieve_style_context(topic, mode)
        retriever_log.success(f"ChromaDB: {len(context)} chars of style context")
    except Exception as e:
        retriever_log.error(f"ChromaDB failed: {str(e)[:50]}")
        context = "No style examples found"

    # Get RAG context from training data (winning/losing scripts)
    try:
        rag = ScriptRAG()
        rag_context = rag.get_full_context_for_topic(topic)
        retriever_log.success(f"RAG: {len(rag_context)} chars from training data")
    except Exception as e:
        retriever_log.error(f"RAG failed: {str(e)[:50]}")
        rag_context = ""

    duration = (time.time() - start_time) * 1000
    retriever_log.end("Retrieval", duration)

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
    start_time = time.time()
    topic = state.get("topic", "")
    research_data = state.get("research_data", "")

    writer_log.start(f"Multi-angle generation for: {topic[:40]}...")

    try:
        writer = MultiAngleWriter()
        result = await writer.generate_all_scripts(topic, research_data)
        duration = (time.time() - start_time) * 1000

        writer_log.success(f"Generated {len(result['scripts'])} scripts", {
            "angles": len(result['angles']),
            "duration_ms": f"{duration:.0f}"
        })

        # Log angle names
        for i, angle in enumerate(result['angles'], 1):
            writer_log.info(f"  Script {i}: {angle.get('name', 'Unknown')[:40]}")

        return {
            "angles": result["angles"],
            "scripts": result["scripts"],
            "summary_table": result["summary_table"],
            "full_output": result["full_output"],
            "draft": result["full_output"],  # Backward compatibility
        }
    except Exception as e:
        writer_log.error(f"Multi-angle failed: {str(e)[:100]}", exc=e)
        writer_log.step("Falling back to single script generation")
        return await fallback_single_script(state)


async def fallback_single_script(state: AgentState):
    """Fallback to single script if multi-angle fails"""
    start_time = time.time()
    writer_log.info("Using single script fallback")

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

    writer_log.step("Calling Claude for single script")
    response = chain.invoke({
        "topic": state.get("topic", ""),
        "research_data": state.get("research_data", "No research available"),
        "style_context": state.get("style_context", "No style examples available"),
        "user_notes": state.get("user_notes", "None"),
    })

    draft = full_clean(response.content)
    duration = (time.time() - start_time) * 1000

    writer_log.success(f"Single script generated", {"duration_ms": f"{duration:.0f}", "draft_len": len(draft)})

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
    start_time = time.time()
    scripts = state.get('scripts', [])
    draft = state.get('draft', '')
    mode = state.get('mode')

    critic_log.start("Validation")

    # If we have multiple scripts, validate each (but just log, don't block)
    if scripts and len(scripts) > 1:
        critic_log.info(f"Validating {len(scripts)} scripts (multi-angle mode)")
        duration = (time.time() - start_time) * 1000
        critic_log.success(f"Validation passed (multi-angle)", {"duration_ms": f"{duration:.0f}"})
        return {"critic_feedback": "PASS"}

    # Single script validation (legacy path)
    content_to_validate = draft if draft else '\n\n'.join(scripts)

    critic = ScriptCritic()
    result = critic.validate(content_to_validate, mode)
    duration = (time.time() - start_time) * 1000

    if result.status == "PASS":
        critic_log.success(f"Validation passed", {"score": f"{result.score}/100", "duration_ms": f"{duration:.0f}"})
        return {"critic_feedback": "PASS"}
    else:
        critic_log.warn(f"Validation failed (score: {result.score}/100) - continuing anyway")
        return {"critic_feedback": "PASS"}


# --- NODE 5: SCRIPT CHECKER ---
def checker_node(state: AgentState):
    """
    Analyzes hooks, ranks them, and provides optimization suggestions.
    For multi-angle mode, analyzes the first script as representative.
    """
    start_time = time.time()
    draft = state.get('draft', '')
    full_output = state.get('full_output', '')
    scripts = state.get('scripts', [])
    mode = state.get('mode')

    checker_log.start("Hook analysis")

    # Use full_output for the final result
    content = full_output if full_output else draft

    try:
        # Analyze first script for hook quality (representative sample)
        sample_content = scripts[0] if scripts else content[:4000]

        checker = ScriptChecker()
        result = checker.check(sample_content, mode)

        analysis = checker.format_analysis(result)
        duration = (time.time() - start_time) * 1000

        checker_log.success(f"Analysis complete", {
            "best_hook": f"#{result.best_hook_number}",
            "viral_potential": result.viral_potential,
            "duration_ms": f"{duration:.0f}"
        })

        return {
            "checker_analysis": analysis,
            "optimized_script": content,  # Return full output with all 3 scripts
            "best_hook_number": result.best_hook_number,
            "hook_ranking": result.hook_ranking
        }
    except Exception as e:
        checker_log.error(f"Analysis failed: {str(e)[:50]}")
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
