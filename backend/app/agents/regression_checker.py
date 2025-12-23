"""
Regression Checker v8.3 - Catches quality issues before output
Checks for: mid-hooks, perspective, jargon, spoken format, etc.
"""

import re
from typing import Dict, List


class RegressionChecker:
    """
    Validates scripts have the elements that make viral content work.
    Now checks for:
    - Multiple hooks throughout (not just opening)
    - Perspective/opinion (not summary tone)
    - Layman language (no unexplained jargon)
    - Spoken format (no bullets)
    - Number context (comparisons, not standalone)
    """

    def check(self, script: str) -> Dict:
        """
        Check script quality and return actionable feedback.

        Returns:
            passes: bool
            score: int (0-100)
            issues: list of specific problems
            feedback: summary string
        """

        issues = []
        score = 100

        # 1. Check for bullet points (can't speak bullets) - CRITICAL
        bullet_count = len(re.findall(r'^\s*[\*\-•]\s+', script, re.MULTILINE))
        if bullet_count > 0:
            issues.append(f"Contains {bullet_count} bullet points - convert to spoken sentences")
            score -= 15

        # 2. Check for numbered list format (1. 2. 3.)
        numbered_count = len(re.findall(r'^\s*\d+\.\s+\w', script, re.MULTILINE))
        if numbered_count > 3:
            issues.append(f"{numbered_count} numbered items in list format - make conversational")
            score -= 10

        # 3. Check for mid-script hooks (retention triggers) - CRITICAL
        hook_phrases = [
            "but here's", "here's where", "that's not even",
            "here's what", "and then", "the crazy part",
            "what most people miss", "nobody's talking about",
            "here's the thing", "plot twist", "but wait",
            "and here's why", "the real story"
        ]
        # Check in middle section (after first 200 chars)
        mid_section = script[200:] if len(script) > 200 else ""
        mid_hooks_found = sum(1 for phrase in hook_phrases if phrase in mid_section.lower())
        if mid_hooks_found < 2:
            issues.append("Missing mid-script hooks - add transitions like 'But here's where it gets interesting'")
            score -= 12

        # 4. Check for perspective/opinion (not summary tone) - CRITICAL
        perspective_phrases = [
            "here's what nobody", "everyone's missing", "the real story",
            "think about it", "here's the thing", "most people don't realize",
            "what nobody tells you", "the question isn't whether",
            "this isn't about", "the bigger picture"
        ]
        has_perspective = any(phrase in script.lower() for phrase in perspective_phrases)
        if not has_perspective:
            issues.append("Reads like a summary - add perspective/opinion (e.g., 'Here's what nobody's talking about...')")
            score -= 12

        # 5. Check for technical jargon without explanation
        jargon_terms = [
            ('proliferation', 'Can\'t be turned into weapons'),
            ('baseload', 'Power that runs 24/7'),
            ('molten salt', 'reactor that runs on liquid fuel'),
            ('efficiency ratio', 'how much fuel gets used'),
            ('neural network', 'AI brain'),
            ('blockchain', 'shared digital record'),
            ('tokenization', 'breaking into pieces'),
        ]
        unexplained_jargon = []
        for term, _ in jargon_terms:
            if term.lower() in script.lower():
                # Check if it's explained (has explanation nearby)
                if not re.search(f'{term}.*(-|–|means|basically|essentially|in other words|which is)', script, re.I):
                    unexplained_jargon.append(term)

        if unexplained_jargon:
            issues.append(f"Technical jargon without explanation: {', '.join(unexplained_jargon)}")
            score -= 5 * len(unexplained_jargon)

        # 6. Check for number context (comparisons)
        numbers = re.findall(r'\d+%|\$?\d+\s*(million|billion|crore|lakh|x|times)', script, re.I)
        if numbers:
            comparison_words = ['vs', 'compared', 'instead of', 'while', 'before', 'was', 'from', 'to', 'up from', 'down from']
            has_comparison = any(word in script.lower() for word in comparison_words)
            if not has_comparison:
                issues.append("Numbers lack context - add comparisons (before vs after, old vs new)")
                score -= 10

        # 7. Check for checklist in output (should be removed)
        if "CHECKLIST" in script.upper() or "☐" in script or "☑" in script:
            issues.append("Checklist appearing in output - needs removal")
            score -= 15

        # 8. Check for generic CTA
        generic_ctas = [
            "what do you think?",
            "like and subscribe",
            "follow for more updates",
            "drop a comment",
            "let me know in the comments"
        ]
        if any(cta in script.lower() for cta in generic_ctas):
            issues.append("Generic CTA - make it specific/provocative (e.g., 'Would you trust this? Or is this crossing a line?')")
            score -= 8

        # 9. Check sentence length (spoken word needs short sentences)
        sentences = re.split(r'[.!?]', script)
        long_sentences = [s for s in sentences if len(s.split()) > 20]
        if len(long_sentences) > 2:
            issues.append(f"{len(long_sentences)} sentences too long for spoken delivery - break them up")
            score -= 8

        # 10. Check for ALL-CAPS spam words
        spam_words = ['DESTROYED', 'PANICKING', 'CHAOS', 'INSANE', 'EXPOSED', 'SHOCKING', 'MIND-BLOWING']
        found_spam = [word for word in spam_words if word in script]
        if found_spam:
            issues.append(f"Spam words in ALL-CAPS: {', '.join(found_spam)}")
            score -= 10

        # 11. Check for meta-commentary placeholders
        placeholders = ['[Full script', '[Different angle]', '[Conversational', '[Numbers explained']
        found_placeholders = [p for p in placeholders if p in script]
        if found_placeholders:
            issues.append("Contains placeholder text that wasn't filled in")
            score -= 10

        # 12. Check for forced India angle
        forced_india_phrases = [
            "indian developers should",
            "this could be useful for indian",
            "indian startups can benefit",
        ]
        if any(phrase in script.lower() for phrase in forced_india_phrases):
            if not any(natural in script.lower() for natural in ['founded by', 'indian founder', 'in india', '₹', 'rupees', 'crore']):
                issues.append("Forced India angle - remove if there's no natural connection")
                score -= 5

        # Ensure score doesn't go below 0
        score = max(0, score)

        return {
            "passes": score >= 70 and len([i for i in issues if 'CRITICAL' in i or score < 70]) == 0,
            "score": score,
            "issues": issues,
            "feedback": f"Score: {score}/100. Issues: {len(issues)}" + (f" - {'; '.join(issues[:3])}" if issues else "")
        }

    def get_fix_suggestions(self, issues: List[str]) -> List[str]:
        """
        Return specific fix suggestions for each issue.
        """
        suggestions = []

        for issue in issues:
            if "bullet points" in issue.lower():
                suggestions.append("Convert bullets to sentences: 'First up, [item]. This replaced my...'")
            elif "mid-script hooks" in issue.lower():
                suggestions.append("Add after each major point: 'But here's where it gets interesting...' or 'That's not even the crazy part.'")
            elif "summary" in issue.lower() or "perspective" in issue.lower():
                suggestions.append("Add opinion: 'Here's what nobody's talking about...' or 'Everyone's missing the real story...'")
            elif "jargon" in issue.lower():
                suggestions.append("Explain in plain English: 'Proliferation resistant' → 'Can't be turned into weapons'")
            elif "numbers" in issue.lower():
                suggestions.append("Add comparison: 'Traditional costs X. This costs Y. That's Z% less.'")
            elif "cta" in issue.lower():
                suggestions.append("Make specific: 'Would you trust this tech? Or is this crossing a line?'")

        return suggestions
