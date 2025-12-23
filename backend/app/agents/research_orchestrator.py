"""
Multi-stage Research Orchestrator
Mimics how a human researcher would find viral content
"""

import os
import re
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI


class ResearchOrchestrator:
    """
    Multi-stage research that finds the SINGLE most viral angle.

    Stage 0: DETECT - What type of topic is this? (Generic/Specific/Trending/Ambiguous)
    Stage 1: SCAN - What are all possible angles on this topic?
    Stage 2: SELECT - Which ONE angle is most viral-worthy?
    Stage 3: DEEP DIVE - Research ONLY that angle deeply
    Stage 4: CONNECT - Build narrative flow between facts
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="perplexity/sonar-pro",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=4000
        )

        self.selector_llm = ChatOpenAI(
            model="anthropic/claude-3.5-sonnet",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.2,
            max_tokens=2000
        )

    async def research(self, topic: str, user_notes: str = "", file_content: str = "", status_callback=None) -> Dict:
        """
        Complete multi-stage research pipeline with topic type detection.
        Handles both web research and user-provided content (PDF/files).
        """
        # If user provided their own content (PDF/file), process it differently
        if file_content and len(file_content) > 100:
            print(f"[Research] Processing user-provided content ({len(file_content)} chars)")
            return await self._process_user_content(topic, file_content, user_notes)

        # Stage 0: DETECT topic type
        if status_callback:
            status_callback("Stage 0: Detecting topic type...")
        print(f"[Research] Stage 0: DETECTING topic type for '{topic}'...")
        topic_detection = await self._stage_detect_topic_type(topic)

        print(f"[Research] Topic Type: {topic_detection['type']}")

        # Handle GENERIC topics (Type B)
        if topic_detection["type"] == "B":
            print(f"[Research] Generic topic detected. Returning suggestions...")
            return {
                "status": "needs_specific_angle",
                "topic_type": "B",
                "message": "This topic is too generic for a viral reel. Pick a specific angle with a person, company, or event.",
                "suggested_angles": topic_detection["suggestions"],
                "original_topic": topic,
                "research_data": None,
                "selected_angle": None,
            }

        # Handle AMBIGUOUS topics (Type D)
        if topic_detection["type"] == "D":
            print(f"[Research] Ambiguous topic. Needs clarification...")
            return {
                "status": "needs_clarification",
                "topic_type": "D",
                "message": "This topic is too broad. Please clarify what specific aspect you want to cover.",
                "questions": topic_detection["questions"],
                "suggested_angles": topic_detection.get("suggestions", []),
                "original_topic": topic,
                "research_data": None,
                "selected_angle": None,
            }

        # For Type A (Specific) and Type C (Trending), proceed with full research
        print(f"[Research] Topic type {topic_detection['type']} - Proceeding with research...")

        # Stage 1: SCAN for angles
        if status_callback:
            status_callback("Stage 1: Scanning for viral angles...")
        print(f"[Research] Stage 1: SCANNING for viral angles on '{topic}'...")
        scan_result = await self._stage_scan(topic)

        # Stage 2: SELECT best angle
        if status_callback:
            status_callback("Stage 2: Selecting best angle...")
        print(f"[Research] Stage 2: SELECTING most viral angle...")
        selected_angle = await self._stage_select(topic, scan_result, user_notes)

        # Stage 3: DEEP DIVE into selected angle
        if status_callback:
            status_callback("Stage 3: Deep diving into selected angle...")
        print(f"[Research] Stage 3: DEEP DIVING into '{selected_angle.get('angle', 'selected angle')}'...")
        deep_research = await self._stage_deep_dive(selected_angle)

        # Stage 4: CONNECT facts into narrative
        if status_callback:
            status_callback("Stage 4: Connecting facts into narrative...")
        print(f"[Research] Stage 4: CONNECTING facts into narrative...")
        connected_research = await self._stage_connect(deep_research, selected_angle)

        return {
            "status": "complete",
            "topic_type": topic_detection["type"],
            "selected_angle": selected_angle,
            "research_data": connected_research,
            "all_angles_considered": scan_result,
        }

    async def _stage_detect_topic_type(self, topic: str) -> Dict:
        """
        Stage 0: DETECT - What type of topic is this?
        Determines how to handle the research.
        """

        detect_prompt = f"""
You are a content strategist for Instagram Reels targeting Indian tech audiences.

## TASK: Classify this topic

**TOPIC:** "{topic}"

## TOPIC TYPES:

### TYPE A: SPECIFIC (Good for viral reels)
Definition: About a specific person, company, product, event, or announcement
Examples:
- "Sam Altman GPT-5 announcement" -> Specific person + specific event
- "Tesla FSD India launch" -> Specific company + specific event
- "Zerodha founder story" -> Specific person
- "DeepSeek vs OpenAI" -> Specific companies + conflict

### TYPE B: GENERIC (Needs transformation)
Definition: Broad concept, definition, or educational topic
Examples:
- "What is AI" -> Generic concept
- "How blockchain works" -> Educational
- "Types of machine learning" -> Generic list
- "AI in healthcare" -> Broad industry topic

### TYPE C: TRENDING (Great for viral reels)
Definition: Current news, controversy, or time-sensitive topic
Examples:
- "TikTok ban latest update" -> Current news
- "Budget 2025 tech impact" -> Time-sensitive
- "OpenAI drama today" -> Current controversy

### TYPE D: AMBIGUOUS (Needs clarification)
Definition: Single word or phrase that could go many directions
Examples:
- "Google" -> Which aspect? News? Product? Person?
- "Elon Musk" -> Which company? Which news?
- "Indian tech" -> Too broad

---

## YOUR OUTPUT:

**TOPIC TYPE:** [A / B / C / D]

**REASONING:** [One sentence explaining why this classification]

**IF TYPE B (Generic), PROVIDE 3 VIRAL-WORTHY ANGLES:**
These should transform the generic topic into specific, story-driven angles.

ANGLE 1: "[Specific person] + [specific action] + [specific detail]"
- Why it's viral: [One line]
- Search query: "[Exact query to research this]"

ANGLE 2: "[Different person/company] + [different action] + [specific detail]"
- Why it's viral: [One line]
- Search query: "[Exact query to research this]"

ANGLE 3: "[India-focused angle with specific company/person]"
- Why it's viral: [One line]
- Search query: "[Exact query to research this]"

**IF TYPE D (Ambiguous), PROVIDE:**
- 2 clarifying questions to narrow down the topic
- 3 possible specific angles based on different interpretations

**RECOMMENDATION:**
- For Type A/C: "PROCEED - Topic is ready for viral research"
- For Type B: "SUGGEST ANGLES - Let user pick a specific angle"
- For Type D: "CLARIFY - Ask user for more details"
"""

        response = await self.selector_llm.ainvoke(detect_prompt)
        return self._parse_topic_type(response.content, topic)

    def _parse_topic_type(self, content: str, original_topic: str) -> Dict:
        """Parse topic type detection response."""
        # Detect type - check for various formats
        topic_type = "A"  # Default to specific
        content_upper = content.upper()

        # Check for Type B (Generic) - multiple patterns
        type_b_patterns = [
            "TYPE:** B", "TYPE: B", "TYPE B", "**B**",
            "TOPIC TYPE:** B", "TOPIC TYPE: B"
        ]
        type_c_patterns = [
            "TYPE:** C", "TYPE: C", "TYPE C", "**C**",
            "TOPIC TYPE:** C", "TOPIC TYPE: C"
        ]
        type_d_patterns = [
            "TYPE:** D", "TYPE: D", "TYPE D", "**D**",
            "TOPIC TYPE:** D", "TOPIC TYPE: D"
        ]
        type_a_patterns = [
            "TYPE:** A", "TYPE: A", "TYPE A", "**A**",
            "TOPIC TYPE:** A", "TOPIC TYPE: A"
        ]

        if any(p in content_upper for p in type_b_patterns):
            topic_type = "B"
        elif any(p in content_upper for p in type_c_patterns):
            topic_type = "C"
        elif any(p in content_upper for p in type_d_patterns):
            topic_type = "D"
        elif any(p in content_upper for p in type_a_patterns):
            topic_type = "A"

        # Also check for explicit mentions in reasoning
        if topic_type == "A":  # Double check if default
            if "GENERIC" in content_upper and "NEEDS TRANSFORMATION" in content_upper:
                topic_type = "B"
            elif "AMBIGUOUS" in content_upper and "NEEDS CLARIFICATION" in content_upper:
                topic_type = "D"

        # Extract suggestions for Type B and D
        suggestions = []
        angle_pattern = r'ANGLE \d+:\s*"([^"]+)"'
        suggestions = re.findall(angle_pattern, content)
        if not suggestions:
            # Fallback: look for any quoted angles that are long enough
            suggestions = re.findall(r'"([^"]{30,})"', content)[:3]

        # Extract questions for Type D
        questions = []
        if topic_type == "D":
            question_patterns = [
                r'Question \d+:\s*(.+?)(?:\n|$)',
                r'- (.+\?)',
            ]
            for pattern in question_patterns:
                found = re.findall(pattern, content)
                if found:
                    questions = [q.strip() for q in found if '?' in q][:2]
                    break

        # Determine if we should proceed
        proceed = topic_type in ["A", "C"]

        return {
            "type": topic_type,
            "suggestions": suggestions,
            "questions": questions,
            "proceed": proceed,
            "raw_response": content,
            "original_topic": original_topic
        }

    async def _stage_scan(self, topic: str) -> Dict:
        """
        Stage 1: SCAN - Find all possible viral angles.
        Like a human researcher browsing headlines to find the interesting story.
        """

        scan_prompt = f"""
You are a viral content researcher looking for the MOST INTERESTING angle on a topic.

## YOUR TASK

For the topic "{topic}", find ALL possible viral-worthy angles.

## WHAT MAKES AN ANGLE VIRAL-WORTHY?

GOOD ANGLES (Look for these):
- A specific person did something unexpected (CEO, founder, employee)
- A company made a surprising move (acquisition, pivot, secret project)
- A shocking number or statistic that contradicts common belief
- A conflict/drama between companies or people
- A hidden strategy that worked brilliantly
- A failure that teaches a lesson
- Something happening RIGHT NOW (recent news, launches, announcements)
- An underdog story (small company beating giants)
- A "they don't want you to know" type insight
- India-specific impact or opportunity

BAD ANGLES (Skip these):
- Generic definitions or explanations
- Educational/how-to content without story
- Vague industry trends without specific examples
- Content from educational platforms (Coursera, GeeksforGeeks, etc.)
- Generic company descriptions without drama
- Old news (more than 2-3 months old unless historically significant)

## SEARCH STRATEGY

Search for:
1. "[topic] latest news 2024 2025"
2. "[topic] controversy drama"
3. "[topic] CEO founder announcement"
4. "[topic] India startup"
5. "[topic] shocking statistics"
6. "[topic] secret strategy"
7. "[topic] vs competitor"

## OUTPUT FORMAT

Return a list of 5-10 potential viral angles:

### ANGLE 1: [One-line description]
- **Hook Potential:** [Person/Company] + [Unexpected Action] + [Specific Detail]
- **Key Person:** [Name, Title, Company]
- **Why It's Viral:** [One sentence on why this would stop scrolling]
- **Recency:** [When did this happen?]
- **Source Type:** [News/Interview/Announcement/Report]

### ANGLE 2: [One-line description]
...

(Continue for all angles found)

### ANGLES TO AVOID (list what you found but rejected):
- [Rejected angle 1]: [Why it's not viral-worthy]
- [Rejected angle 2]: [Why it's not viral-worthy]

---

## TOPIC TO RESEARCH:

{topic}
"""

        response = await self.llm.ainvoke(scan_prompt)
        return {"raw_scan": response.content, "topic": topic}

    async def _stage_select(self, topic: str, scan_result: Dict, user_notes: str) -> Dict:
        """
        Stage 2: SELECT - Choose the SINGLE most viral angle.
        Uses Claude to analyze and pick the best option.
        """

        select_prompt = f"""
You are a viral content strategist. Your job is to pick the SINGLE BEST angle for an Instagram Reel.

## SCAN RESULTS (All angles found):

{scan_result['raw_scan']}

## USER'S NOTES (Consider these preferences):

{user_notes if user_notes else "No specific preferences."}

## SELECTION CRITERIA

Rate each angle on:

| Criteria | Weight | Description |
|----------|--------|-------------|
| HOOK STRENGTH | 30% | Can this become a scroll-stopping first line? |
| SPECIFICITY | 25% | Does it have specific names, numbers, dates? |
| RECENCY | 20% | Is this fresh news (within 2-3 months)? |
| STORY ARC | 15% | Can this sustain a 45-60 second narrative? |
| INDIA RELEVANCE | 10% | Does it connect to Indian audience? |

## YOUR TASK

1. Score each angle (1-10) on all criteria
2. Calculate weighted score
3. Pick the SINGLE BEST angle
4. Explain why this angle will outperform others

## OUTPUT FORMAT

### ANGLE SCORING

| Angle | Hook | Specificity | Recency | Story Arc | India | TOTAL |
|-------|------|-------------|---------|-----------|-------|-------|
| 1. [Name] | X/10 | X/10 | X/10 | X/10 | X/10 | X/10 |
| 2. [Name] | X/10 | X/10 | X/10 | X/10 | X/10 | X/10 |
...

### SELECTED ANGLE

**Winner:** [Angle name]

**The Hook (Draft):** "[Person/Company] + [Action] + [Specific Detail]"

**Key Person to Focus On:**
- Name: [Full name]
- Title: [Position]
- Company: [Organization]
- Why them: [Why they anchor this story]

**The Story Arc:**
1. Hook: [What grabs attention]
2. Setup: [Context needed]
3. Reveal: [The main insight/drama]
4. Proof: [Evidence/numbers]
5. Implication: [Why it matters]

**Specific Search Queries for Deep Dive:**
1. "[Exact query to find more on this angle]"
2. "[Exact query to find quotes from key person]"
3. "[Exact query to find India connection]"
4. "[Exact query to find specific numbers]"

**Why This Angle Wins:**
[2-3 sentences on why this will outperform other angles]
"""

        response = await self.selector_llm.ainvoke(select_prompt)

        # Parse the response to extract key info
        content = response.content

        # Extract the angle, hook, and search queries
        return {
            "raw_selection": content,
            "angle": self._extract_between(content, "**Winner:**", "\n"),
            "draft_hook": self._extract_between(content, '**The Hook (Draft):**', "\n"),
            "search_queries": self._extract_search_queries(content),
            "topic": topic
        }

    async def _stage_deep_dive(self, selected_angle: Dict) -> Dict:
        """
        Stage 3: DEEP DIVE - Research ONLY the selected angle.
        Multiple targeted searches to get deep, specific information.
        """

        queries = selected_angle.get('search_queries', [])
        angle = selected_angle.get('angle', selected_angle.get('topic', ''))

        deep_dive_prompt = f"""
You are doing a DEEP DIVE research on ONE specific angle for a viral Instagram Reel.

## THE SELECTED ANGLE:

{selected_angle['raw_selection']}

## YOUR MISSION

Find EVERYTHING needed to write a compelling 45-60 second script on this SPECIFIC angle.

## CRITICAL: WHAT MAKES VIRAL SCRIPTS DIFFERENT

Human-written viral scripts have these elements that AI usually misses:

1. **CONTEXT/BACKSTORY (WHY NOW?)** - What event triggered this? Why is this happening NOW?
   - Example: "Since Russia invaded Ukraine, Germany changed defense strategy"
   - NOT: Just jumping to "Company X raised $Y"

2. **BEFORE/AFTER NUMBERS** - Show the CHANGE, not just a number
   - Example: "373M → 1B = 170% increase in 2 years"
   - NOT: "They raised €13 million"

3. **CONTRAST DATA** - Traditional/Old vs New approach
   - Example: "Traditional drones: cost thousands, need maintenance, break. Cockroaches: operate in darkness, don't need GPS"
   - NOT: Just listing features

4. **ESCALATION DATA** - Small → Big implications
   - Example: Company ($13M) → Industry ($175B) → Global ("Every military will want this")
   - NOT: Staying at company level only

## WHAT TO SEARCH FOR:

### 1. THE BACKSTORY/CONTEXT (CRITICAL - MOST SCRIPTS MISS THIS)
   - What TRIGGERED this? What event, policy, or crisis made this happen?
   - What was the world/industry like BEFORE this?
   - Why is this company/person doing this NOW vs 2 years ago?
   - What changed in the market/geopolitics/technology?

   SEARCH FOR: "[topic] why now", "[topic] triggered by", "[topic] after [event]", "[topic] in response to"

### 2. BEFORE/AFTER NUMBERS (Not just standalone numbers)
   - What was the number BEFORE? What is it NOW?
   - Calculate the percentage change
   - Find industry-level numbers, not just company-level
   - Find budget/funding trajectory over time

   SEARCH FOR: "[industry] investment 2022 vs 2024", "[topic] growth rate", "[topic] market size change"

### 3. CONTRAST DATA (Old Way vs New Way)
   - What's the traditional/old approach?
   - What are its PROBLEMS? (cost, maintenance, limitations)
   - How does the new approach solve these?
   - What can the new do that old CAN'T?

   SEARCH FOR: "[new thing] vs traditional", "[old approach] problems", "[new approach] advantages"

### 4. ESCALATION DATA (Small → Medium → Big)
   - Company-level stat (funding, revenue, etc.)
   - Industry-level stat (market size, total investment)
   - Global implication (who else will want this, future predictions)

   SEARCH FOR: "[industry] market size 2029", "[topic] global adoption", "[topic] future predictions"

### 5. THE KEY PERSON
   - Full background (education, previous roles, achievements)
   - Recent quotes (exact words in quotation marks)
   - The specific action/announcement they made

### 6. DIRECT QUOTES
   - Find 2-3 exact quotes from the key person
   - Find 1 quote about why this matters/what changed

## OUTPUT FORMAT

### BACKSTORY/CONTEXT (WHY NOW?) - CRITICAL

**The Trigger Event:** [What event/crisis/change triggered this?]
**What Changed:** [What was different before? What shifted?]
**Timeline:** [When did the trigger happen? When did the response start?]
**Search Queries Used:** [List queries that found this context]

Example format:
"Since [TRIGGER EVENT] in [DATE], [THING] changed. Before this, [OLD STATE]. Now, [NEW STATE]. This is why [COMPANY/PERSON] is [ACTION]."

### BEFORE/AFTER NUMBERS - CRITICAL

| Metric | BEFORE | AFTER | CHANGE | TIME PERIOD |
|--------|--------|-------|--------|-------------|
| [Metric 1] | [Old number] | [New number] | [X% increase/Xx bigger] | [Years] |
| [Metric 2] | [Old number] | [New number] | [X% increase/Xx bigger] | [Years] |
| [Metric 3] | [Old number] | [New number] | [X% increase/Xx bigger] | [Years] |

### CONTRAST DATA (OLD VS NEW) - CRITICAL

**THE OLD WAY:**
| Aspect | Traditional Approach | Problem/Limitation |
|--------|---------------------|-------------------|
| Cost | [Specific amount] | [Why it's a problem] |
| Maintenance | [What's required] | [Why it's a problem] |
| Capability | [What it can do] | [What it CAN'T do] |

**THE NEW WAY:**
| Aspect | New Approach | Advantage |
|--------|-------------|-----------|
| Cost | [Specific amount] | [Comparison to old] |
| Maintenance | [What's required] | [Why it's better] |
| Capability | [What it can do] | [What old CAN'T do] |

**One-liner contrast:** "[Old] costs [X], needs [Y], breaks. [New]? [Advantage 1]. [Advantage 2]. [Advantage 3]."

### ESCALATION DATA (SMALL → BIG) - CRITICAL

| Level | Stat | Implication |
|-------|------|-------------|
| COMPANY | [Company-level number] | [What this means] |
| INDUSTRY | [Industry-level number] | [What this means] |
| GLOBAL | [Global projection/implication] | [Future prediction] |

**Escalation narrative:** "This company raised [X]. But the industry is now [Y]. And [global implication - who else will want this]."

### KEY PERSON PROFILE

| Field | Detail |
|-------|--------|
| Name | [Full name] |
| Title | [Current position] |
| Company | [Organization] |
| Background | [1-2 line credentials] |
| The Action | [What they specifically did] |
| When | [Exact date if possible] |

### DIRECT QUOTES (Exact words only)

1. "[Quote 1]" - [Person], [Context]
2. "[Quote 2]" - [Person], [Context]
3. "[Quote 3]" - [Person], [Context]

### INDIA ANGLE

- **Direct Impact:** [How this affects Indians]
- **Cost Context:** [Pricing in Rs.]
- **Opportunity:** [What Indians can do with this]

### SOURCES

1. [Source 1 - Type: News/Interview/Report]
2. [Source 2 - Type: News/Interview/Report]
3. [Source 3 - Type: News/Interview/Report]
"""

        response = await self.llm.ainvoke(deep_dive_prompt)
        return {"raw_research": response.content, "angle": angle}

    async def _stage_connect(self, deep_research: Dict, selected_angle: Dict) -> str:
        """
        Stage 4: CONNECT - Build narrative connections between facts.
        This ensures the script will flow naturally from one point to the next.
        """

        connect_prompt = f"""
You are a narrative architect. Organize research facts into a connected story flow.

## THE RESEARCH:

{deep_research['raw_research']}

## THE SELECTED ANGLE:

{selected_angle['raw_selection']}

## KEY PRINCIPLES (Apply flexibly)

1. **CONTEXT FIRST** - Explain WHY this is happening before WHAT happened
2. **NUMBERS WITH MEANING** - Show before→after, not standalone numbers
3. **CONTRAST** - Compare old way vs new way when applicable
4. **ESCALATION** - Zoom from company → industry → global
5. **SHARP INSIGHT** - Specific business reframe, not generic philosophy

## ORGANIZE THE RESEARCH INTO:

**HOOK OPTIONS (3 variations):**
- One using "While everyone's focused on X, Y quietly happened..."
- One using person/company + unexpected action
- One with India angle if applicable

**CONTEXT/BACKSTORY:**
What triggered this? Why is this happening NOW?

**NUMBERS WITH CONTEXT:**
Before → After with percentage change or comparison

**THE STORY:**
Who did what, explained simply

**CONTRAST (if applicable):**
Old approach problems vs new approach advantages

**ESCALATION:**
Company stat → Industry stat → Global implication

**INSIGHT:**
Sharp, specific reframe (not generic "this changes everything")

**INDIA ANGLE:**
How this affects Indian audience (with Rs. if applicable)

**OPEN QUESTION:**
Genuine question that prompts thought
- "Would you invest in this kind of technology?"
- "The question is: Will [category] survive this?"

## OUTPUT FORMAT

Provide the organized research in these sections (be flexible with format):

**HOOK OPTIONS:** 3 different hook angles

**CONTEXT:** The backstory/trigger

**NUMBERS:** Key stats with context

**THE STORY:** Core narrative

**CONTRAST:** Old vs new (if applicable)

**ESCALATION:** Bigger picture stats

**INSIGHT:** Sharp reframe

**INDIA ANGLE:** Local relevance

**QUESTION:** Engagement prompt
"""

        response = await self.selector_llm.ainvoke(connect_prompt)
        return response.content

    def _extract_between(self, text: str, start: str, end: str) -> str:
        """Extract text between two markers."""
        try:
            start_idx = text.find(start) + len(start)
            end_idx = text.find(end, start_idx)
            return text[start_idx:end_idx].strip()
        except:
            return ""

    def _extract_search_queries(self, text: str) -> List[str]:
        """Extract search queries from selection output."""
        queries = []
        lines = text.split('\n')
        in_queries = False
        for line in lines:
            if 'Search Queries' in line or 'Deep Dive' in line:
                in_queries = True
                continue
            if in_queries and line.strip().startswith('"'):
                query = line.strip().strip('"').strip('1234567890.').strip()
                if query:
                    queries.append(query)
            if in_queries and line.strip().startswith('**Why'):
                break
        return queries[:4]  # Max 4 queries

    async def _process_user_content(self, topic: str, content: str, user_notes: str) -> Dict:
        """
        Process user-uploaded PDF/file content.
        Extract the STORY, not fragments. This fixes the word-fragment issue.
        """

        extract_prompt = f"""
You're a researcher preparing content for a viral Instagram Reel script.

The user uploaded a document about: {topic}

Your job: Extract the STORY from this content. Not fragments. Not bullet points. The narrative.

## WHAT TO EXTRACT

**The Core Story:**
What happened? Who did it? Why does it matter?
Write this as a flowing paragraph, not bullets.

**The Trigger (Why Now):**
What event or milestone made this newsworthy?
When did it happen?

**The Key Numbers (With Context):**
Don't just list numbers. Explain what they mean.
Bad: "99% fuel efficiency"
Good: "Traditional reactors waste 99% of their fuel. This one uses almost everything."

**The Contrast (Old vs New):**
What was the old way? What's broken about it?
What's the new way? Why is it better?

**The Bigger Picture:**
Why should anyone care? What does this mean for the world?

**Quotable Moments:**
Any statements from people involved that we can quote?

**The Controversy/Tension (if any):**
Is there debate? Opposition? Risk? Drama?

---

## DOCUMENT CONTENT:

{content[:8000]}

---

## USER NOTES:

{user_notes if user_notes else "None provided"}

---

## OUTPUT FORMAT

Write flowing paragraphs, not bullet points. This will be used to write a script someone will SPEAK.

**THE STORY:**
[2-3 paragraphs explaining what happened and why it matters]

**WHY NOW:**
[1 paragraph on the trigger/timing]

**THE NUMBERS (explained simply):**
[Numbers with plain English context, written as sentences not bullets]

**OLD WAY VS NEW WAY:**
[Contrast written conversationally]

**BIGGER PICTURE:**
[Why this matters beyond the immediate story]

**QUOTES:**
[Any direct quotes with attribution]

**TENSION/DRAMA:**
[Any controversy or stakes]
"""

        response = await self.selector_llm.ainvoke(extract_prompt)

        return {
            "status": "complete",
            "topic_type": "user_content",
            "research_data": response.content,
            "selected_angle": {"angle": topic, "source": "user_uploaded_content"},
            "research_sources": ["User uploaded document"],
        }
