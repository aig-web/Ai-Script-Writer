"""
Utility functions for script processing
Cleans output, removes bullets, removes checklists
"""

import re


def clean_script_output(text: str) -> str:
    """
    Clean the script output:
    - Remove checklist
    - Remove meta-commentary
    - Remove bullet points formatting
    """

    # Remove checklist section entirely
    if "CHECKLIST" in text.upper():
        parts = re.split(r'#{1,3}\s*CHECKLIST', text, flags=re.IGNORECASE)
        text = parts[0].strip()

    # Remove checkbox characters
    text = re.sub(r'[☐☑✓✗]', '', text)

    # Remove lines that look like checklist items
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        # Skip lines that are checklist-like
        if re.match(r'^\s*(Hook|Context|Numbers|Contrast|Insight|Word count|Short punch).*[✓✗☐☑]', line, re.I):
            continue
        if re.match(r'^\s*\d+\s*words?\s*$', line, re.I):
            continue
        if re.match(r'^\s*-\s*\[\s*[xX\s]\s*\]', line):  # - [ ] or - [x] style
            continue
        clean_lines.append(line)

    text = '\n'.join(clean_lines)

    # Remove trailing whitespace
    text = text.strip()

    return text


def convert_bullets_to_prose(text: str) -> str:
    """
    Convert bullet points to spoken prose.
    This is critical because you can't speak bullet points.
    """
    lines = text.split('\n')
    result = []
    in_script_section = False

    for i, line in enumerate(lines):
        # Track if we're in the SCRIPT section
        if '## SCRIPT' in line.upper():
            in_script_section = True
            result.append(line)
            continue

        # Only convert bullets in the SCRIPT section
        if in_script_section:
            # Check if it's a bullet point
            if re.match(r'^\s*[\*\-•]\s+', line):
                # Remove bullet and clean
                clean_line = re.sub(r'^\s*[\*\-•]\s+', '', line).strip()
                result.append(clean_line)
            # Check for numbered list (1. 2. 3.)
            elif re.match(r'^\s*\d+\.\s+', line):
                # Convert "1. Thing" to "First, Thing" or "Number one, Thing"
                clean_line = re.sub(r'^\s*\d+\.\s+', '', line).strip()
                result.append(clean_line)
            else:
                result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def remove_meta_commentary(text: str) -> str:
    """
    Remove meta-commentary like "[Full script - 150 words]" placeholders.
    """
    # Remove placeholder-style comments
    text = re.sub(r'\[Full script.*?\]', '', text)
    text = re.sub(r'\[Conversational.*?\]', '', text)
    text = re.sub(r'\[Hooks/transitions.*?\]', '', text)
    text = re.sub(r'\[Numbers explained.*?\]', '', text)
    text = re.sub(r'\[Clear perspective.*?\]', '', text)
    text = re.sub(r'\[Engaging closing.*?\]', '', text)
    text = re.sub(r'\[Different angle\]', '', text)

    # Clean up empty lines created by removals
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def ensure_spoken_format(text: str) -> str:
    """
    Ensure the script is in a format that can be spoken.
    - No technical tables
    - No markdown formatting
    - No code blocks
    """
    # Remove markdown tables
    text = re.sub(r'\|[^\n]+\|', '', text)
    text = re.sub(r'\|-+\|', '', text)

    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text)

    # Remove bold/italic markdown (but keep the text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic* -> italic

    # Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def full_clean(text: str) -> str:
    """
    Run all cleaning functions in sequence.
    """
    text = clean_script_output(text)
    text = remove_meta_commentary(text)
    text = convert_bullets_to_prose(text)
    text = ensure_spoken_format(text)
    return text
