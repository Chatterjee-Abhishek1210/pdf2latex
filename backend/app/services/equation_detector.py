"""
Equation Detector — Detects mathematical equations in PDF text.
Uses heuristic pattern matching to identify inline and display equations.
"""
import re
import logging
from typing import List
from app.models.schemas import EquationBlock, TextBlock

logger = logging.getLogger(__name__)


class EquationDetector:
    """
    Detects mathematical equations within extracted text blocks.
    Uses pattern matching for common mathematical symbols and structures.
    """

    # Mathematical Unicode ranges and symbols
    MATH_SYMBOLS = set("∫∑∏∂∇∆√∞≈≠≤≥±×÷∈∉⊂⊃∪∩∧∨¬∀∃∅→←↔⇒⇐⇔αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ")

    # Patterns that strongly suggest mathematical content
    MATH_PATTERNS = [
        r'[=<>≤≥≈≠±]',           # Comparison/equality operators
        r'\d+[\+\-\*/\^]\d+',    # Arithmetic expressions
        r'[a-zA-Z]\s*[=]\s*',    # Variable assignments
        r'\b(sin|cos|tan|log|ln|exp|lim|max|min|sup|inf)\b',  # Functions
        r'[∫∑∏]',                # Calculus symbols
        r'\b\d+\s*[/]\s*\d+\b',  # Fractions
        r'[α-ωΑ-Ω]',            # Greek letters
        r'_\{.*?\}',             # Subscripts
        r'\^\{.*?\}',            # Superscripts
    ]

    # Common equation starters/patterns in text
    DISPLAY_PATTERNS = [
        r'^\s*[A-Za-z]\s*=',     # x = ...
        r'^\s*\\',               # LaTeX commands
        r'^\s*\d+\)',            # Numbered equations
    ]

    def detect(self, page, page_num: int, text_blocks: List[TextBlock]) -> List[EquationBlock]:
        """
        Detect equations from text blocks on a page.
        """
        equations = []

        for block in text_blocks:
            if block.page != page_num:
                continue

            text = block.text.strip()
            if not text:
                continue

            # Check if the entire block is an equation
            if self._is_equation_block(text, block):
                eq = EquationBlock(
                    latex=self._text_to_latex_math(text),
                    x=block.x,
                    y=block.y,
                    width=block.width,
                    height=block.height,
                    page=page_num,
                    inline=False,
                )
                equations.append(eq)

            # Check for inline equations within text
            inline_eqs = self._find_inline_equations(text, block)
            equations.extend(inline_eqs)

        return equations

    def _is_equation_block(self, text: str, block: TextBlock) -> bool:
        """
        Determine if an entire text block is a mathematical equation.
        """
        # Short blocks with lots of math symbols
        math_char_count = sum(1 for c in text if c in self.MATH_SYMBOLS or c in "=+-*/^_{}")
        total_chars = len(text)

        if total_chars == 0:
            return False

        math_ratio = math_char_count / total_chars

        # High ratio of math symbols
        if math_ratio > 0.3 and total_chars < 200:
            return True

        # Check display equation patterns
        for pattern in self.DISPLAY_PATTERNS:
            if re.match(pattern, text):
                if math_ratio > 0.15:
                    return True

        # Short, centered text with math symbols is likely an equation
        if block.alignment == "center" and total_chars < 100 and math_ratio > 0.1:
            return True

        return False

    def _find_inline_equations(self, text: str, block: TextBlock) -> List[EquationBlock]:
        """
        Find inline equations within a text block.
        """
        # This is a simplified detection — in production, use a trained model
        equations = []

        # Look for text segments between $ signs (common in technical PDFs)
        dollar_pattern = r'\$([^$]+)\$'
        for match in re.finditer(dollar_pattern, text):
            eq_text = match.group(1)
            equations.append(EquationBlock(
                latex=eq_text,
                x=block.x,
                y=block.y,
                width=block.width,
                height=block.height,
                page=block.page,
                inline=True,
            ))

        return equations

    def _text_to_latex_math(self, text: str) -> str:
        """
        Convert detected equation text to LaTeX math syntax.
        Handles common Unicode math symbols.
        """
        replacements = {
            '∫': r'\int',
            '∑': r'\sum',
            '∏': r'\prod',
            '∂': r'\partial',
            '∇': r'\nabla',
            '∆': r'\Delta',
            '√': r'\sqrt',
            '∞': r'\infty',
            '≈': r'\approx',
            '≠': r'\neq',
            '≤': r'\leq',
            '≥': r'\geq',
            '±': r'\pm',
            '×': r'\times',
            '÷': r'\div',
            '∈': r'\in',
            '∉': r'\notin',
            '⊂': r'\subset',
            '⊃': r'\supset',
            '∪': r'\cup',
            '∩': r'\cap',
            '∧': r'\wedge',
            '∨': r'\vee',
            '¬': r'\neg',
            '∀': r'\forall',
            '∃': r'\exists',
            '∅': r'\emptyset',
            '→': r'\rightarrow',
            '←': r'\leftarrow',
            '↔': r'\leftrightarrow',
            '⇒': r'\Rightarrow',
            '⇐': r'\Leftarrow',
            '⇔': r'\Leftrightarrow',
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma',
            'δ': r'\delta', 'ε': r'\epsilon', 'ζ': r'\zeta',
            'η': r'\eta', 'θ': r'\theta', 'ι': r'\iota',
            'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
            'ν': r'\nu', 'ξ': r'\xi', 'π': r'\pi',
            'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau',
            'υ': r'\upsilon', 'φ': r'\phi', 'χ': r'\chi',
            'ψ': r'\psi', 'ω': r'\omega',
            'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta',
            'Λ': r'\Lambda', 'Ξ': r'\Xi', 'Π': r'\Pi',
            'Σ': r'\Sigma', 'Φ': r'\Phi', 'Ψ': r'\Psi',
            'Ω': r'\Omega',
        }

        result = text
        for symbol, latex_cmd in replacements.items():
            result = result.replace(symbol, f' {latex_cmd} ')

        # Clean up multiple spaces
        result = re.sub(r'\s+', ' ', result).strip()

        return result
