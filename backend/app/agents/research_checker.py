"""
Research Quality Checker
Validates that research has all components needed for a viral script.
"""

import re
from typing import Dict, List, Tuple


class ResearchChecker:
    """
    Checks if research output has everything needed for a viral script.
    """

    REQUIRED_COMPONENTS = [
        ("hook_fact", "A scroll-stopping hook fact"),
        ("key_person", "A specific person with name and title"),
        ("direct_quote", "At least one direct quote in quotation marks"),
        ("specific_number", "At least one specific number (not rounded)"),
        ("india_angle", "India relevance with Rs. amount if possible"),
        ("transition", "A 'But here's where it gets interesting' moment"),
        ("insight", "A bigger picture reframe"),
    ]

    def check(self, research_data: str) -> Tuple[bool, List[str], int]:
        """
        Check research quality.

        Returns:
            Tuple of (passes: bool, issues: List[str], score: int)
        """
        issues = []
        score = 0

        # Check for each required component
        checks = [
            self._has_hook_fact(research_data),
            self._has_key_person(research_data),
            self._has_direct_quote(research_data),
            self._has_specific_number(research_data),
            self._has_india_angle(research_data),
            self._has_transition(research_data),
            self._has_insight(research_data),
        ]

        for i, (component_name, description) in enumerate(self.REQUIRED_COMPONENTS):
            if checks[i]:
                score += 15  # ~15 points per component
            else:
                issues.append(f"Missing: {description}")

        # Bonus points for extra quality
        if self._has_multiple_quotes(research_data):
            score += 5
        if self._has_comparison_stat(research_data):
            score += 5
        if self._has_recent_date(research_data):
            score += 5

        passes = score >= 70 and len(issues) <= 2

        return passes, issues, min(score, 100)

    def _has_hook_fact(self, text: str) -> bool:
        """Check for hook fact section."""
        return "HOOK FACT" in text.upper() or "HOOK:" in text.upper()

    def _has_key_person(self, text: str) -> bool:
        """Check for key person with name and title."""
        indicators = ["CEO", "founder", "director", "chief", "president", "Name:"]
        return any(ind.lower() in text.lower() for ind in indicators)

    def _has_direct_quote(self, text: str) -> bool:
        """Check for direct quote in quotation marks."""
        # Look for quoted text that's more than just a few words
        quotes = re.findall(r'"([^"]{20,})"', text)
        return len(quotes) >= 1

    def _has_specific_number(self, text: str) -> bool:
        """Check for specific numbers (not rounded millions/billions)."""
        # Look for specific numbers like $32.7 billion, Rs.50,000, 2,200 crores
        specific_patterns = [
            r'\$\d+\.?\d*\s*(billion|million|crore|lakh)',  # $32.7 billion
            r'Rs\.?\s*\d+,?\d*',  # Rs.50,000 or Rs 50,000
            r'\d+,\d{3}',  # 2,200
            r'\d+\.\d+%',  # 15.7%
            r'\d+\s*(crore|lakh)',  # 500 crore
        ]
        for pattern in specific_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _has_india_angle(self, text: str) -> bool:
        """Check for India relevance."""
        india_indicators = [
            "india", "indian", "rs.", "rs ", "rupee", "crore", "lakh",
            "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad",
            "chennai", "pune", "kolkata", "ahmedabad"
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in india_indicators)

    def _has_transition(self, text: str) -> bool:
        """Check for transition phrases."""
        transitions = [
            "but here's where",
            "here's the crazy part",
            "plot twist",
            "but wait",
            "here's what most people don't know",
            "transition",
        ]
        text_lower = text.lower()
        return any(trans in text_lower for trans in transitions)

    def _has_insight(self, text: str) -> bool:
        """Check for insight/reframe section."""
        return "INSIGHT" in text.upper() or "bigger picture" in text.lower()

    def _has_multiple_quotes(self, text: str) -> bool:
        """Bonus: Check for multiple direct quotes."""
        quotes = re.findall(r'"([^"]{20,})"', text)
        return len(quotes) >= 2

    def _has_comparison_stat(self, text: str) -> bool:
        """Bonus: Check for comparison stats (X times, X% more, etc.)."""
        patterns = [r'\d+x', r'\d+\s*times', r'\d+%\s*(more|less|higher|lower)']
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _has_recent_date(self, text: str) -> bool:
        """Bonus: Check for recent dates (2024, 2025)."""
        return "2024" in text or "2025" in text
