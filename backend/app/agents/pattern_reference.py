"""
Pattern Reference - What works and what doesn't based on actual script performance
Used to inject winning/losing patterns into the writer prompt.
"""

WINNING_PATTERNS = """
## PATTERNS FROM WINNING SCRIPTS

**Hooks that worked:**
- Context before reveal: "While everyone focused on X, Y quietly happened"
- Contrast hook: "Traditional X costs millions. This costs €2."
- Stakes hook: "Since [event], everything changed for [subject]"
- Perspective hook: "Everyone's talking about X. They're missing the real story."

**Structures that worked:**
- Short punchy opening lines (2-6 words each) after hook
- Transition hooks every 3-4 sentences ("But here's where it gets interesting")
- Numbers always with comparison (before vs after, old vs new)
- Zoom out at end (company → industry → world)
- Sharp reframe before CTA ("They're not doing X. They're creating Y.")

**Language that worked:**
- Conversational tone ("Here's the thing...")
- Analogies for complex concepts
- Direct address ("Think about it...")
- Rhetorical questions mid-script for retention

**CTAs that worked:**
- Binary choices ("Would you X or Y?")
- Provocative questions about implications
- Questions that require opinion, not just "yes/no"
"""

LOSING_PATTERNS = """
## PATTERNS FROM LOSING SCRIPTS (AVOID THESE)

**Hooks that flopped:**
- Starting with company name + action
- "What if I told you..."
- Generic questions as hooks
- Bio dumps before the story

**Structures that flopped:**
- Info dump in first paragraph
- No transitions - just continuous information
- Bullet points for statistics
- Staying at company level only (no zoom out)
- Generic philosophical endings

**Language that flopped:**
- Technical jargon without explanation
- ALL-CAPS for emphasis
- "This is huge" / "Game changer" without proof
- Formal/Wikipedia tone
- Forced India angles

**CTAs that flopped:**
- "What do you think?"
- "Follow for more updates"
- "Like and subscribe"
- Vague "the future is here" statements
"""


def get_patterns():
    """Return winning and losing patterns for prompt injection."""
    return WINNING_PATTERNS, LOSING_PATTERNS
