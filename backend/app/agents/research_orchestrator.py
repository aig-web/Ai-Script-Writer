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
            max_tokens=8000  # Increased for exhaustive research output
        )

        self.selector_llm = ChatOpenAI(
            model="anthropic/claude-3.5-sonnet",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.2,
            max_tokens=6000  # Increased to preserve all research data
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
You are doing an EXHAUSTIVE DEEP DIVE research on ONE specific angle for a viral Instagram Reel.

## THE SELECTED ANGLE:

{selected_angle['raw_selection']}

## YOUR MISSION

Find EVERYTHING - gather 80-120+ individual facts, data points, quotes, and insights. The scriptwriter needs ABUNDANT raw material to choose from. Don't summarize - collect EVERYTHING you can find.

## CRITICAL: QUANTITY MATTERS

Previous research gave only 15-25 facts. That's NOT ENOUGH. We need:
- 30-50 specific numbers/statistics
- 15-20 direct quotes from different people
- 20-30 surprising/hook-worthy facts
- 10-15 comparison/contrast points
- 10-15 India-specific data points
- Multiple timelines and historical context points

## WHAT TO SEARCH FOR (Be exhaustive):

### 1. NUMBERS & STATISTICS (Find 30-50 different numbers)
Search for and list EVERY number you can find:
- Revenue figures (current, historical, projected)
- User counts / customer counts
- Market size (current, projected 2025, 2030)
- Growth rates (YoY, MoM, total)
- Funding amounts (all rounds)
- Valuations (current, previous)
- Employee counts
- Cost savings / efficiency gains
- Speed improvements
- Percentage changes
- Rankings and positions
- Comparisons to competitors
- Time durations (how long things took)
- Prices and costs
- Investment amounts
- Any other quantifiable data

### 2. DIRECT QUOTES (Find 15-20 quotes)
Search for quotes from:
- The CEO/Founder
- Other executives
- Investors
- Industry analysts
- Competitors
- Customers/Users
- Media commentators
- Government officials (if relevant)
- Researchers/Experts

### 3. HOOK-WORTHY FACTS (Find 20-30 surprising facts)
- Counter-intuitive facts
- "Most people don't know..." facts
- Failure/comeback stories
- Secret strategies revealed
- Behind-the-scenes insights
- Controversial decisions
- Unexpected connections
- Timing coincidences
- David vs Goliath moments
- First-ever achievements
- Record-breaking stats

### 4. BACKSTORY & CONTEXT (Find 10-15 context points)
- What triggered this?
- What was happening before?
- Why now specifically?
- What failed attempts preceded this?
- What crisis/opportunity drove this?
- Historical parallels
- Industry shifts that enabled this

### 5. COMPARISONS & CONTRASTS (Find 10-15 comparisons)
- Old way vs new way
- This company vs competitors
- Before vs after
- Expected vs actual
- Industry average vs this company
- Cost comparisons
- Speed comparisons
- Quality comparisons

### 6. INDIA-SPECIFIC DATA (Only if naturally relevant)
NOTE: Only include India angle if there's a GENUINE connection:
- Indian founders/investors directly involved
- Direct impact on Indian users/market
- Indian company competing or partnering
- Significant pricing/accessibility angle for India
DO NOT force India angle if there's no natural connection.
If relevant, find:
- Indian market size
- Indian user numbers
- Pricing in INR (₹)
- Indian competitors
- Indian employees/offices

### 7. PEOPLE PROFILES (Multiple people, not just one)
For EACH key person involved, find:
- Full name and current title
- Previous roles/companies
- Education background
- Notable achievements
- Age (if public)
- Net worth (if relevant)
- Specific quotes

### 8. TIMELINE & MILESTONES (Find 10-15 dates)
- Founding date
- Key product launches
- Funding rounds dates
- Major announcements
- Pivot points
- Crisis moments
- Recovery milestones
- Future planned dates

### 9. CONTROVERSY & DRAMA (Find 5-10 dramatic elements)
- Conflicts with competitors
- Internal drama
- Public criticism
- Regulatory issues
- Failed products/features
- Leadership changes
- Lawsuits or legal issues

### 10. FUTURE PREDICTIONS (Find 5-10 predictions)
- Expert predictions
- Company roadmap
- Industry forecasts
- Analyst expectations
- Potential risks
- Growth projections

---

## OUTPUT FORMAT (Be exhaustive - aim for 3000+ words of raw research)

### RAW NUMBERS & STATISTICS (List 30-50)
1. [Number] - [What it represents] - [Source/Context]
2. [Number] - [What it represents] - [Source/Context]
3. ...
(Continue until you have 30-50 different numbers)

### DIRECT QUOTES (List 15-20)
1. "[Exact quote]" — [Person Name], [Title], [Context/When said]
2. "[Exact quote]" — [Person Name], [Title], [Context/When said]
3. ...
(Continue until you have 15-20 different quotes)

### HOOK-WORTHY FACTS (List 20-30)
1. [Surprising fact with specific detail]
2. [Counter-intuitive insight]
3. ...
(Continue until you have 20-30 facts)

### BACKSTORY & CONTEXT
- **Origin Story:** [How this started - detailed]
- **Trigger Event:** [What made this happen now]
- **Before State:** [What was the situation before]
- **Key Turning Points:** [List 3-5 pivotal moments]
- **Timeline:**
  - [Date]: [Event]
  - [Date]: [Event]
  - (List 10+ timeline entries)

### COMPARISON DATA

**VS COMPETITORS:**
| Metric | This Company | Competitor 1 | Competitor 2 | Industry Avg |
|--------|--------------|--------------|--------------|--------------|
| [Metric] | [Value] | [Value] | [Value] | [Value] |
(Include 5-10 comparison rows)

**OLD VS NEW:**
| Aspect | Old Way | New Way | Improvement |
|--------|---------|---------|-------------|
| [Aspect] | [Old] | [New] | [X% better] |
(Include 5-10 rows)

### KEY PEOPLE PROFILES

**Person 1: [Name]**
- Title: [Current position]
- Background: [Education, previous roles]
- Key Achievement: [Notable accomplishment]
- Quotes: "[Quote 1]", "[Quote 2]"

**Person 2: [Name]**
- Title: [Current position]
- Background: [Education, previous roles]
- Key Achievement: [Notable accomplishment]
- Quotes: "[Quote 1]", "[Quote 2]"

(Profile 3-5 different people)

### INDIA ANGLE (Only if naturally relevant)
NOTE: Only include if there's a genuine India connection. Leave section empty if no natural connection.
If relevant:
- **Market Size in India:** [₹ amount]
- **Indian Users/Customers:** [Number]
- **Indian Pricing:** [₹ prices]
- **Indian Competitors:** [List with comparisons]

### CONTROVERSY & DRAMA
1. [Drama point 1 with details]
2. [Drama point 2 with details]
(List all controversial/dramatic elements)

### FUTURE & PREDICTIONS
1. [Prediction 1] - [Source/Expert]
2. [Prediction 2] - [Source/Expert]
(List 5-10 predictions)

### SOURCES (List all sources found)
1. [Source 1] - [Type: News/Interview/Report/Study]
2. [Source 2] - [Type]
(List 10+ sources)

---

REMEMBER: The goal is QUANTITY. Give the scriptwriter 80-120+ individual facts to choose from. Don't summarize or condense - list everything you find.
"""

        response = await self.llm.ainvoke(deep_dive_prompt)
        return {"raw_research": response.content, "angle": angle}

    async def _stage_connect(self, deep_research: Dict, selected_angle: Dict) -> str:
        """
        Stage 4: CONNECT - Organize facts into categories while PRESERVING ALL DATA.
        Don't condense - keep all 80-120+ facts organized for the scriptwriter.
        """

        connect_prompt = f"""
You are a narrative architect. Organize research facts into a connected story flow.

## THE RAW RESEARCH (KEEP ALL OF IT):

{deep_research['raw_research']}

## THE SELECTED ANGLE:

{selected_angle['raw_selection']}

## KEY PRINCIPLES (v8.3)

1. **CONTEXT FIRST** - Explain WHY this is happening before WHAT happened
2. **NUMBERS WITH MEANING** - Show before→after, not standalone numbers
3. **CONTRAST** - Compare old way vs new way when applicable
4. **ESCALATION** - Zoom from company → industry → global
5. **HOOKS THROUGHOUT** - Add curiosity triggers between major points (not just opening)
6. **LAYMAN LANGUAGE** - No jargon without explanation. Would a non-tech friend understand?
7. **PERSPECTIVE** - Not Wikipedia. Have opinions. Take a stance.
8. **INDIA ANGLE - ONLY IF NATURAL** - Don't force it. Only include if genuine connection.

## OUTPUT FORMAT (Preserve all data, add organization)

**TOP 10 HOOK OPTIONS:**
Create 10 different hook variations:
1. [Shocking number hook] - "[Number] + [unexpected context]"
2. [Person-action hook] - "[Person] just [unexpected action]"
3. [While everyone hook] - "While everyone's focused on X, Y quietly..."
4. [Most people don't know hook] - "Most people don't know that..."
5. [India angle hook] - ONLY if natural connection exists, otherwise skip
6. [Controversy hook] - Drama/conflict angle
7. [Underdog hook] - David vs Goliath angle
8. [Secret revealed hook] - "Here's what [company] doesn't tell you..."
9. [Timeline hook] - "In just X days/months, [achievement]"
10. [Comparison hook] - "[Thing A] costs X. [Thing B]? Just Y."

**MID-SCRIPT RETENTION TRIGGERS:**
Phrases to use BETWEEN major points to keep viewers watching:
- "But here's where it gets interesting..."
- "And then they discovered something nobody expected."
- "That's not even the crazy part."
- "But there's a problem nobody's talking about."
- "Here's what the headlines missed."

**ALL NUMBERS & STATISTICS (Keep all):**
[Copy ALL numbers from research, organized by category]
- Financial: [List all financial numbers]
- Users/Growth: [List all user/growth numbers]
- Comparisons: [List all comparison numbers]
- Timeline: [List all dates/durations]

**ALL QUOTES (Keep all):**
[Copy ALL quotes from research]

**ALL HOOK-WORTHY FACTS (Keep all):**
[Copy ALL surprising facts from research]

**CONTEXT/BACKSTORY:**
What triggered this? Why is this happening NOW?

**NUMBERS WITH CONTEXT (Layman-friendly):**
Before → After with percentage change or comparison
Technical → Layman translation (e.g., "99% fuel efficiency" → "Uses almost all its fuel instead of wasting 99%")

**ALL COMPARISON DATA (Keep all):**
[Copy ALL comparison tables and data]

**ALL PEOPLE PROFILES (Keep all):**
[Copy ALL person profiles with their quotes]

**CONTROVERSY & DRAMA:**
[Copy all dramatic/controversial elements]

**FUTURE PREDICTIONS:**
[Copy all predictions]

**THE CORE STORY:**
Who did what, explained simply (2-3 paragraphs) - LAYMAN LANGUAGE

**ESCALATION NARRATIVE:**
Company stat → Industry stat → Global implication

**PERSPECTIVE/OPINION:**
A summary says: "[Neutral statement about what happened]"
A perspective says: "[Opinionated take with stance]"
Provide 3 perspective options the scriptwriter can use.

**INSIGHT OPTIONS (Give 5 different insights):**
1. [Business insight with perspective]
2. [Technology insight with perspective]
3. [Market insight with perspective]
4. [Contrarian insight - what everyone's missing]
5. [Future-focused insight with perspective]

**INDIA ANGLE (Only if natural connection):**
If there's a NATURAL India connection (Indian founders, Indian market impact, ₹ pricing):
[Include India-specific data]
If NO natural connection, write: "No natural India angle - skip in script"

**ENGAGEMENT QUESTIONS (Give 5 options):**
Real questions that prompt thought - NOT "what do you think?" (that's lazy)
1. [Question about implications or choices]
2. [Would you invest/use this?]
3. [Will [category] survive this?]
4. [Controversial question]
5. [Future prediction question]

**ALL SOURCES:**
[Copy all sources]

---

CRITICAL: Your output should be 2000-3000 words minimum. Do NOT condense the research. The scriptwriter needs ALL the raw material. Use LAYMAN LANGUAGE throughout.
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
        Process user-uploaded PDF/file content + do additional Perplexity research.
        NO LIMITS - extract EVERYTHING from user's document, then add Perplexity on top.
        """

        print(f"[Research] Processing user content + Perplexity research for: {topic}")
        print(f"[Research] Document size: {len(content)} characters")

        # STEP 1: Extract EVERYTHING from user's document - NO LIMITS
        # Split into chunks if document is very large to process all of it
        doc_chunks = []
        chunk_size = 15000  # Process in chunks
        for i in range(0, len(content), chunk_size):
            doc_chunks.append(content[i:i + chunk_size])

        print(f"[Research] Processing {len(doc_chunks)} chunk(s) from document")

        all_doc_facts = []

        for chunk_idx, chunk in enumerate(doc_chunks):
            extract_prompt = f"""
You are extracting ALL research data from a user-uploaded document for a viral Instagram Reel.

## TOPIC: {topic}

## DOCUMENT CONTENT (Part {chunk_idx + 1} of {len(doc_chunks)}):

{chunk}

## USER NOTES:

{user_notes if user_notes else "None provided"}

---

## YOUR MISSION - EXTRACT EVERYTHING

Extract EVERY SINGLE fact, number, quote, name, date from this document.
DO NOT summarize. DO NOT condense. List EVERYTHING individually.

## OUTPUT FORMAT - LIST EVERYTHING YOU FIND:

### ALL NUMBERS (List every single number)
1. [Number] - [What it represents]
2. [Number] - [What it represents]
(List EVERY number - no limit)

### ALL QUOTES (List every quote)
1. "[Quote]" — [Person], [Context]
2. "[Quote]" — [Person], [Context]
(List EVERY quote - no limit)

### ALL FACTS (List every fact)
1. [Fact]
2. [Fact]
(List EVERY fact - no limit)

### ALL PEOPLE MENTIONED
- [Name]: [Title], [Key Info], [Any quotes]
(List EVERY person - no limit)

### ALL DATES/TIMELINE
- [Date]: [Event]
(List EVERY date - no limit)

### ALL COMPARISONS
- [Comparison]
(List EVERY comparison - no limit)

### THE STORY
[Write out the complete narrative from this section]

---

CRITICAL: Your job is to PRESERVE EVERYTHING. No limits. No summarizing. Extract every single data point.
"""

            chunk_response = await self.selector_llm.ainvoke(extract_prompt)
            all_doc_facts.append(chunk_response.content)
            print(f"[Research] Extracted {len(chunk_response.content)} chars from chunk {chunk_idx + 1}")

        # Combine all document extractions
        doc_facts = "\n\n---\n\n".join(all_doc_facts)
        print(f"[Research] Total extracted from document: {len(doc_facts)} chars")

        # STEP 2: Do EXHAUSTIVE Perplexity research to ADD MORE data
        perplexity_prompt = f"""
Research this topic EXHAUSTIVELY to ADD to user-provided content.

## TOPIC: {topic}

## KEY FACTS FROM USER'S DOCUMENT (for context):
{doc_facts[:4000]}

---

## YOUR MISSION - FIND EVERYTHING THE DOCUMENT DOESN'T HAVE

The user provided a document. Now search the web and find:
- ALL additional numbers/statistics not in their document
- ALL quotes from OTHER people (analysts, competitors, experts, users)
- ALL recent news (2024-2025)
- ALL India-specific data (₹ pricing, Indian users, Indian market)
- ALL competitor comparisons
- ALL controversy/drama
- ALL future predictions
- ALL background info on people mentioned

## OUTPUT FORMAT - NO LIMITS

### ADDITIONAL NUMBERS FROM WEB (Find as many as possible)
1. [Number] - [What it represents] - [Source]
2. [Number] - [What it represents] - [Source]
(No limit - list everything you find)

### ADDITIONAL QUOTES FROM WEB (Find as many as possible)
1. "[Quote]" — [Person], [Title], [Source]
2. "[Quote]" — [Person], [Title], [Source]
(No limit - list everything you find)

### ADDITIONAL FACTS FROM WEB (Find as many as possible)
1. [Fact] - [Source]
2. [Fact] - [Source]
(No limit - list everything you find)

### INDIA ANGLE (Only if naturally relevant)
NOTE: Only include if there's a GENUINE connection (Indian founders, Indian market impact, ₹ pricing).
Don't force India angle if no natural connection.
If relevant:
- Market size in India: [₹ amount]
- Indian users: [Number]
- Indian pricing: [₹]
- Indian competitors: [List]

### RECENT NEWS (2024-2025)
1. [Date]: [News item] - [Source]
2. [Date]: [News item] - [Source]
(No limit - list all recent news)

### COMPETITOR DATA
| Metric | This | Competitor 1 | Competitor 2 | Competitor 3 |
(Include all competitors and metrics)

### PEOPLE BACKGROUND (Additional info on people mentioned)
**[Person Name]:**
- Full background
- Education
- Previous roles
- Net worth (if available)
- Key quotes

### CONTROVERSY/DRAMA (Find all drama)
1. [Drama/Controversy] - [Details]
(No limit - list all dramatic elements)

### FUTURE PREDICTIONS
1. [Prediction] - [Expert/Source]
(No limit - list all predictions)

### SOURCES
(List all sources used)

---

CRITICAL: Find as much NEW information as possible. No limits on quantity.
"""

        # Get additional research from Perplexity
        perplexity_response = await self.llm.ainvoke(perplexity_prompt)
        perplexity_facts = perplexity_response.content

        print(f"[Research] Got {len(perplexity_facts)} chars from Perplexity research")

        # STEP 3: Combine ALL data - no condensing
        combined_research = f"""
# COMPLETE RESEARCH DATA

## EVERYTHING FROM USER'S DOCUMENT:

{doc_facts}

---

## EVERYTHING FROM WEB RESEARCH:

{perplexity_facts}

---

## TOTAL: All facts from document + all facts from web research
"""

        print(f"[Research] Combined research: {len(combined_research)} chars total")

        return {
            "status": "complete",
            "topic_type": "user_content_plus_research",
            "research_data": combined_research,
            "selected_angle": {"angle": topic, "source": "user_document + perplexity_research"},
            "research_sources": ["User uploaded document (complete)", "Perplexity web research (exhaustive)"],
        }
