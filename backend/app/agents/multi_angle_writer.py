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
        """Prompt to plan 3 RADICALLY different angles for the topic"""
        return f"""You are an expert viral content strategist for Instagram Reels.

Given this topic and research, identify 3 RADICALLY DIFFERENT angles.
Each script should feel like it's about a COMPLETELY DIFFERENT STORY.

**TOPIC:** {topic}

**RESEARCH DATA:**
{research_data[:4000]}

---

## CRITICAL: SCRIPTS MUST BE COMPLETELY DIFFERENT

The 3 scripts should NOT:
- Tell the same story with different words
- Use the same timeline/narrative
- Focus on the same person
- Have similar hooks

The 3 scripts SHOULD:
- Each focus on a DIFFERENT aspect of the research
- Use DIFFERENT facts/numbers from the research
- Target DIFFERENT emotions
- Have COMPLETELY different opening hooks

---

## ANGLE CATEGORIES (Pick 3 from different categories)

**CATEGORY A - PERSON-FOCUSED:**
- The Underdog Origin Story - Childhood struggles, early failures, comeback
- The Villain Arc - Controversial decisions, enemies made, ruthless tactics
- The Mentor/Advisor - Who guided them, secret influences

**CATEGORY B - BUSINESS-FOCUSED:**
- The Hidden Revenue Model - How they ACTUALLY make money
- The Competitor Destroyer - How they're killing rivals
- The Market Timing - Why this worked NOW vs before

**CATEGORY C - DRAMATIC:**
- The Scandal/Controversy - Drama, lawsuits, harassment, firing
- The Near-Death Moment - Almost failed, crisis point, pivot
- The Secret Nobody Knows - Hidden facts most people miss

**CATEGORY D - EDUCATIONAL:**
- The Marketing Genius - Guerrilla tactics, growth hacks
- The Product Innovation - What makes it technically different
- The Market Timing - Why it worked NOW vs before

**CATEGORY E - FUTURE-FOCUSED:**
- The Industry Disruption - What industries this kills
- The 5-Year Prediction - Where this is heading
- The Global Impact - How this affects everyone

---

## OUTPUT FORMAT (JSON):
```json
{{
    "angles": [
        {{
            "name": "5-7 word angle name",
            "category": "A/B/C/D/E",
            "hook_style": "shock|question|negative|story|financial|controversy",
            "focus": "Specific aspect - be detailed (20+ words)",
            "opening_direction": "Exact hook approach (20+ words)",
            "facts_to_use": ["specific fact 1 from research", "specific fact 2", "specific fact 3"],
            "facts_to_AVOID": ["fact to NOT use - reserved for other scripts"],
            "emotional_trigger": "curiosity|fomo|outrage|inspiration|fear|greed",
            "structure": "story|revelation|comparison|timeline|listicle"
        }},
        // ... 2 more from DIFFERENT categories
    ]
}}
```

IMPORTANT: Each angle must use DIFFERENT facts from research. No overlap.

Return ONLY the JSON, no other text."""

    def _get_script_writing_prompt(
        self,
        topic: str,
        angle: Dict,
        research_data: str,
        rag_context: str,
        angle_number: int
    ) -> str:
        """Comprehensive prompt for writing a single angle's script - RADICALLY DIFFERENT each time"""

        # Different structures for each script
        # Script 1 = Controversy/Drama (most engaging first)
        # Script 2 = Story Arc (personal journey)
        # Script 3 = Business Breakdown (analytical)
        structures = {
            1: {
                "name": "THE CONTROVERSY/DRAMA",
                "format": """
[HOOK - Controversial statement or drama]
[THE SETUP - What everyone thinks they know]
[THE TWIST - What actually happened]
[THE DRAMA - Conflict, lawsuit, or scandal details]
[THE RESPONSE - How they handled it]
[THE OUTCOME - Where they are now]
[THE DEBATE - Both sides of the argument]
[ENGAGEMENT - Controversial question + CTA]
""",
                "hook_types": [
                    "Controversy/scandal hook",
                    "Lawsuit/legal drama hook",
                    "Public attack hook (They called her...)",
                    "Industry war hook (X vs Y: Who's right?)",
                    "Unpopular opinion hook (Everyone loves X, but...)"
                ]
            },
            2: {
                "name": "THE STORY ARC",
                "format": """
[HOOK - Shocking personal moment]
[BACKSTORY - Where they started, 2-3 sentences]
[THE STRUGGLE - What went wrong, specific details]
[THE TURNING POINT - "But here's where it gets interesting..."]
[THE BREAKTHROUGH - What they did differently]
[THE RESULT - Specific numbers/outcome]
[THE LESSON - What we can learn]
[ENGAGEMENT - Personal question + CTA]
""",
                "hook_types": [
                    "Personal tragedy/struggle hook",
                    "Age-based shock hook (At just X years old...)",
                    "Rejection/failure hook (They fired her for...)",
                    "Timeline hook (In X months, she went from...)",
                    "Identity hook (She was just a...)"
                ]
            },
            3: {
                "name": "THE BUSINESS BREAKDOWN",
                "format": """
[HOOK - Mind-blowing business stat]
[THE PROBLEM - What was broken in the industry]
[THE INSIGHT - What they saw that others missed]
[THE STRATEGY - Specific tactic/approach used]
[THE NUMBERS - Revenue, users, growth stats]
[THE COMPARISON - vs competitors or industry average]
[THE TAKEAWAY - Business lesson for audience]
[ENGAGEMENT - Would you use this? + CTA]
""",
                "hook_types": [
                    "Revenue/valuation shock hook",
                    "Competitor destruction hook (X is killing Y because...)",
                    "Secret strategy hook (Here's what nobody knows...)",
                    "Cost comparison hook (X costs $Y. This costs $Z.)",
                    "Market timing hook (In 2024, everything changed...)"
                ]
            }
        }

        struct = structures.get(angle_number, structures[1])

        return f"""You write viral Instagram Reel scripts. 60 seconds. Spoken out loud. For Indian tech audiences - but they're smart people who want interesting stories, not dumbed-down content.

## CRITICAL: THIS IS SCRIPT #{angle_number} - IT MUST BE COMPLETELY DIFFERENT FROM OTHER SCRIPTS

This script uses the "{struct['name']}" structure.
It must focus on: **{angle['name']}**

---

## HOW VIRAL REELS WORK

A viral reel isn't a summary. It's a JOURNEY.

You're not informing people. You're taking them somewhere. Every few seconds, you give them a reason to keep watching.

Think of it like this:
- Second 0-5: Hook them (why should I care?)
- Second 5-15: Context (what's the backstory?)
- Second 15-30: The meat (what actually happened?)
- Second 30-45: The twist (here's what most people miss...)
- Second 45-55: The bigger picture (why this changes everything)
- Second 55-60: The question (make them think/respond)

---

## THE SECRET: HOOKS THROUGHOUT

Most people think hook = first line only. Wrong.

A viral script has MULTIPLE hooks. Mini-cliffhangers that keep people watching.

After every major point, add a transition that creates curiosity:
- "But here's where it gets interesting..."
- "And then they discovered something nobody expected."
- "That's not even the crazy part."
- "But there's a problem nobody's talking about."
- "Here's what the headlines missed."

---

## SPEAK LIKE A HUMAN (LAYMAN LANGUAGE)

This will be SPOKEN. Out loud. To camera.

**No bullet points.** You can't speak bullets.
**No jargon.** Explain like you're telling a friend.
**No long sentences.** If you run out of breath reading it, it's too long.

Numbers need to be FELT, not just stated:
BAD: "99% fuel efficiency vs <1% in traditional reactors"
GOOD: "Normal reactors? They waste 99% of their fuel. This thing uses almost everything."

Make abstract things concrete. Use analogies. Compare to things people know.

---

## HAVE A PERSPECTIVE

You're not Wikipedia. You have opinions.

A summary says: "China built a thorium reactor."
A perspective says: "While everyone was arguing about nuclear safety, China quietly solved a problem we've ignored for 50 years."

Take a stance. Have a point of view. Make people think.

---

## INDIA ANGLE - ONLY IF NATURAL

Our audience is Indian. But don't force India into every script.

NATURAL India angles (use these):
- Indian founders/investors directly involved
- Direct impact on Indian users/market
- Price context in ₹ that adds genuine value
- Indian company competing or partnering

FORCED India angles (AVOID):
- "This could be useful for Indian startups" on unrelated topics
- "Indian developers should watch this" for generic news
- Random ₹ conversions that add nothing

If there's no natural connection, just tell a great story. Don't force it.

---

## TOPIC
{topic}

## THIS SCRIPT'S UNIQUE ANGLE
- **Focus:** {angle['focus']}
- **Hook Style:** {angle['hook_style']}
- **Opening Direction:** {angle['opening_direction']}
- **Facts to USE:** {', '.join(angle.get('facts_to_use', angle.get('key_facts_to_use', []))[:4])}
- **Facts to AVOID (used in other scripts):** {', '.join(angle.get('facts_to_AVOID', [])[:3])}
- **Emotional Trigger:** {angle.get('emotional_trigger', 'curiosity')}
- **Structure:** {angle.get('structure', 'story')}

## RESEARCH DATA
{research_data[:3500]}

## PATTERNS FROM WINNING SCRIPTS
{rag_context[:1500]}

---

## SCRIPT #{angle_number} STRUCTURE: {struct['name']}
{struct['format']}

---

## 5 HOOK OPTIONS FOR THIS STRUCTURE
Write 5 hooks matching these types:
1. {struct['hook_types'][0]}
2. {struct['hook_types'][1]}
3. {struct['hook_types'][2]}
4. {struct['hook_types'][3]}
5. {struct['hook_types'][4]}

**Hook Rules:**
- Under 15 words each
- Include specific numbers from RESEARCH
- Never start with company/brand name
- Pattern-interrupt immediately
- Each hook should feel DIFFERENT from the others

---

## SCRIPT RULES

**LENGTH:** 150-200 words (60 seconds when spoken)

**MANDATORY:**
- Multiple hooks THROUGHOUT (not just opening) - at least 2-3 mid-script retention triggers
- Short, punchy sentences (8-12 words max)
- One-sentence paragraphs for emphasis
- Specific numbers WITH context (make them FELT, not just stated)
- LAYMAN LANGUAGE - no jargon without explanation
- PERSPECTIVE - have an opinion, don't just summarize
- Direct question near the end (real question, not "what do you think?")
- Value-based follow CTA (not generic "follow for more")

**BANNED:**
- DESTROYED, PANICKING, TERRIFYING, CHAOS, INSANE (in caps)
- "No one is safe", "drop a", "comment if you agree"
- Bullet points (can't be spoken)
- Starting with company name
- Long paragraphs (3+ sentences)
- Technical jargon without explanation
- FORCED India angles (only natural connections)
- "What do you think?" as closing question (too generic)

---

## OUTPUT FORMAT

SCRIPT {angle_number}: {angle['name'].upper()}

5 HOOK OPTIONS:

Hook 1: [First hook type]

Hook 2: [Second hook type]

Hook 3: [Third hook type]

Hook 4: [Fourth hook type]

Hook 5: [Fifth hook type]

FULL SCRIPT:

[Write the complete 150-200 word script using {struct['name']} structure.
Start with your best hook. Use the specific facts assigned to this angle.
Make every sentence punchy and spoken-friendly.
Include 2-3 mid-script retention hooks.
Use LAYMAN LANGUAGE throughout.
Have PERSPECTIVE - don't just summarize.
Only include India angle if there's a natural connection.]

---

Write Script #{angle_number} now. Make it COMPLETELY DIFFERENT from the other scripts."""

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
