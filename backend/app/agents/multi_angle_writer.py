"""
Multi-Angle Writer - Generates 3 viral scripts with different perspectives
Each script has 5 unique hooks exploring different framings
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple, AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.script_rag import ScriptRAG


class MultiAngleWriter:
    """
    Generates 3 viral Instagram Reel scripts exploring different angles.
    Each script has 5 unique hooks.
    """

    def __init__(self):
        self.rag = ScriptRAG()

        # Use Claude for writing (best creative output)
        self.writer_llm = ChatOpenAI(
            model="anthropic/claude-sonnet-4",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.8,  # Higher for creativity
            max_tokens=8000
        )

        # Use GPT-4o-mini for angle generation (fast)
        self.planner_llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=2000
        )

    def _get_angle_planning_prompt(self, topic: str, research_data: str) -> str:
        """Prompt to plan 3 different angles for the topic"""
        return f"""You are an expert viral content strategist for Instagram Reels.

Given this topic and research, identify 3 DISTINCT angles that could each become a viral script.
Each angle should approach the topic from a completely different perspective.

**TOPIC:** {topic}

**RESEARCH DATA:**
{research_data[:3000]}

**ANGLE TYPES TO CONSIDER:**
1. The Hidden Strategy Angle - Focus on secret genius/strategy most people miss
2. The Disruption Angle - How this is beating/disrupting traditional players
3. The India Opportunity Angle - What this means for Indian audience (₹, opportunities)
4. The Future Tech Angle - Sci-fi becoming reality
5. The Business Genius Angle - Break down the brilliant business model
6. The Underdog Story Angle - Human story behind the success
7. The Controversy Angle - Ethical dilemmas or debates
8. The FOMO Angle - What you're missing out on

**OUTPUT FORMAT (JSON):**
```json
{{
    "angles": [
        {{
            "name": "Short angle name (3-5 words)",
            "hook_style": "shock|question|negative|story|financial|status",
            "focus": "What specific aspect to focus on",
            "opening_direction": "How should the hook start",
            "key_facts_to_use": ["fact1", "fact2", "fact3"],
            "emotional_trigger": "curiosity|fomo|outrage|inspiration|fear"
        }},
        // ... 2 more angles
    ]
}}
```

Return ONLY the JSON, no other text."""

    def _get_script_writing_prompt(
        self,
        topic: str,
        angle: Dict,
        research_data: str,
        rag_context: str,
        angle_number: int
    ) -> str:
        """Comprehensive prompt for writing a single angle's script"""
        return f"""You are an ELITE viral content scriptwriter for Instagram Reels.

Your scripts consistently achieve millions of views by leveraging proven psychological triggers.

## YOUR TASK
Write Script #{angle_number} for this topic, focusing on: **{angle['name']}**

## TOPIC
{topic}

## ANGLE DETAILS
- **Focus:** {angle['focus']}
- **Hook Style:** {angle['hook_style']}
- **Opening Direction:** {angle['opening_direction']}
- **Key Facts to Use:** {', '.join(angle.get('key_facts_to_use', [])[:3])}
- **Emotional Trigger:** {angle.get('emotional_trigger', 'curiosity')}

## RESEARCH DATA
{research_data[:2500]}

## PATTERNS FROM WINNING SCRIPTS
{rag_context[:2000]}

---

## THE VIRAL FORMULA STRUCTURE

### 1. HOOK CONSTRUCTION (0-3 seconds) - WRITE 5 DIFFERENT HOOKS
You MUST write 5 unique hooks exploring different framings:
- **Hook 1:** The Shocking Claim - Bold statement that challenges beliefs
- **Hook 2:** The Hidden Knowledge - "If you think X, you don't know about Y..."
- **Hook 3:** The Financial/Status - Numbers, money, or status trigger
- **Hook 4:** The Curiosity Gap - Create immediate need to know more
- **Hook 5:** The Personal Stakes - "Every [audience] is affected by this..."

**Hook Rules:**
- Under 15 words each
- Include specific numbers when possible
- Never start with company name
- Pattern-interrupt in first 2 seconds

### 2. SCRIPT STRUCTURE (60 seconds, 150-200 words)
```
[HOOK - Choose best one from your 5]
[IMMEDIATE VALIDATION - 3-8s] - Proof that supports your hook
[PATTERN INTERRUPT - 8-15s] - "But here's where it gets interesting..."
[REVELATION CASCADE - 15-30s] - 3-4 key details in rapid succession
[BUSINESS GENIUS - 30-45s] - Core strategy/mechanism explained
[BROADER IMPLICATIONS - 45-55s] - Universal principle or takeaway
[ENGAGEMENT & CTA - 55-60s] - Question + follow CTA
```

### 3. MANDATORY ELEMENTS
- [ ] "The crazy part" or "But here's where it gets interesting" transition
- [ ] Specific numbers with context (not standalone)
- [ ] Short, punchy sentences (8-12 words)
- [ ] One-sentence paragraphs for emphasis
- [ ] At least 2 mid-script retention hooks
- [ ] Direct question near the end
- [ ] Value-based follow CTA

### 4. BANNED ELEMENTS (DO NOT USE)
- Words: DESTROYED, PANICKING, TERRIFYING, CHAOS, INSANE, EXPOSED, BOMBSHELL, SHOCKED, MIND-BLOWING (in caps)
- Phrases: "no one is safe", "drop a", "comment if you agree", "big tech doesn't want"
- Bullet points (can't be spoken)
- Starting with company name
- Long paragraphs
- Technical jargon without explanation
- Generic CTAs like "follow for more"

---

## OUTPUT FORMAT

### SCRIPT {angle_number}: {angle['name'].upper()}

**5 HOOK OPTIONS:**

Hook 1: [The Shocking Claim hook]

Hook 2: [The Hidden Knowledge hook]

Hook 3: [The Financial/Status hook]

Hook 4: [The Curiosity Gap hook]

Hook 5: [The Personal Stakes hook]

**FULL SCRIPT:**
[Write the complete 150-200 word script here, using your best hook as the opening.
Use short paragraphs. Include all mandatory elements.
Make it conversational and spoken-friendly.]

---

Write Script #{angle_number} now. Make it VIRAL-WORTHY."""

    async def generate_angles(self, topic: str, research_data: str) -> List[Dict]:
        """Generate 3 distinct angles for the topic"""
        prompt = self._get_angle_planning_prompt(topic, research_data)

        response = await self.planner_llm.ainvoke([
            SystemMessage(content="You are a viral content strategist. Output only valid JSON."),
            HumanMessage(content=prompt)
        ])

        # Parse JSON from response
        content = response.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content)
            angles = data.get("angles", [])

            # Ensure we have exactly 3 angles
            if len(angles) < 3:
                # Add default angles
                default_angles = self.rag.get_angle_suggestions(topic)
                while len(angles) < 3 and default_angles:
                    angles.append({
                        "name": default_angles.pop(0)["name"],
                        "hook_style": "shock",
                        "focus": "Unique perspective on the topic",
                        "opening_direction": "Start with a bold claim",
                        "key_facts_to_use": [],
                        "emotional_trigger": "curiosity"
                    })

            return angles[:3]

        except json.JSONDecodeError as e:
            print(f"[MultiAngleWriter] JSON parse error: {e}")
            # Return default angles
            return self.rag.get_angle_suggestions(topic)

    async def write_single_script(
        self,
        topic: str,
        angle: Dict,
        research_data: str,
        rag_context: str,
        angle_number: int
    ) -> str:
        """Write a single script for one angle"""
        prompt = self._get_script_writing_prompt(
            topic, angle, research_data, rag_context, angle_number
        )

        response = await self.writer_llm.ainvoke([
            SystemMessage(content="""You are an elite viral Instagram Reels scriptwriter.
Your scripts achieve millions of views. Follow the formula exactly.
Write in a conversational, spoken style. No bullet points."""),
            HumanMessage(content=prompt)
        ])

        return response.content

    async def generate_all_scripts(
        self,
        topic: str,
        research_data: str
    ) -> Dict:
        """
        Generate 3 complete scripts with different angles.
        Returns structured output with all scripts and summary.
        """
        print(f"[MultiAngleWriter] Starting generation for: {topic}")

        # Get RAG context
        rag_context = self.rag.get_full_context_for_topic(topic)

        # Step 1: Generate angles
        print("[MultiAngleWriter] Generating 3 angles...")
        angles = await self.generate_angles(topic, research_data)

        # Step 2: Write all 3 scripts in parallel
        print("[MultiAngleWriter] Writing 3 scripts in parallel...")
        tasks = [
            self.write_single_script(topic, angle, research_data, rag_context, i + 1)
            for i, angle in enumerate(angles)
        ]

        scripts = await asyncio.gather(*tasks)

        # Step 3: Create summary table
        summary_table = self._create_summary_table(angles, scripts)

        # Step 4: Compile full output
        full_output = self._compile_full_output(topic, angles, scripts, summary_table)

        return {
            "topic": topic,
            "angles": angles,
            "scripts": scripts,
            "summary_table": summary_table,
            "full_output": full_output
        }

    async def generate_scripts_streaming(
        self,
        topic: str,
        research_data: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream the generation process with status updates.
        Yields status updates and partial results.
        """
        yield {"type": "status", "message": "Analyzing topic and generating 3 unique angles..."}

        # Get RAG context
        rag_context = self.rag.get_full_context_for_topic(topic)

        # Step 1: Generate angles
        angles = await self.generate_angles(topic, research_data)

        yield {
            "type": "angles",
            "data": [{"name": a["name"], "focus": a["focus"]} for a in angles]
        }

        # Step 2: Write scripts one by one (for streaming visibility)
        scripts = []
        for i, angle in enumerate(angles):
            yield {"type": "status", "message": f"Writing Script {i+1}: {angle['name']}..."}

            script = await self.write_single_script(
                topic, angle, research_data, rag_context, i + 1
            )
            scripts.append(script)

            yield {
                "type": "script_complete",
                "script_number": i + 1,
                "angle_name": angle["name"],
                "preview": script[:200] + "..."
            }

        # Step 3: Create summary
        yield {"type": "status", "message": "Creating summary table..."}
        summary_table = self._create_summary_table(angles, scripts)

        # Step 4: Final output
        full_output = self._compile_full_output(topic, angles, scripts, summary_table)

        yield {
            "type": "result",
            "data": {
                "topic": topic,
                "angles": angles,
                "scripts": scripts,
                "summary_table": summary_table,
                "full_output": full_output
            }
        }

    def _create_summary_table(self, angles: List[Dict], scripts: List[str]) -> str:
        """Create a markdown summary table"""
        table = """
## SUMMARY

| Script | Angle | Primary Hook |
|--------|-------|--------------|
"""
        for i, (angle, script) in enumerate(zip(angles, scripts), 1):
            # Extract first hook from script
            hook = "See script for hooks"
            if "Hook 1:" in script:
                hook_match = script.split("Hook 1:")[1].split("\n")[0].strip()
                if hook_match:
                    hook = hook_match[:60] + "..." if len(hook_match) > 60 else hook_match

            table += f"| Script {i} | {angle['name']} | \"{hook}\" |\n"

        table += """
All three scripts follow the viral formula with pattern-interrupting hooks, "the crazy part" triggers, short punchy sentences, revelation cascades, and specific numbers for credibility.
"""
        return table

    def _compile_full_output(
        self,
        topic: str,
        angles: List[Dict],
        scripts: List[str],
        summary_table: str
    ) -> str:
        """Compile the complete output - scripts only, no summary table inline"""
        output = f"""# 3 VIRAL SCRIPTS: {topic.upper()}

---

"""
        for i, (angle, script) in enumerate(zip(angles, scripts), 1):
            output += f"""
{script}

---
"""
        # Note: summary_table is returned separately in the result dict
        # Frontend displays it in a dedicated section if needed
        return output

    def _extract_first_hook(self, script: str) -> str:
        """Extract the first hook from a script"""
        lines = script.split('\n')
        for line in lines:
            if line.strip().startswith('Hook 1:'):
                return line.replace('Hook 1:', '').strip()
        return ""


# Convenience function for direct usage
async def generate_multi_angle_scripts(topic: str, research_data: str) -> Dict:
    """Generate 3 viral scripts with different angles"""
    writer = MultiAngleWriter()
    return await writer.generate_all_scripts(topic, research_data)


# Test
if __name__ == "__main__":
    async def test():
        writer = MultiAngleWriter()

        topic = "Germany's AI-powered spy cockroaches"
        research = """
        Germany's SWARM Biotactics just raised 11 million dollars.
        They put tiny electronic backpacks on live cockroaches.
        These are military-grade cyborg insects.
        Each cockroach can be remotely controlled.
        They collect real-time data and send encrypted messages.
        They can go where drones can't - collapsed buildings, underground bunkers.
        The CEO said "We're entering a decade where access, autonomy, and resilience define geopolitical advantage."
        Germany is tripling its defense budget to 175 billion dollars by 2029.
        Defense tech investment jumped from 373 million to 1 billion dollars in two years.
        """

        result = await writer.generate_all_scripts(topic, research)
        print(result["full_output"])

    asyncio.run(test())
