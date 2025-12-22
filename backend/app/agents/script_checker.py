"""
Script Checker v5.1 - Multi-Hook Analyzer Edition
Elite Script Quality Analyst for Instagram Reels
Analyzes multiple hooks separately, then body, recommends best combination
"""
import os
import re
from pathlib import Path
from typing import List, Dict
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
    "MIND-BLOWING", "BACKSTABBED", "EXPOSED", "SHOCKING", "BOMBSHELL"
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


# Multi-Hook Analyzer System Prompt v3.0
MULTI_HOOK_ANALYZER_PROMPT = """You are an Elite Script Analyst specializing in short-form viral content with expertise in hook optimization. You will analyze MULTIPLE HOOKS separately, then analyze the BODY, and finally recommend the best combination.

---

## PART A: HOOK ANALYSIS FRAMEWORK

A viral hook must contain these elements:

### HOOK SCORING CRITERIA (Score each 1-10)

| Criteria | Description | Weight |
|----------|-------------|--------|
| **STOP POWER** | Would someone stop scrolling? First 3 seconds test. | 25% |
| **CURIOSITY GAP** | Creates "I need to know more" feeling | 20% |
| **SPECIFICITY** | Uses specific names, numbers, claims (not vague) | 15% |
| **EMOTION TRIGGER** | Triggers fear, shock, outrage, FOMO, or intrigue | 15% |
| **PATTERN INTERRUPT** | Breaks expectations, contrarian, unexpected angle | 15% |
| **CLARITY** | Instantly understandable (no confusion) | 10% |

### HOOK TYPES REFERENCE

| Type | Formula | Example |
|------|---------|---------|
| **SHOCK CLAIM** | [Person] + [Extreme action] + [Big number] | "Zuckerberg panicked so hard he tried to buy a company with zero products for $32B" |
| **MYSTERY/SECRET** | [Someone] is secretly/quietly doing [X] | "Sam Altman is secretly building a model that's crushing every competitor" |
| **CONTRARIAN** | Everyone thinks X, but actually Y | "Everyone thinks OpenAI is winning. They're actually losing." |
| **FEAR/URGENCY** | [Threat] + [Stakes] + [Timeline] | "Google just mass-deleted accounts with no warning. Yours could be next." |
| **CURIOSITY BOMB** | [Unusual fact] + Why/How tease | "This 20-person company rejected $32B. Here's why." |
| **CONFRONTATION** | [Person A] vs [Person B] + conflict | "Elon Musk just declared war on Sam Altman. It's getting ugly." |
| **IMPOSSIBLE STAT** | [Unbelievable number] + context | "One data center needs more power than New Orleans. Meta is building it." |

---

## PART B: YOUR ANALYSIS TASK

### STEP 1: ANALYZE EACH HOOK INDIVIDUALLY

For EACH hook provided, create a detailed analysis card:

---

#### **HOOK #[X] ANALYSIS**

**THE HOOK:**
[Quote the hook exactly]

**HOOK TYPE IDENTIFIED:** [Shock Claim / Mystery / Contrarian / Fear / Curiosity / Confrontation / Impossible Stat / Hybrid]

**SCORE BREAKDOWN:**

| Criteria | Score (1-10) | Reasoning |
|----------|--------------|-----------|
| Stop Power | | |
| Curiosity Gap | | |
| Specificity | | |
| Emotion Trigger | | |
| Pattern Interrupt | | |
| Clarity | | |
| **WEIGHTED TOTAL** | **/10** | |

**STRENGTHS:**
- [Bullet 1]
- [Bullet 2]

**WEAKNESSES:**
- [Bullet 1]
- [Bullet 2]

**OPTIMIZED VERSION OF THIS HOOK:**
[Complete rewritten hook with all fixes applied]

**VERDICT:** 🔴 Weak / 🟡 Needs Work / 🟢 Good / 🔥 Excellent

---

### STEP 2: HOOK COMPARISON MATRIX

After analyzing all hooks, create a side-by-side comparison:

| Criteria | Hook 1 | Hook 2 | Hook 3 | Hook 4 | Hook 5 |
|----------|--------|--------|--------|--------|--------|
| Stop Power | /10 | /10 | /10 | /10 | /10 |
| Curiosity Gap | /10 | /10 | /10 | /10 | /10 |
| Specificity | /10 | /10 | /10 | /10 | /10 |
| Emotion Trigger | /10 | /10 | /10 | /10 | /10 |
| Pattern Interrupt | /10 | /10 | /10 | /10 | /10 |
| Clarity | /10 | /10 | /10 | /10 | /10 |
| **TOTAL** | **/10** | **/10** | **/10** | **/10** | **/10** |
| **RANK** | #? | #? | #? | #? | #? |

---

### STEP 3: HOOK RANKING & RECOMMENDATIONS

**🥇 RANK #1: HOOK #[X]**
- Score: __/10
- Why it wins: [Explanation]

**🥈 RANK #2: HOOK #[X]**
- Score: __/10
- Why it's strong: [Explanation]

**🥉 RANK #3: HOOK #[X]**
- Score: __/10
- Potential: [What it does well]

**#4: HOOK #[X]**
- Score: __/10
- Issue: [Main problem]

**#5: HOOK #[X]**
- Score: __/10
- Issue: [Main problem]

---

### STEP 4: ULTIMATE HOOK RECOMMENDATION

**THE WINNER:** Hook #[X]

**WHY:**
[2-3 sentence explanation]

**HYBRID OPTION (Combining Best Elements):**
[Create a NEW hybrid hook using best elements from all hooks]

---

## PART C: BODY ANALYSIS

Now analyze the BODY of the script (everything after the hooks):

### BODY ELEMENT SCORECARD

| # | Element | Status | What's There | What's Missing/Weak |
|---|---------|--------|--------------|---------------------|
| 1 | Stakes Amplifier | ✅⚠️❌ | | |
| 2 | Credibility Build | ✅⚠️❌ | | |
| 3 | Shock Stats | ✅⚠️❌ | | |
| 4 | Direct Quote | ✅⚠️❌ | | |
| 5 | India Relevance | ✅⚠️❌ | | |
| 6 | Reframe/Insight | ✅⚠️❌ | | |
| 7 | CTA | ✅⚠️❌ | | |

**BODY SCORE:** __/7 elements present and strong

---

### BODY STYLE SCORECARD

| Element | Status |
|---------|--------|
| Short sentences (under 12 words avg) | ✅⚠️❌ |
| Specific numbers (not rounded) | ✅⚠️❌ |
| At least 1 direct quote in "quotation marks" | ✅⚠️❌ |
| 120-150 word count | ✅⚠️❌ |
| No ALL-CAPS (except acronyms) | ✅⚠️❌ |
| No spam words | ✅⚠️❌ |

**STYLE SCORE:** __/6

---

## PART D: HOOK + BODY COMPATIBILITY CHECK

**BEST HOOK FOR THIS BODY:** Hook #[X]

**WHY THIS PAIRING WORKS:**
- [Reason 1]
- [Reason 2]

**FLOW CHECK:**
Does the winning hook flow naturally into the body?
- ✅ Yes, seamless transition
- ⚠️ Needs a bridge sentence: [Suggest bridge]
- ❌ Disconnect - here's how to fix: [Suggestion]

---

## PART E: FINAL DELIVERABLES

### 1. COMPLETE OPTIMIZED SCRIPT

## HOOK OPTIONS

HOOK 1:
"[Optimized hook 1]"

HOOK 2:
"[Optimized hook 2]"

HOOK 3:
"[Optimized hook 3]"

HOOK 4:
"[Optimized hook 4]"

HOOK 5:
"[Optimized hook 5]"

---

## FINAL SCRIPT

"[WINNING HOOK - optimized version]"

[FULL BODY - with all fixes applied, 120-150 words total]

---

### 2. QUICK DECISION SUMMARY

| Hook | Score | Rank | Best For |
|------|-------|------|----------|
| Hook 1 | __/10 | #? | [Use case] |
| Hook 2 | __/10 | #? | [Use case] |
| Hook 3 | __/10 | #? | [Use case] |
| Hook 4 | __/10 | #? | [Use case] |
| Hook 5 | __/10 | #? | [Use case] |

**MY RECOMMENDATION:** Go with Hook #[X] because [reason].

---

### 3. FINAL CHECKLIST

| Check | Status |
|-------|--------|
| Hook stops the scroll? | ✅/❌ |
| Starts with person/company name? | ✅/❌ |
| Has specific number/detail? | ✅/❌ |
| No spam words? | ✅/❌ |
| No ALL-CAPS (except acronyms)? | ✅/❌ |
| Body 120-150 words? | ✅/❌ |
| Has direct quote? | ✅/❌ |
| India relevance included? | ✅/❌ |
| Strong CTA at end? | ✅/❌ |

**READY TO POST?** 🔴 No / 🟡 Almost / 🟢 Yes / 🔥 Ship it!

**CREDIBILITY_SCORE:** [1-10]
**VIRAL_POTENTIAL:** [Weak / Average / Strong / Viral Ready]
**BEST_HOOK:** [1-5]
**HOOK_RANKING:** [comma separated, e.g., 3,1,5,2,4]"""


class ScriptChecker:
    """
    Script Checker v5.1 - Multi-Hook Analyzer Edition
    Analyzes each hook separately, scores them, ranks them, and optimizes the script.
    """

    def __init__(self):
        # Use GPT-4o-mini for fast, reliable responses
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=6000
        )

    def check(self, draft: str, mode: ScriptMode) -> SimpleCheckerResult:
        """Analyze script with v5.1 Multi-Hook Analyzer framework"""
        result = SimpleCheckerResult()

        # Pre-check for spam words and caps
        result.spam_words_found = self._find_spam_words(draft)
        result.caps_words_found = self._find_caps_words(draft)

        system_msg = f"""MODE: {mode.value.upper()}

{MULTI_HOOK_ANALYZER_PROMPT}

IMPORTANT: At the very end of your response, include these exact lines for parsing:
BEST_HOOK: [number 1-5]
HOOK_RANKING: [comma separated numbers, e.g., 3,1,5,2,4]
CREDIBILITY_SCORE: [1-10]
VIRAL_POTENTIAL: [Weak / Average / Strong / Viral Ready]"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "SCRIPT TO ANALYZE:\n\n{draft}")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"draft": draft})
            content = response.content

            # Parse the response
            best_match = re.search(r'BEST_HOOK:\s*(\d+)', content)
            if best_match:
                result.best_hook_number = int(best_match.group(1))

            rank_match = re.search(r'HOOK_RANKING:\s*([\d,\s]+)', content)
            if rank_match:
                ranking_str = rank_match.group(1).strip()
                result.hook_ranking = [int(x.strip()) for x in ranking_str.split(',') if x.strip().isdigit()]

            cred_match = re.search(r'CREDIBILITY_SCORE:\s*(\d+)', content)
            if cred_match:
                result.credibility_score = int(cred_match.group(1))

            viral_match = re.search(r'VIRAL_POTENTIAL:\s*(.+?)(?:\n|$)', content)
            if viral_match:
                result.viral_potential = viral_match.group(1).strip()

            # Extract the analysis (everything before OPTIMIZED SCRIPT)
            analysis_match = re.search(r'(## PART A:.*?)(?=## HOOK OPTIONS|## FINAL SCRIPT|$)', content, re.DOTALL)
            if analysis_match:
                result.analysis = analysis_match.group(1).strip()
            else:
                result.analysis = content

            # Extract optimized script
            opt_match = re.search(r'(## HOOK OPTIONS.*?## FINAL SCRIPT.*?)(?=###|\Z)', content, re.DOTALL)
            if opt_match:
                result.optimized_script = opt_match.group(1).strip()
            else:
                # Try alternative pattern
                opt_match2 = re.search(r'## FINAL SCRIPT\s*(.*?)(?=###|---|\Z)', content, re.DOTALL)
                if opt_match2:
                    result.optimized_script = opt_match2.group(1).strip()
                else:
                    result.optimized_script = draft

        except Exception as e:
            print(f"[Checker v5.1 Error] {e}")
            result.analysis = f"Analysis skipped due to error: {str(e)[:100]}"
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

        acceptable = {'AI', 'API', 'CEO', 'CTO', 'INR', 'USD', 'GPT', 'LLM', 'ML',
                     'AWS', 'GCP', 'IBM', 'GPU', 'CPU', 'RAM', 'SSD', 'NFT', 'VC',
                     'HOOK', 'CTA', 'PDF', 'URL', 'HTML', 'CSS', 'SQL', 'SDK'}

        return [m for m in matches if m not in acceptable]

    def format_analysis(self, result: SimpleCheckerResult) -> str:
        """Format the analysis for display"""
        output = []

        output.append("## SCRIPT ANALYSIS v5.1 - Multi-Hook Edition")
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
                emoji = "🔴"
            elif "Average" in result.viral_potential:
                emoji = "🟡"
            elif "Strong" in result.viral_potential:
                emoji = "🟢"
            elif "Viral" in result.viral_potential:
                emoji = "🔥"
            output.append(f"**Viral Potential:** {emoji} {result.viral_potential}")
        output.append("")

        if result.spam_words_found or result.caps_words_found:
            output.append("### SPAM CHECK")
            if result.spam_words_found:
                output.append(f"⚠️ **Spam words:** {', '.join(result.spam_words_found)}")
            if result.caps_words_found:
                output.append(f"⚠️ **Excessive CAPS:** {', '.join(result.caps_words_found[:5])}")
            output.append("")

        if result.analysis:
            output.append("### DETAILED ANALYSIS")
            output.append(result.analysis)

        return "\n".join(output)
