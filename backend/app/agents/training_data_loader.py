"""
Training Data Loader - Parses winning and losing scripts for RAG
Extracts structured data from script files for pattern learning
"""
import re
from typing import List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ScriptCategory(Enum):
    WINNING = "winning"
    LOSING = "losing"


@dataclass
class ParsedScript:
    """Structured representation of a parsed script"""
    title: str
    hooks: List[str]
    body: str
    full_text: str
    category: ScriptCategory

    # Extracted elements
    hook_count: int
    has_crazy_part: bool
    has_transition_hooks: bool
    has_india_angle: bool
    has_numbers: bool
    has_quotes: bool
    word_count: int

    # Structure analysis
    hook_types: List[str]  # shock, question, negative, story, financial, status
    cta_type: str  # question, save, follow, comment


class TrainingDataLoader:
    """
    Loads and parses winning/losing scripts for training the RAG system.
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            # Look for reference_docs folder in root directory
            base_path = Path(__file__).resolve().parent.parent.parent.parent / "reference_docs"
        self.base_path = Path(base_path)

        # Patterns for extraction
        self.hook_patterns = [
            r'Hook\s*\d+\s*[:\-]?\s*(.+?)(?=Hook\s*\d+|Body|$)',
            r'HOOK\s*(?:OPTION\s*)?\d+\s*[:\-]?\s*(.+?)(?=HOOK|Body|$)',
        ]

        self.transition_phrases = [
            "but here's where it gets interesting",
            "but here's the crazy part",
            "now here's the crazy part",
            "the crazy part",
            "plot twist",
            "but wait",
            "here's what most people don't know",
            "this is where it gets",
            "but then",
        ]

        self.hook_type_patterns = {
            "shock": [r"beat", r"killed", r"destroyed", r"banned", r"secret", r"hidden"],
            "question": [r"^have you", r"^what if", r"^ever wonder", r"^did you know"],
            "negative": [r"losing", r"fail", r"mistake", r"worst", r"scary", r"terrifying"],
            "story": [r"this man", r"this woman", r"meet", r"in \d{4}", r"started"],
            "financial": [r"crore", r"lakh", r"₹", r"rupee", r"earn", r"revenue", r"profit"],
            "status": [r"rich", r"elite", r"billionaire", r"ceo", r"founder"],
        }

    def load_winning_scripts(self) -> List[ParsedScript]:
        """Load and parse winning scripts"""
        winning_file = self.base_path / "Winning reels script.txt"
        if not winning_file.exists():
            print(f"[TrainingLoader] Winning scripts file not found: {winning_file}")
            return []

        content = winning_file.read_text(encoding='utf-8')
        return self._parse_scripts(content, ScriptCategory.WINNING)

    def load_losing_scripts(self) -> List[ParsedScript]:
        """Load and parse losing scripts"""
        # Try both with and without .txt extension
        losing_file = self.base_path / "Losing reels script.txt"
        if not losing_file.exists():
            losing_file = self.base_path / "Losing reels script"
        if not losing_file.exists():
            print(f"[TrainingLoader] Losing scripts file not found: {losing_file}")
            return []

        content = losing_file.read_text(encoding='utf-8')
        return self._parse_scripts(content, ScriptCategory.LOSING)

    def _parse_scripts(self, content: str, category: ScriptCategory) -> List[ParsedScript]:
        """Parse raw content into structured scripts"""
        scripts = []

        # Split by script titles (numbered list at the beginning or double newlines)
        # Each script typically starts with a title line followed by Hook 1:
        script_blocks = self._split_into_scripts(content)

        for title, block in script_blocks:
            if len(block.strip()) < 100:  # Skip very short blocks
                continue

            try:
                parsed = self._parse_single_script(title, block, category)
                if parsed:
                    scripts.append(parsed)
            except Exception as e:
                print(f"[TrainingLoader] Error parsing script '{title[:30]}...': {e}")

        print(f"[TrainingLoader] Parsed {len(scripts)} {category.value} scripts")
        return scripts

    def _split_into_scripts(self, content: str) -> List[Tuple[str, str]]:
        """Split content into individual scripts by detecting titles"""
        scripts = []

        # Look for patterns like "Samay Raina's Latent app\nHook 1:" or title followed by hooks
        # Split on lines that look like titles (no Hook/Body prefix, followed by Hook)
        lines = content.split('\n')

        current_title = None
        current_block = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip the numbered index list at the beginning
            if re.match(r'^\d+\.\s+.+$', stripped) and len(stripped) < 100:
                # This is likely an index entry, skip
                continue

            # Check if this is a title line (not starting with Hook/Body, followed by Hook)
            is_title = (
                stripped and
                not stripped.lower().startswith('hook') and
                not stripped.lower().startswith('body') and
                len(stripped) < 100 and
                not stripped.startswith('-') and
                not stripped.startswith('●')
            )

            # Look ahead to see if next non-empty line is "Hook"
            next_is_hook = False
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip().lower()
                if next_line:
                    if next_line.startswith('hook'):
                        next_is_hook = True
                    break

            if is_title and next_is_hook and current_title is None:
                # Start a new script
                if current_title and current_block:
                    scripts.append((current_title, '\n'.join(current_block)))
                current_title = stripped
                current_block = []
            elif is_title and next_is_hook:
                # New script starts
                if current_title and current_block:
                    scripts.append((current_title, '\n'.join(current_block)))
                current_title = stripped
                current_block = []
            else:
                # Continue current block
                if current_title:
                    current_block.append(line)

        # Add the last script
        if current_title and current_block:
            scripts.append((current_title, '\n'.join(current_block)))

        return scripts

    def _parse_single_script(self, title: str, block: str, category: ScriptCategory) -> ParsedScript:
        """Parse a single script block into structured data"""
        # Extract hooks
        hooks = self._extract_hooks(block)

        # Extract body (everything after hooks)
        body = self._extract_body(block)

        # Full text is the entire block
        full_text = block.strip()

        # Analyze script
        has_crazy_part = any(p in block.lower() for p in ["crazy part", "craziest part", "here's the crazy"])
        has_transition_hooks = any(p in block.lower() for p in self.transition_phrases)
        has_india_angle = any(p in block.lower() for p in ["india", "indian", "₹", "crore", "lakh", "rupee"])
        has_numbers = bool(re.search(r'\d+(?:\.\d+)?(?:\s*(?:crore|lakh|percent|%|million|billion))?', block))
        has_quotes = '"' in block and block.count('"') >= 2

        word_count = len(block.split())

        # Classify hook types
        hook_types = []
        for hook in hooks:
            hook_type = self._classify_hook(hook)
            if hook_type:
                hook_types.append(hook_type)

        # Classify CTA
        cta_type = self._classify_cta(block)

        return ParsedScript(
            title=title,
            hooks=hooks,
            body=body,
            full_text=full_text,
            category=category,
            hook_count=len(hooks),
            has_crazy_part=has_crazy_part,
            has_transition_hooks=has_transition_hooks,
            has_india_angle=has_india_angle,
            has_numbers=has_numbers,
            has_quotes=has_quotes,
            word_count=word_count,
            hook_types=hook_types,
            cta_type=cta_type
        )

    def _extract_hooks(self, block: str) -> List[str]:
        """Extract hooks from script block"""
        hooks = []

        # Try different hook patterns
        for pattern in self.hook_patterns:
            matches = re.findall(pattern, block, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    hook = match.strip()
                    # Clean up the hook
                    hook = re.sub(r'\n+', ' ', hook)
                    hook = hook.strip()
                    if hook and len(hook) > 10:
                        hooks.append(hook)

        # Also try line-by-line detection
        if not hooks:
            lines = block.split('\n')
            in_hook = False
            current_hook = []

            for line in lines:
                stripped = line.strip()
                if re.match(r'^hook\s*\d+\s*[:\-]?', stripped, re.IGNORECASE):
                    if current_hook:
                        hooks.append(' '.join(current_hook).strip())
                    current_hook = [re.sub(r'^hook\s*\d+\s*[:\-]?\s*', '', stripped, flags=re.IGNORECASE)]
                    in_hook = True
                elif stripped.lower().startswith('body') or (in_hook and not stripped):
                    if current_hook:
                        hooks.append(' '.join(current_hook).strip())
                        current_hook = []
                    in_hook = False
                elif in_hook:
                    current_hook.append(stripped)

        return hooks[:5]  # Max 5 hooks

    def _extract_body(self, block: str) -> str:
        """Extract body text from script block"""
        # Find where hooks end and body begins
        body_match = re.search(r'(?:Body\s*[:\-]?\s*|Hook\s*\d+.*?\n\n)(.*)', block, re.IGNORECASE | re.DOTALL)
        if body_match:
            return body_match.group(1).strip()

        # Fallback: take everything after the last "Hook" section
        lines = block.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if re.match(r'^hook\s*\d+', line.strip(), re.IGNORECASE):
                body_start = i + 1

        if body_start > 0 and body_start < len(lines):
            return '\n'.join(lines[body_start:]).strip()

        return block.strip()

    def _classify_hook(self, hook: str) -> str:
        """Classify hook type based on patterns"""
        hook_lower = hook.lower()

        for hook_type, patterns in self.hook_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, hook_lower):
                    return hook_type

        return "general"

    def _classify_cta(self, block: str) -> str:
        """Classify CTA type"""
        block_lower = block.lower()

        if "save this" in block_lower:
            return "save"
        elif "comment" in block_lower and ("let me know" in block_lower or "drop" in block_lower):
            return "comment"
        elif "follow" in block_lower and ("for more" in block_lower):
            return "follow"
        elif "?" in block[-200:]:  # Question near the end
            return "question"

        return "follow"

    def get_winning_patterns(self) -> Dict[str, any]:
        """Analyze winning scripts for common patterns"""
        winning = self.load_winning_scripts()

        patterns = {
            "avg_hook_count": 0,
            "crazy_part_rate": 0,
            "transition_rate": 0,
            "india_angle_rate": 0,
            "numbers_rate": 0,
            "quotes_rate": 0,
            "avg_word_count": 0,
            "common_hook_types": {},
            "common_cta_types": {},
            "sample_hooks": [],
        }

        if not winning:
            return patterns

        n = len(winning)
        patterns["avg_hook_count"] = sum(s.hook_count for s in winning) / n
        patterns["crazy_part_rate"] = sum(1 for s in winning if s.has_crazy_part) / n
        patterns["transition_rate"] = sum(1 for s in winning if s.has_transition_hooks) / n
        patterns["india_angle_rate"] = sum(1 for s in winning if s.has_india_angle) / n
        patterns["numbers_rate"] = sum(1 for s in winning if s.has_numbers) / n
        patterns["quotes_rate"] = sum(1 for s in winning if s.has_quotes) / n
        patterns["avg_word_count"] = sum(s.word_count for s in winning) / n

        # Count hook types
        hook_type_counts = {}
        for s in winning:
            for ht in s.hook_types:
                hook_type_counts[ht] = hook_type_counts.get(ht, 0) + 1
        patterns["common_hook_types"] = hook_type_counts

        # Count CTA types
        cta_counts = {}
        for s in winning:
            cta_counts[s.cta_type] = cta_counts.get(s.cta_type, 0) + 1
        patterns["common_cta_types"] = cta_counts

        # Sample best hooks (first hook from each script)
        patterns["sample_hooks"] = [s.hooks[0] for s in winning[:10] if s.hooks]

        return patterns

    def get_losing_patterns(self) -> Dict[str, any]:
        """Analyze losing scripts for patterns to avoid"""
        losing = self.load_losing_scripts()

        patterns = {
            "avg_hook_count": 0,
            "crazy_part_rate": 0,
            "transition_rate": 0,
            "india_angle_rate": 0,
            "common_issues": [],
        }

        if not losing:
            return patterns

        n = len(losing)
        patterns["avg_hook_count"] = sum(s.hook_count for s in losing) / n
        patterns["crazy_part_rate"] = sum(1 for s in losing if s.has_crazy_part) / n
        patterns["transition_rate"] = sum(1 for s in losing if s.has_transition_hooks) / n
        patterns["india_angle_rate"] = sum(1 for s in losing if s.has_india_angle) / n

        return patterns

    def get_all_scripts_for_embedding(self) -> List[Dict]:
        """Get all scripts formatted for vector embedding"""
        winning = self.load_winning_scripts()
        losing = self.load_losing_scripts()

        all_scripts = []

        for script in winning:
            all_scripts.append({
                "title": script.title,
                "category": "winning",
                "hooks": script.hooks,
                "body": script.body,
                "full_text": script.full_text,
                "metadata": {
                    "hook_types": script.hook_types,
                    "cta_type": script.cta_type,
                    "has_crazy_part": script.has_crazy_part,
                    "has_india_angle": script.has_india_angle,
                    "word_count": script.word_count,
                }
            })

        for script in losing:
            all_scripts.append({
                "title": script.title,
                "category": "losing",
                "hooks": script.hooks,
                "body": script.body,
                "full_text": script.full_text,
                "metadata": {
                    "hook_types": script.hook_types,
                    "cta_type": script.cta_type,
                    "has_crazy_part": script.has_crazy_part,
                    "has_india_angle": script.has_india_angle,
                    "word_count": script.word_count,
                }
            })

        return all_scripts


# Test the loader
if __name__ == "__main__":
    loader = TrainingDataLoader()

    print("\n=== WINNING SCRIPTS ===")
    winning = loader.load_winning_scripts()
    for s in winning[:3]:
        print(f"\nTitle: {s.title}")
        print(f"Hooks: {len(s.hooks)}")
        if s.hooks:
            print(f"First hook: {s.hooks[0][:100]}...")
        print(f"Hook types: {s.hook_types}")

    print("\n=== PATTERNS ===")
    patterns = loader.get_winning_patterns()
    print(f"Avg hook count: {patterns['avg_hook_count']:.1f}")
    print(f"Crazy part rate: {patterns['crazy_part_rate']*100:.0f}%")
    print(f"Transition rate: {patterns['transition_rate']*100:.0f}%")
    print(f"India angle rate: {patterns['india_angle_rate']*100:.0f}%")
