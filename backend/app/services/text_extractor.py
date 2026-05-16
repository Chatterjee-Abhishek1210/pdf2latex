"""
Text Extractor — Extracts text with full formatting metadata from PDF pages.
Preserves font family, size, weight, style, color, underline, and position.
Per-span formatting is captured for mixed-style text blocks.
"""
import fitz
import re
import logging
from typing import List
from app.models.schemas import TextBlock, TextSpan, FontInfo

logger = logging.getLogger(__name__)


class TextExtractor:
    """
    Extracts text blocks from PDF pages with complete formatting information.
    Uses PyMuPDF's detailed text extraction with character-level data.
    """

    # Common font name mappings to LaTeX font families
    FONT_MAP = {
        "times": "serif",
        "arial": "sans-serif",
        "helvetica": "sans-serif",
        "courier": "monospace",
        "consolas": "monospace",
        "cambria": "serif",
        "calibri": "sans-serif",
        "georgia": "serif",
        "verdana": "sans-serif",
        "palatino": "serif",
        "garamond": "serif",
        "bookman": "serif",
        "cmr": "serif",       # Computer Modern Roman
        "cmss": "sans-serif", # Computer Modern Sans
        "cmtt": "monospace",  # Computer Modern Typewriter
    }

    def extract(self, page: fitz.Page, page_num: int) -> List[TextBlock]:
        """
        Extract all text blocks from a page with formatting metadata.
        Also gathers per-span data so the generator can reproduce
        mixed bold/italic/color within a single block.
        """
        blocks = []

        # Use "dict" mode for detailed character-level extraction
        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in page_dict.get("blocks", []):
            if block["type"] != 0:  # type 0 = text block
                continue

            block_text_parts = []
            block_fonts = []
            block_colors = []
            block_bbox = block["bbox"]
            all_spans: List[TextSpan] = []
            line_count = 0
            has_underline = False

            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    text = span["text"]
                    if not text:
                        continue

                    line_text += text
                    font_name = span.get("font", "")
                    font_size = span.get("size", 12.0)
                    font_flags = span.get("flags", 0)
                    color_int = span.get("color", 0)
                    span_bbox = span.get("bbox", block_bbox)

                    # Parse font flags (PyMuPDF flags)
                    # bit 0 = superscript, bit 1 = italic, bit 2 = serif,
                    # bit 3 = monospace, bit 4 = bold
                    is_bold = bool(font_flags & (1 << 4))
                    is_italic = bool(font_flags & (1 << 1))

                    # Detect underline from font name heuristic
                    # PyMuPDF doesn't have a direct underline flag in font_flags,
                    # but we can detect it from annotations or the font name
                    is_underline = False

                    # Convert color integer to hex
                    r = (color_int >> 16) & 0xFF
                    g = (color_int >> 8) & 0xFF
                    b = color_int & 0xFF
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"

                    family = self._map_font_family(font_name)

                    span_font = FontInfo(
                        family=family,
                        size=round(font_size, 1),
                        weight="bold" if is_bold else "normal",
                        style="italic" if is_italic else "normal",
                        color=color_hex,
                        name=font_name,
                        underline=is_underline,
                    )

                    all_spans.append(TextSpan(
                        text=text,
                        font=span_font,
                        x=span_bbox[0],
                        y=span_bbox[1],
                        width=span_bbox[2] - span_bbox[0],
                        height=span_bbox[3] - span_bbox[1],
                    ))

                    block_fonts.append({
                        "name": font_name,
                        "size": font_size,
                        "bold": is_bold,
                        "italic": is_italic,
                        "underline": is_underline,
                    })
                    block_colors.append(color_hex)

                if line_text.strip():
                    block_text_parts.append(line_text)
                    line_count += 1

            full_text = "\n".join(block_text_parts)
            if not full_text.strip():
                continue

            # Determine dominant font for this block
            font_info = self._get_dominant_font(block_fonts, block_colors)

            # Detect underline from annotations on the page
            # (underlines in PDF are often drawn as line annotations or drawings)
            underline_detected = self._check_underline_drawings(
                page, block_bbox
            )
            if underline_detected:
                font_info.underline = True
                has_underline = True

            # Detect alignment
            page_width = page.rect.width
            alignment = self._detect_alignment(
                block_bbox, page_width, full_text
            )

            text_block = TextBlock(
                text=full_text,
                x=block_bbox[0],
                y=block_bbox[1],
                width=block_bbox[2] - block_bbox[0],
                height=block_bbox[3] - block_bbox[1],
                font=font_info,
                alignment=alignment,
                page=page_num,
                spans=all_spans,
                line_count=line_count,
            )

            blocks.append(text_block)

        return blocks

    def _check_underline_drawings(self, page: fitz.Page, block_bbox) -> bool:
        """
        Check if there are any horizontal lines (drawings) directly below
        a text block, which indicates underlined text.
        """
        x0, y0, x1, y1 = block_bbox
        block_bottom = y1
        block_left = x0
        block_right = x1

        try:
            drawings = page.get_drawings()
            for d in drawings:
                for item in d.get("items", []):
                    if item[0] == "l":  # line
                        p1 = item[1]
                        p2 = item[2]
                        # Check if this is a horizontal line near the bottom of the block
                        if abs(p1.y - p2.y) < 2:  # horizontal
                            line_y = p1.y
                            line_left = min(p1.x, p2.x)
                            line_right = max(p1.x, p2.x)
                            # Line should be near the bottom of the text block
                            # and span a significant portion of the block width
                            if (abs(line_y - block_bottom) < 5 and
                                line_left <= block_left + 5 and
                                line_right >= block_right - 5):
                                return True
                            # Also check if line is within the block vertically
                            if (y0 - 2 <= line_y <= y1 + 5 and
                                line_right - line_left > (block_right - block_left) * 0.5):
                                return True
        except Exception:
            pass

        return False

    def _get_dominant_font(self, fonts: list, colors: list) -> FontInfo:
        """
        Determine the dominant font info from a list of character fonts.
        """
        if not fonts:
            return FontInfo()

        # Use the most common font properties
        sizes = [f["size"] for f in fonts]
        avg_size = sum(sizes) / len(sizes) if sizes else 12.0

        # Most common bold/italic
        bold_count = sum(1 for f in fonts if f["bold"])
        italic_count = sum(1 for f in fonts if f["italic"])
        underline_count = sum(1 for f in fonts if f.get("underline", False))
        is_bold = bold_count > len(fonts) / 2
        is_italic = italic_count > len(fonts) / 2
        is_underline = underline_count > len(fonts) / 2

        # Most common font name
        font_name = fonts[0]["name"] if fonts else ""
        family = self._map_font_family(font_name)

        # Most common color
        color = colors[0] if colors else "#000000"
        if colors:
            color_counts = {}
            for c in colors:
                color_counts[c] = color_counts.get(c, 0) + 1
            color = max(color_counts, key=color_counts.get)

        return FontInfo(
            family=family,
            size=round(avg_size, 1),
            weight="bold" if is_bold else "normal",
            style="italic" if is_italic else "normal",
            color=color,
            name=font_name,
            underline=is_underline,
        )

    def _map_font_family(self, font_name: str) -> str:
        """
        Map PDF font name to a generic family (serif, sans-serif, monospace).
        """
        name_lower = font_name.lower()
        for key, family in self.FONT_MAP.items():
            if key in name_lower:
                return family

        # Default heuristics
        if "bold" in name_lower or "italic" in name_lower:
            clean = re.sub(r'[-_]?(bold|italic|regular|medium|light|book)', '', name_lower)
            for key, family in self.FONT_MAP.items():
                if key in clean:
                    return family

        return "serif"  # default

    def _detect_alignment(self, bbox, page_width, text) -> str:
        """
        Detect text alignment based on position relative to page.
        """
        x0, y0, x1, y1 = bbox
        block_width = x1 - x0
        center_x = (x0 + x1) / 2
        page_center = page_width / 2

        # If block is narrow and centered
        if abs(center_x - page_center) < 20 and block_width < page_width * 0.6:
            return "center"

        # If right-aligned
        if x1 > page_width * 0.85 and x0 > page_width * 0.4:
            return "right"

        # If text spans most of the page width, it's likely justified
        if block_width > page_width * 0.7:
            return "justify"

        return "left"
