"""
Color Extractor — Extracts all color information from PDF elements.
"""
import fitz
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class ColorExtractor:
    """
    Extracts color information from all PDF elements including
    text, backgrounds, borders, and drawings.
    """

    def extract_page_colors(self, page: fitz.Page) -> Dict[str, Set[str]]:
        """
        Extract all colors used on a page, categorized by type.
        """
        colors = {
            "text": set(),
            "background": set(),
            "border": set(),
            "drawing": set(),
        }

        # Text colors
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        color_int = span.get("color", 0)
                        hex_color = self._int_to_hex(color_int)
                        colors["text"].add(hex_color)

        # Drawing colors
        drawings = page.get_drawings()
        for d in drawings:
            fill = d.get("fill")
            stroke = d.get("color")
            if fill:
                hex_fill = self._rgb_to_hex(fill)
                colors["background"].add(hex_fill)
            if stroke:
                hex_stroke = self._rgb_to_hex(stroke)
                colors["border"].add(hex_stroke)

        return colors

    def _int_to_hex(self, color_int: int) -> str:
        """Convert integer color to hex string."""
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"

    def _rgb_to_hex(self, rgb_tuple) -> str:
        """Convert RGB float tuple (0-1) to hex string."""
        if len(rgb_tuple) == 3:
            r, g, b = rgb_tuple
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        return "#000000"

    def get_unique_colors(self, page: fitz.Page) -> List[str]:
        """Get all unique colors used on a page."""
        all_colors = set()
        page_colors = self.extract_page_colors(page)
        for category_colors in page_colors.values():
            all_colors.update(category_colors)
        return list(all_colors)
