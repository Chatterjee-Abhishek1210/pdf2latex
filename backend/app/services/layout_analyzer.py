"""
Layout Analyzer — Analyzes page layout including margins, columns, structure,
and all drawn shapes (rectangles, lines, paths) for pixel-perfect reproduction.
"""
import fitz
import logging
from typing import List
from app.models.schemas import PageLayout, DrawingElement

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """
    Analyzes the layout structure of each PDF page including:
    - Page dimensions
    - Margins
    - Column structure
    - Background color
    - Headers and footers
    - All drawn shapes (filled rectangles, borders, lines, rules)
    """

    def analyze_page(self, page: fitz.Page, page_num: int) -> PageLayout:
        """
        Analyze a single page's layout.
        """
        rect = page.rect
        width = rect.width
        height = rect.height

        # Detect margins from text/content blocks
        margins = self._detect_margins(page)

        # Detect column layout
        columns, column_gap = self._detect_columns(page, margins)

        # Detect background color
        bg_color = self._detect_background_color(page)

        # Detect headers and footers
        header_text, footer_text = self._detect_header_footer(page, margins)

        # Extract all drawn shapes (rectangles, lines, filled rects)
        drawings = self._extract_drawings(page, page_num)

        layout = PageLayout(
            width=width,
            height=height,
            margin_top=margins["top"],
            margin_bottom=margins["bottom"],
            margin_left=margins["left"],
            margin_right=margins["right"],
            columns=columns,
            column_gap=column_gap,
            bg_color=bg_color,
            has_header=bool(header_text),
            has_footer=bool(footer_text),
            header_text=header_text,
            footer_text=footer_text,
            page_num=page_num,
            drawings=drawings,
        )

        logger.debug(
            f"Page {page_num + 1} layout: {width:.0f}x{height:.0f}pt, "
            f"margins: T{margins['top']:.0f} B{margins['bottom']:.0f} "
            f"L{margins['left']:.0f} R{margins['right']:.0f}, "
            f"columns: {columns}, drawings: {len(drawings)}"
        )

        return layout

    def _detect_margins(self, page: fitz.Page) -> dict:
        """
        Detect page margins by finding the bounding box of all content.
        """
        rect = page.rect
        blocks = page.get_text("blocks")

        if not blocks:
            # Default margins (1 inch = 72 points)
            return {"top": 72, "bottom": 72, "left": 72, "right": 72}

        min_x = min(b[0] for b in blocks)
        min_y = min(b[1] for b in blocks)
        max_x = max(b[2] for b in blocks)
        max_y = max(b[3] for b in blocks)

        return {
            "top": max(min_y, 36),      # At least 0.5 inch
            "bottom": max(rect.height - max_y, 36),
            "left": max(min_x, 36),
            "right": max(rect.width - max_x, 36),
        }

    def _detect_columns(self, page: fitz.Page, margins: dict) -> tuple:
        """
        Detect multi-column layout by analyzing text block x-positions.
        """
        blocks = page.get_text("blocks")
        if not blocks:
            return 1, 20

        rect = page.rect
        content_width = rect.width - margins["left"] - margins["right"]

        # Collect x-positions of block centers
        centers = [(b[0] + b[2]) / 2 for b in blocks if b[4].strip()]

        if not centers or content_width < 200:
            return 1, 20

        # Check for bimodal distribution (2 columns)
        page_center = rect.width / 2
        left_blocks = sum(1 for c in centers if c < page_center - 20)
        right_blocks = sum(1 for c in centers if c > page_center + 20)

        if left_blocks > 2 and right_blocks > 2:
            # Detect gap between columns
            left_max_x = max(b[2] for b in blocks if (b[0] + b[2]) / 2 < page_center - 20)
            right_min_x = min(b[0] for b in blocks if (b[0] + b[2]) / 2 > page_center + 20)
            gap = right_min_x - left_max_x

            if gap > 10:
                return 2, max(gap, 20)

        return 1, 20

    def _detect_background_color(self, page: fitz.Page) -> str:
        """
        Detect the background color of a page.
        """
        # Check for filled rectangles covering the whole page
        drawings = page.get_drawings()
        rect = page.rect

        for d in drawings:
            d_rect = d.get("rect")
            fill = d.get("fill")
            if d_rect and fill:
                # Check if this rectangle covers most of the page
                if (d_rect.width > rect.width * 0.9 and
                    d_rect.height > rect.height * 0.9):
                    r, g, b = fill
                    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        return "#ffffff"

    def _detect_header_footer(self, page: fitz.Page, margins: dict) -> tuple:
        """
        Detect header and footer text.
        """
        blocks = page.get_text("blocks")
        rect = page.rect
        header_text = ""
        footer_text = ""

        for block in blocks:
            if block[4] is None:
                continue
            text = block[4].strip() if isinstance(block[4], str) else str(block[4]).strip()
            if not text:
                continue

            # Header: text in the top margin area
            if block[1] < margins["top"] * 0.7:
                header_text = text

            # Footer: text in the bottom margin area
            if block[3] > rect.height - margins["bottom"] * 0.7:
                footer_text = text

        return header_text, footer_text

    def _extract_drawings(self, page: fitz.Page, page_num: int) -> List[DrawingElement]:
        """
        Extract all drawn shapes from a page:
        filled rectangles, stroked rectangles, lines, and rules.
        These are essential for reproducing borders, shading, and
        decorative elements pixel-perfectly.
        """
        elements = []
        page_rect = page.rect

        try:
            drawings = page.get_drawings()
        except Exception as e:
            logger.warning(f"Could not extract drawings from page {page_num + 1}: {e}")
            return elements

        for d in drawings:
            fill = d.get("fill")
            stroke_color = d.get("color")
            stroke_width = d.get("width")
            if stroke_width is None:
                stroke_width = 0.5
            d_rect = d.get("rect")

            # Convert fill/stroke to hex
            fill_hex = None
            if fill is not None:
                try:
                    r, g, b = fill[0], fill[1], fill[2]
                    fill_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                except (IndexError, TypeError):
                    pass

            stroke_hex = None
            if stroke_color is not None:
                try:
                    r, g, b = stroke_color[0], stroke_color[1], stroke_color[2]
                    stroke_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                except (IndexError, TypeError):
                    pass

            # Skip page-sized background fills (already captured as bg_color)
            if d_rect and fill_hex:
                if (d_rect.width > page_rect.width * 0.9 and
                    d_rect.height > page_rect.height * 0.9):
                    continue

            # Process each drawing item
            items = d.get("items", [])
            for item in items:
                kind = item[0]  # "l" = line, "re" = rect, "qu" = quad, "c" = curve

                if kind == "re":
                    # Rectangle
                    r = item[1]  # fitz.Rect
                    # Skip very tiny or invisible rects
                    if r.width < 0.5 and r.height < 0.5:
                        continue
                    elements.append(DrawingElement(
                        draw_type="rect",
                        x=r.x0,
                        y=r.y0,
                        width=r.width,
                        height=r.height,
                        page=page_num,
                        fill_color=fill_hex,
                        stroke_color=stroke_hex,
                        stroke_width=stroke_width if stroke_hex else 0,
                    ))

                elif kind == "l":
                    # Line
                    p1 = item[1]  # fitz.Point
                    p2 = item[2]  # fitz.Point
                    elements.append(DrawingElement(
                        draw_type="line",
                        x=p1.x,
                        y=p1.y,
                        x2=p2.x,
                        y2=p2.y,
                        width=0,
                        height=0,
                        page=page_num,
                        fill_color=None,
                        stroke_color=stroke_hex or "#000000",
                        stroke_width=stroke_width,
                    ))

            # If no items but we have a rect with fill/stroke, use d_rect
            if not items and d_rect:
                if fill_hex or stroke_hex:
                    if d_rect.width >= 0.5 or d_rect.height >= 0.5:
                        elements.append(DrawingElement(
                            draw_type="rect",
                            x=d_rect.x0,
                            y=d_rect.y0,
                            width=d_rect.width,
                            height=d_rect.height,
                            page=page_num,
                            fill_color=fill_hex,
                            stroke_color=stroke_hex,
                            stroke_width=stroke_width if stroke_hex else 0,
                        ))

        logger.debug(f"Extracted {len(elements)} drawing elements from page {page_num + 1}")
        return elements
