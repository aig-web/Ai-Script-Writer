"""
Script Checker v8.0 - Hook Optimization Expert
Analyzes hooks using the proven viral formula with JSON output
Includes retention checklist for maximum engagement
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.schemas.enums import ScriptMode


# Spam words that should be avoided
SPAM_WORDS = [
    "DESTROYED", "PANICKING", "TERRIFYING", "CHAOS", "INSANE",
    "MIND-BLOWING", "BACKSTABBED", "EXPOSED", "SHOCKING", "BOMBSHELL",
    "FURIOUS", "TREMBLING"
]


class SimpleCheckerResult:
    """Result class for script analysis"""
    def __init__(self):
        self.best_hook_number = 1
        self.hook_ranking = [1, 2, 3, 4, 5]
        self.analysis = ""
        self.optimized_script = ""
        self.spam_words_found = []
        self.caps_words_found = []
        self.credibility_score = 0
        self.viral_potential = ""
        self.hook_analysis: List[Dict] = []
        self.retention_score = 0


# Hook Optimization Expert Prompt v8.0
CHECKER_PROMPT = """You are a Hook Optimization Expert for viral Instagram Reels.

## THE CORRECT HOOK FORMULA

[Famous Person/Company] + [Dramatic Action Verb] + [Specific Detail/Number]

## REFERENCE HOOKS (Score 9-10/10)

- "Mark Zuckerberg panicked so hard that he tried to buy a company with zero products for $32 billion dollars."
- "Sam Altman is secretly building a powerful AI model that's already crushing the top AI models."
- "Meta is quietly becoming an electricity company. And no one's talking about it."
- "This juice shop makes almost 2 crore rupees working just 4 hours a day."
- "Samay Raina beat Netflix and Hotstar with just one Instagram story."
- "Tesla's former AI director just dropped a tool that forces GPT, Claude, and Grok to judge each other."

## HOOK SCORING CRITERIA

| Criteria | Description | Weight |
|----------|-------------|--------|
| STOP POWER | Would someone stop scrolling in 2 seconds? | 25% |
| CURIOSITY GAP | Creates "I need to know more" feeling | 20% |
| SPECIFICITY | Uses specific names, numbers, claims | 15% |
| EMOTION TRIGGER | Triggers genuine interest (not fake hype) | 15% |
| CREDIBILITY | Sounds trustworthy, not spammy | 15% |
| CLARITY | Instantly understandable | 10% |

## FOR EACH HOOK, CHECK:

1. Starts with person/company name? (Required)
2. Has dramatic action verb? (Required)
3. Has specific detail/number? (Required)
4. Word count 10-20? (Required)
5. Zero ALL-CAPS? (Required)
6. No banned spam words? (Required)
7. Sounds factual not hypey? (Required)

## ANALYSIS OUTPUT

For each of the 5 hooks:

HOOK #[X]:
- Text: "[quote the hook]"
- Word Count: [X]
- Starts with Person/Company: YES/NO
- Has Action Verb: YES/NO
- Has Specific Detail: YES/NO
- Spam Check: CLEAN / [list issues]
- Score: X/10
- Issues: [list any problems]
- Improved Version: "[rewritten hook if score < 8]"

## HOOK RANKING

Rank all 5 hooks from best to worst:
1. Hook #[X] - Score: X/10 - [one-line reason]
2. Hook #[X] - Score: X/10 - [one-line reason]
3. Hook #[X] - Score: X/10 - [one-line reason]
4. Hook #[X] - Score: X/10 - [one-line reason]
5. Hook #[X] - Score: X/10 - [one-line reason]

BEST HOOK: #[X]

## SCRIPT OPTIMIZATION

If any hooks score below 8/10, provide optimized versions.
If the final script has issues, provide an optimized version.

## OUTPUT FORMAT

Return ONLY valid JSON (no markdown, no explanation):
{
  "hook_analysis": [
    {
      "hook_number": 1,
      "text": "...",
      "word_count": 0,
      "starts_with_person": true,
      "has_action_verb": true,
      "has_specific_detail": true,
      "spam_check": "CLEAN",
      "score": 0,
      "issues": [],
      "improved_version": null
    }
  ],
  "hook_ranking": [3, 1, 5, 2, 4],
  "best_hook_number": 3,
  "optimized_script": null,
  "viral_potential": "Weak/Average/Strong/Viral Ready",
  "credibility_score": 0,
  "retention_checklist": {
    "first_3_seconds": true,
    "content_over_creator": true,
    "retention_triggers": true,
    "impactful_conclusion": true,
    "loop_creation": true,
    "share_save_optimization": true,
    "engagement_elements": true
  },
  "retention_score": 0
}"""


# Retention Checklist for viral content optimization
RETENTION_CHECKLIST = """
## VIRAL RETENTION CHECKLIST

### First 3 Seconds
- [ ] Hook uses split-screen or engaging visual format suggestion
- [ ] Most exciting/intriguing element at the start
- [ ] Pattern-interrupting opening

### Content Over Creator
- [ ] Focuses on value, entertainment, or curiosity
- [ ] Answers "Why should viewers care?"

### Visual Variety (Suggestions)
- [ ] Avoids prolonged face-on-camera shots
- [ ] Suggests quick cuts, B-roll, graphics

### Retention Triggers
- [ ] Promises value at end
- [ ] Mid-script hooks present
- [ ] Step-by-step or numbered elements

### Impactful Conclusion
- [ ] Last 10-15 seconds highlight why it matters
- [ ] Practical takeaways for viewers

### Loop Creation
- [ ] "Follow me" is 5 seconds before end, not at end
- [ ] Ending transitions smoothly (could loop back to start)

### Share/Save Optimization
- [ ] Contains shareable/surprising content
- [ ] Aims for 15+ seconds retention
- [ ] Includes save-worthy information

### Engagement Elements
- [ ] Direct questions present
- [ ] Controversial or relatable topic
- [ ] Clear call-to-action
"""


class ScriptChecker:
    """
    Script Checker v8.0 - Hook Optimization Expert
    Analyzes hooks with proven viral formula and JSON output
    """

    def __init__(self):
        # Use GPT-4o-mini for fast, reliable analysis
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.2,
            max_tokens=4000
        )

    def check(self, draft: str, mode: ScriptMode) -> SimpleCheckerResult:
        """Analyze and optimize script with v8.0 Hook Optimizer"""
        result = SimpleCheckerResult()

        # Pre-check for spam words and caps
        result.spam_words_found = self._find_spam_words(draft)
        result.caps_words_found = self._find_caps_words(draft)

        system_msg = f"""MODE: {mode.value.upper()}

{CHECKER_PROMPT}

{RETENTION_CHECKLIST}

PRE-CHECK RESULTS:
- Spam words found: {result.spam_words_found}
- Excessive CAPS found: {result.caps_words_found}

If any spam words or excessive caps are found, mark them in issues and provide cleaned versions.
Return ONLY valid JSON. No markdown code blocks. No explanation text."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "SCRIPT TO ANALYZE AND OPTIMIZE:\n\n{draft}")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"draft": draft})
            content = response.content.strip()

            # Try to parse JSON response
            json_data = self._extract_json(content)

            if json_data:
                # Extract structured data
                result.hook_analysis = json_data.get("hook_analysis", [])
                result.hook_ranking = json_data.get("hook_ranking", [1, 2, 3, 4, 5])
                result.best_hook_number = json_data.get("best_hook_number", 1)
                result.credibility_score = json_data.get("credibility_score", 0)
                result.viral_potential = json_data.get("viral_potential", "Average")
                result.retention_score = json_data.get("retention_score", 0)

                # Build optimized script if provided
                if json_data.get("optimized_script"):
                    result.optimized_script = json_data["optimized_script"]
                else:
                    result.optimized_script = draft

                # Build analysis string from hook_analysis
                result.analysis = self._build_analysis_string(json_data)
            else:
                # Fallback to regex parsing
                result = self._parse_fallback(content, result, draft)

        except Exception as e:
            print(f"[Checker v8.0 Error] {e}")
            result.analysis = f"Analysis skipped due to error: {str(e)[:100]}"
            result.optimized_script = draft

        return result

    def _extract_json(self, content: str) -> Optional[Dict]:
        """Extract JSON from response content"""
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'\s*```$', '', content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in content
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        return None

    def _build_analysis_string(self, json_data: Dict) -> str:
        """Build human-readable analysis from JSON data"""
        lines = ["### HOOK ANALYSIS\n"]

        for hook in json_data.get("hook_analysis", []):
            lines.append(f"**HOOK #{hook.get('hook_number', '?')}:**")
            lines.append(f"- Text: \"{hook.get('text', 'N/A')[:100]}...\"")
            lines.append(f"- Word Count: {hook.get('word_count', 'N/A')}")
            lines.append(f"- Starts with Person/Company: {'YES' if hook.get('starts_with_person') else 'NO'}")
            lines.append(f"- Has Action Verb: {'YES' if hook.get('has_action_verb') else 'NO'}")
            lines.append(f"- Has Specific Detail: {'YES' if hook.get('has_specific_detail') else 'NO'}")
            lines.append(f"- Spam Check: {hook.get('spam_check', 'N/A')}")
            lines.append(f"- Score: {hook.get('score', 0)}/10")

            issues = hook.get('issues', [])
            if issues:
                lines.append(f"- Issues: {', '.join(issues)}")

            improved = hook.get('improved_version')
            if improved:
                lines.append(f"- Improved: \"{improved}\"")

            lines.append("")

        # Add ranking
        ranking = json_data.get("hook_ranking", [])
        if ranking:
            lines.append("### HOOK RANKING")
            for i, hook_num in enumerate(ranking, 1):
                lines.append(f"{i}. Hook #{hook_num}")
            lines.append("")

        # Add retention checklist results
        retention = json_data.get("retention_checklist", {})
        if retention:
            lines.append("### RETENTION CHECKLIST")
            for key, value in retention.items():
                status = "[x]" if value else "[ ]"
                formatted_key = key.replace("_", " ").title()
                lines.append(f"{status} {formatted_key}")

        return "\n".join(lines)

    def _parse_fallback(self, content: str, result: SimpleCheckerResult, draft: str) -> SimpleCheckerResult:
        """Fallback regex parsing when JSON fails"""
        # Parse best hook
        best_match = re.search(r'BEST[_\s]HOOK[:\s#]*(\d+)', content, re.IGNORECASE)
        if best_match:
            result.best_hook_number = int(best_match.group(1))

        # Parse hook ranking
        rank_match = re.search(r'hook_ranking["\s:]+\[([^\]]+)\]', content, re.IGNORECASE)
        if rank_match:
            ranking_str = rank_match.group(1)
            result.hook_ranking = [int(x.strip()) for x in ranking_str.split(',') if x.strip().isdigit()]

        # Parse credibility score
        cred_match = re.search(r'credibility_score["\s:]+(\d+)', content, re.IGNORECASE)
        if cred_match:
            result.credibility_score = int(cred_match.group(1))

        # Parse viral potential
        viral_match = re.search(r'viral_potential["\s:]+["\']?([^"\'}\n,]+)', content, re.IGNORECASE)
        if viral_match:
            result.viral_potential = viral_match.group(1).strip()

        # Set analysis to raw content
        result.analysis = content[:2000]
        result.optimized_script = draft

        return result

    def _find_spam_words(self, text: str) -> List[str]:
        """Find spam words in text"""
        found = []
        text_upper = text.upper()
        for word in SPAM_WORDS:
            if word in text_upper:
                found.append(word)
        return found

    def _find_caps_words(self, text: str) -> List[str]:
        """Find ALL-CAPS words (excluding common acronyms)"""
        caps_pattern = r'\b[A-Z]{3,}\b'
        matches = re.findall(caps_pattern, text)

        acceptable = {
            'AI', 'API', 'CEO', 'CTO', 'CFO', 'COO', 'INR', 'USD', 'EUR',
            'GPT', 'LLM', 'ML', 'NLP', 'AWS', 'GCP', 'IBM', 'GPU', 'CPU',
            'RAM', 'SSD', 'NFT', 'VC', 'HOOK', 'CTA', 'PDF', 'URL', 'HTML',
            'CSS', 'SQL', 'SDK', 'iOS', 'OPENAI', 'CHATGPT', 'CLAUDE',
            'GEMINI', 'LLAMA', 'META', 'GOOGLE', 'MICROSOFT', 'AMAZON',
            'TESLA', 'NVIDIA', 'AMD', 'INTEL', 'TCS', 'INFOSYS', 'WIPRO',
            'OPTIONS', 'FINAL', 'SCRIPT', 'ANALYSIS', 'RANKING', 'HUL',
            'IPL', 'EV', 'EVS', 'CIDCO', 'NMIIA', 'B2B', 'B2C', 'SaaS'
        }

        return [m for m in matches if m not in acceptable]

    def format_analysis(self, result: SimpleCheckerResult) -> str:
        """Format the analysis for display"""
        output = []

        output.append("## SCRIPT ANALYSIS v8.0")
        output.append("")

        output.append("### HOOK RANKING")
        output.append(f"**Best Hook: #{result.best_hook_number}**")

        if result.hook_ranking:
            ranking_str = " > ".join([f"#{n}" for n in result.hook_ranking])
            output.append(f"**Order:** {ranking_str}")
        output.append("")

        if result.credibility_score:
            output.append(f"**Credibility Score:** {result.credibility_score}/10")
        if result.viral_potential:
            emoji = ""
            if "Weak" in result.viral_potential:
                emoji = "[LOW]"
            elif "Average" in result.viral_potential:
                emoji = "[MED]"
            elif "Strong" in result.viral_potential:
                emoji = "[HIGH]"
            elif "Viral" in result.viral_potential:
                emoji = "[VIRAL]"
            output.append(f"**Viral Potential:** {emoji} {result.viral_potential}")

        if result.retention_score:
            output.append(f"**Retention Score:** {result.retention_score}/10")
        output.append("")

        if result.spam_words_found or result.caps_words_found:
            output.append("### QUALITY WARNINGS")
            if result.spam_words_found:
                output.append(f"WARNING: Spam words found: {', '.join(result.spam_words_found)}")
            if result.caps_words_found:
                output.append(f"WARNING: Excessive CAPS: {', '.join(result.caps_words_found[:5])}")
            output.append("")

        if result.analysis and len(result.analysis) > 50:
            output.append("### DETAILED ANALYSIS")
            # Truncate if too long
            if len(result.analysis) > 1500:
                output.append(result.analysis[:1500] + "...")
            else:
                output.append(result.analysis)

        return "\n".join(output)
