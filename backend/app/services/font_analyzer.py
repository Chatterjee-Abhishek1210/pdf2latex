"""
Font Analyzer — Analyzes and maps PDF fonts to LaTeX equivalents.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class FontAnalyzer:
    """
    Analyzes fonts used in PDF and maps them to LaTeX font packages.
    """

    # Mapping of common PDF fonts to LaTeX font packages
    LATEX_FONT_PACKAGES = {
        "times": ("mathptmx", r"\usepackage{mathptmx}"),
        "helvetica": ("helvet", r"\usepackage[scaled=0.92]{helvet}"),
        "arial": ("helvet", r"\usepackage[scaled=0.92]{helvet}"),
        "courier": ("courier", r"\usepackage{courier}"),
        "palatino": ("palatino", r"\usepackage{palatino}"),
        "bookman": ("bookman", r"\usepackage{bookman}"),
        "garamond": ("ebgaramond", r"\usepackage{ebgaramond}"),
        "georgia": ("mathptmx", r"\usepackage{mathptmx}"),  # closest match
        "cambria": ("mathptmx", r"\usepackage{mathptmx}"),
        "calibri": ("helvet", r"\usepackage[scaled=0.92]{helvet}"),
        "verdana": ("helvet", r"\usepackage[scaled=0.92]{helvet}"),
    }

    def analyze_fonts(self, doc) -> Dict[str, any]:
        """
        Analyze all fonts used in the document.
        Returns font statistics and LaTeX package recommendations.
        """
        font_usage = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if block["type"] != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_name = span.get("font", "unknown")
                        font_size = span.get("size", 12)
                        text_len = len(span.get("text", ""))

                        if font_name not in font_usage:
                            font_usage[font_name] = {
                                "count": 0,
                                "total_chars": 0,
                                "sizes": [],
                            }
                        font_usage[font_name]["count"] += 1
                        font_usage[font_name]["total_chars"] += text_len
                        font_usage[font_name]["sizes"].append(font_size)

        return font_usage

    def get_latex_packages(self, font_usage: Dict) -> List[str]:
        """
        Get LaTeX font packages needed based on detected fonts.
        """
        packages = set()

        for font_name in font_usage:
            name_lower = font_name.lower()
            for key, (pkg_name, pkg_cmd) in self.LATEX_FONT_PACKAGES.items():
                if key in name_lower:
                    packages.add(pkg_cmd)
                    break

        return list(packages)

    def get_base_font_size(self, font_usage: Dict) -> float:
        """
        Determine the base (most common) font size in the document.
        """
        all_sizes = []
        for info in font_usage.values():
            all_sizes.extend(info["sizes"])

        if not all_sizes:
            return 12.0

        # Find most common font size
        size_counts = {}
        for s in all_sizes:
            rounded = round(s)
            size_counts[rounded] = size_counts.get(rounded, 0) + 1

        return max(size_counts, key=size_counts.get)
