"""
Script RAG System - Retrieval Augmented Generation for Viral Scripts
Uses winning/losing script patterns for better generation
"""
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI

from app.agents.training_data_loader import TrainingDataLoader, ParsedScript


class ScriptRAG:
    """
    RAG system for viral script generation.
    Retrieves relevant winning scripts and patterns to guide generation.
    """

    def __init__(self):
        self.loader = TrainingDataLoader()
        self.winning_scripts: List[ParsedScript] = []
        self.losing_scripts: List[ParsedScript] = []
        self.winning_patterns: Dict = {}
        self.losing_patterns: Dict = {}

        # Load data
        self._load_data()

        # LLM for similarity matching (when vector DB not available)
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=2000
        )

    def _load_data(self):
        """Load all training data"""
        print("[ScriptRAG] Loading training data...")
        self.winning_scripts = self.loader.load_winning_scripts()
        self.losing_scripts = self.loader.load_losing_scripts()
        self.winning_patterns = self.loader.get_winning_patterns()
        self.losing_patterns = self.loader.get_losing_patterns()
        print(f"[ScriptRAG] Loaded {len(self.winning_scripts)} winning, {len(self.losing_scripts)} losing scripts")

    def get_similar_winning_scripts(self, topic: str, n: int = 3) -> List[ParsedScript]:
        """
        Find winning scripts most similar to the given topic.
        Uses keyword matching and category similarity.
        """
        if not self.winning_scripts:
            return []

        # Simple keyword matching for now
        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())

        scored_scripts = []
        for script in self.winning_scripts:
            score = 0
            title_lower = script.title.lower()
            full_lower = script.full_text.lower()

            # Title match (highest weight)
            for word in topic_words:
                if word in title_lower:
                    score += 10
                elif word in full_lower:
                    score += 2

            # Category matching
            if "ai" in topic_lower or "tech" in topic_lower:
                if any(k in title_lower for k in ["ai", "tech", "app", "device", "robot"]):
                    score += 5
            if "business" in topic_lower or "startup" in topic_lower:
                if any(k in title_lower for k in ["business", "startup", "company", "founder", "crore"]):
                    score += 5
            if "india" in topic_lower:
                if script.has_india_angle:
                    score += 5

            scored_scripts.append((script, score))

        # Sort by score and return top n
        scored_scripts.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_scripts[:n]]

    def get_hook_examples(self, topic: str, n: int = 5) -> List[str]:
        """Get example hooks from similar winning scripts"""
        similar = self.get_similar_winning_scripts(topic, n)
        hooks = []
        for script in similar:
            if script.hooks:
                hooks.append(script.hooks[0])  # Get first hook
        return hooks[:n]

    def get_script_structure_examples(self, topic: str) -> str:
        """Get structural examples from winning scripts"""
        similar = self.get_similar_winning_scripts(topic, 2)
        if not similar:
            return ""

        examples = []
        for script in similar:
            example = f"""
### Example: {script.title}
**Hook Style:** {', '.join(script.hook_types[:2]) if script.hook_types else 'general'}
**Sample Hook:** {script.hooks[0][:150] if script.hooks else 'N/A'}...

**Key Elements Used:**
- Crazy part trigger: {'Yes' if script.has_crazy_part else 'No'}
- Transition hooks: {'Yes' if script.has_transition_hooks else 'No'}
- Numbers/stats: {'Yes' if script.has_numbers else 'No'}
- Direct quotes: {'Yes' if script.has_quotes else 'No'}
- India angle: {'Yes' if script.has_india_angle else 'No'}

**CTA Style:** {script.cta_type}
"""
            examples.append(example)

        return "\n".join(examples)

    def get_patterns_summary(self) -> str:
        """Get a summary of winning patterns for prompt injection"""
        wp = self.winning_patterns

        if not wp.get("avg_hook_count"):
            return ""

        summary = f"""
## PATTERNS FROM {len(self.winning_scripts)} WINNING SCRIPTS

**Hook Statistics:**
- Average hooks per script: {wp.get('avg_hook_count', 0):.1f}
- Scripts with "crazy part": {wp.get('crazy_part_rate', 0)*100:.0f}%
- Scripts with transition hooks: {wp.get('transition_rate', 0)*100:.0f}%
- Scripts with India angle: {wp.get('india_angle_rate', 0)*100:.0f}%
- Scripts with specific numbers: {wp.get('numbers_rate', 0)*100:.0f}%
- Scripts with direct quotes: {wp.get('quotes_rate', 0)*100:.0f}%
- Average word count: {wp.get('avg_word_count', 0):.0f} words

**Common Hook Types:** {', '.join(f"{k} ({v})" for k, v in sorted(wp.get('common_hook_types', {}).items(), key=lambda x: -x[1])[:5])}

**Common CTA Types:** {', '.join(f"{k} ({v})" for k, v in sorted(wp.get('common_cta_types', {}).items(), key=lambda x: -x[1])[:3])}

**Top Performing Hook Examples:**
{chr(10).join(f'- "{h[:100]}..."' for h in wp.get('sample_hooks', [])[:5])}
"""
        return summary

    def get_losing_patterns_warning(self) -> str:
        """Get warning about patterns to avoid from losing scripts"""
        lp = self.losing_patterns

        if not lp.get("avg_hook_count"):
            return ""

        # Compare with winning
        wp = self.winning_patterns

        warnings = ["## PATTERNS FROM LOSING SCRIPTS (AVOID THESE)"]

        # Find differences
        if lp.get("crazy_part_rate", 0) < wp.get("crazy_part_rate", 0):
            warnings.append(f"- Missing 'crazy part' trigger (losing: {lp.get('crazy_part_rate', 0)*100:.0f}% vs winning: {wp.get('crazy_part_rate', 0)*100:.0f}%)")

        if lp.get("transition_rate", 0) < wp.get("transition_rate", 0):
            warnings.append(f"- Missing transition hooks (losing: {lp.get('transition_rate', 0)*100:.0f}% vs winning: {wp.get('transition_rate', 0)*100:.0f}%)")

        warnings.append("""
**Common Issues in Losing Scripts:**
- Starting with company name instead of hook
- Too much explanation before the hook
- Missing mid-script retention triggers
- Generic CTAs without value proposition
- Overly long sentences
- Technical jargon without explanation
""")

        return "\n".join(warnings)

    def get_full_context_for_topic(self, topic: str) -> str:
        """Get comprehensive RAG context for a topic"""
        context_parts = []

        # Add similar script examples
        examples = self.get_script_structure_examples(topic)
        if examples:
            context_parts.append("## SIMILAR WINNING SCRIPTS FOR REFERENCE")
            context_parts.append(examples)

        # Add winning patterns
        patterns = self.get_patterns_summary()
        if patterns:
            context_parts.append(patterns)

        # Add losing patterns warning
        warnings = self.get_losing_patterns_warning()
        if warnings:
            context_parts.append(warnings)

        return "\n\n".join(context_parts)

    def get_angle_suggestions(self, topic: str) -> List[Dict[str, str]]:
        """
        Suggest 3 different angles based on winning script patterns.
        Returns list of angle suggestions with hook types.
        """
        # Analyze topic keywords
        topic_lower = topic.lower()

        # Define angle templates based on winning patterns
        angle_templates = [
            {
                "name": "The Hidden Strategy Angle",
                "description": "Focus on the secret/genius strategy behind the topic",
                "hook_style": "shock",
                "template": "Reveal the hidden genius/strategy that most people miss",
                "example_prefix": "Here's the hidden evil genius strategy...",
            },
            {
                "name": "The Disruption Angle",
                "description": "How this is disrupting/changing an industry",
                "hook_style": "shock",
                "template": "Show how this is beating/disrupting traditional players",
                "example_prefix": "While everyone was focused on X, this quietly...",
            },
            {
                "name": "The India Opportunity Angle",
                "description": "What this means for India/Indian audience",
                "hook_style": "financial",
                "template": "Connect to Indian market, ₹ amounts, opportunities",
                "example_prefix": "But here's why this is HUGE for India...",
            },
            {
                "name": "The Future Tech Angle",
                "description": "How this represents the future happening now",
                "hook_style": "story",
                "template": "Position as sci-fi becoming reality",
                "example_prefix": "This isn't science fiction anymore. It's happening right now.",
            },
            {
                "name": "The Business Genius Angle",
                "description": "Break down the brilliant business strategy",
                "hook_style": "financial",
                "template": "Analyze the business model and revenue potential",
                "example_prefix": "Let me break down the genius business model...",
            },
            {
                "name": "The Underdog Story Angle",
                "description": "Focus on the founder/company journey",
                "hook_style": "story",
                "template": "Tell the human story behind the success",
                "example_prefix": "This person started with nothing. Today...",
            },
        ]

        # Select 3 most relevant angles based on topic
        selected = []

        # Always include one of these based on topic type
        if any(k in topic_lower for k in ["ai", "tech", "device", "robot", "app"]):
            selected.append(angle_templates[3])  # Future Tech
            selected.append(angle_templates[0])  # Hidden Strategy
            selected.append(angle_templates[2])  # India Opportunity
        elif any(k in topic_lower for k in ["business", "company", "startup", "founder"]):
            selected.append(angle_templates[4])  # Business Genius
            selected.append(angle_templates[5])  # Underdog Story
            selected.append(angle_templates[1])  # Disruption
        elif any(k in topic_lower for k in ["india", "indian"]):
            selected.append(angle_templates[2])  # India Opportunity
            selected.append(angle_templates[4])  # Business Genius
            selected.append(angle_templates[0])  # Hidden Strategy
        else:
            # Default selection
            selected.append(angle_templates[0])  # Hidden Strategy
            selected.append(angle_templates[1])  # Disruption
            selected.append(angle_templates[2])  # India Opportunity

        return selected[:3]


# Test
if __name__ == "__main__":
    rag = ScriptRAG()

    print("\n=== TESTING RAG ===")
    topic = "AI-powered spy cockroaches"

    print(f"\nTopic: {topic}")
    print("\n--- Similar Scripts ---")
    similar = rag.get_similar_winning_scripts(topic, 3)
    for s in similar:
        print(f"- {s.title}")

    print("\n--- Hook Examples ---")
    hooks = rag.get_hook_examples(topic, 3)
    for h in hooks:
        print(f"- {h[:80]}...")

    print("\n--- Angle Suggestions ---")
    angles = rag.get_angle_suggestions(topic)
    for a in angles:
        print(f"- {a['name']}: {a['description']}")

    print("\n--- Patterns Summary ---")
    print(rag.get_patterns_summary()[:500])
