import re


class MathParser:
    """Detects and formats mathematical expressions in LaTeX."""

    def parse_formulas(self, text: str) -> list[str]:
        """Extract LaTeX formulas from text."""
        patterns = [
            r'\$\$(.*?)\$\$',         # display math $$...$$
            r'\$(.*?)\$',              # inline math $...$
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\[(.*?)\\]',            # display math \[...\]
            r'\\((.*?)\\)',            # inline math \(...\)
        ]
        formulas = []
        for pat in patterns:
            matches = re.findall(pat, text, re.DOTALL)
            formulas.extend(matches)
        return [f.strip() for f in formulas if f.strip()]

    def wrap_latex(self, formula: str) -> str:
        """Wrap a LaTeX formula for HTML rendering."""
        return f'<span class="math-formula">\\({formula}\\)</span>'

    def format_text_with_math(self, text: str) -> str:
        """Format text, preserving LaTeX expressions for rendering."""
        # Replace display math
        text = re.sub(
            r'\$\$(.*?)\$\$',
            lambda m: f'<div class="math-display">\\[{m.group(1)}\\]</div>',
            text,
            flags=re.DOTALL,
        )
        # Replace inline math
        text = re.sub(
            r'\$(.*?)\$',
            lambda m: f'\\({m.group(1)}\\)',
            text,
        )
        return text
