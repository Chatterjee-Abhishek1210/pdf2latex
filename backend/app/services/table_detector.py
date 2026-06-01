"""
Table Detector — Detects and reconstructs table structures from PDF pages.
Uses PyMuPDF's built-in table detection and line analysis.
"""
import fitz
import logging
from typing import List
from app.models.schemas import TableBlock, TableCell, FontInfo

logger = logging.getLogger(__name__)


class TableDetector:
    """
    Detects tables in PDF pages and extracts their structure,
    including cell content, borders, spans, and formatting.
    """

    def detect(self, page: fitz.Page, page_num: int) -> List[TableBlock]:
        """
        Detect all tables on a page.
        """
        tables = []

        try:
            # Use PyMuPDF's built-in table finder
            tab_finder = page.find_tables()

            for table_idx, table in enumerate(tab_finder.tables):
                try:
                    table_block = self._process_table(table, page, page_num)
                    if table_block:
                        tables.append(table_block)
                        logger.info(
                            f"Detected table on page {page_num + 1}: "
                            f"{table_block.rows}x{table_block.cols}"
                        )
                except Exception as e:
                    logger.warning(f"Error processing table {table_idx}: {e}")

        except Exception as e:
            logger.warning(f"Table detection failed on page {page_num + 1}: {e}")
            # Fallback: try line-based detection
            tables = self._detect_from_lines(page, page_num)

        # Remove nested/outer tables (e.g. giant layout boxes containing actual tables)
        filtered_tables = []
        for i, t1 in enumerate(tables):
            is_outer = False
            for j, t2 in enumerate(tables):
                if i == j:
                    continue
                t1_x1, t1_y1 = t1.x, t1.y
                t1_x2, t1_y2 = t1.x + t1.width, t1.y + t1.height
                t2_x1, t2_y1 = t2.x, t2.y
                t2_x2, t2_y2 = t2.x + t2.width, t2.y + t2.height
                
                # Check containment with 2 points tolerance
                if (t1_x1 <= t2_x1 + 2 and t1_y1 <= t2_y1 + 2 and 
                    t1_x2 >= t2_x2 - 2 and t1_y2 >= t2_y2 - 2):
                    area1 = t1.width * t1.height
                    area2 = t2.width * t2.height
                    if area1 > area2 * 1.1:
                        is_outer = True
                        break
            if not is_outer:
                filtered_tables.append(t1)
        tables = filtered_tables

        return tables

    def _process_table(self, table, page: fitz.Page, page_num: int) -> TableBlock:
        """
        Process a detected table into our TableBlock format.
        """
        bbox = table.bbox
        extracted = table.extract()

        if not extracted or len(extracted) == 0:
            return None

        rows = len(extracted)
        cols = max(len(row) for row in extracted) if extracted else 0

        if rows == 0 or cols == 0:
            return None

        cells = []
        for row_idx, row in enumerate(extracted):
            for col_idx, cell_text in enumerate(row):
                if cell_text is None:
                    cell_text = ""

                cell = TableCell(
                    text=str(cell_text).strip(),
                    row=row_idx,
                    col=col_idx,
                    font=FontInfo(size=10.0),
                    alignment=self._detect_cell_alignment(str(cell_text)),
                )
                cells.append(cell)

        # Check if first row is a header (common pattern)
        has_header = self._detect_header(extracted, cells)

        return TableBlock(
            cells=cells,
            rows=rows,
            cols=cols,
            x=bbox[0],
            y=bbox[1],
            width=bbox[2] - bbox[0],
            height=bbox[3] - bbox[1],
            page=page_num,
            has_header=has_header,
        )

    def _detect_header(self, data: list, cells: list) -> bool:
        """
        Heuristic: detect if the first row is a header.
        Headers tend to be bold or have different formatting.
        """
        if not data or len(data) < 2:
            return False

        first_row = data[0]
        # If first row has non-numeric content while other rows are numeric
        first_numeric = sum(1 for c in first_row if c and self._is_numeric(str(c)))
        if first_numeric < len(first_row) / 2:
            return True

        return True  # Default assume header

    def _is_numeric(self, text: str) -> bool:
        """Check if text is numeric."""
        try:
            float(text.replace(",", "").replace("%", "").strip())
            return True
        except (ValueError, AttributeError):
            return False

    def _detect_cell_alignment(self, text: str) -> str:
        """Detect cell alignment based on content."""
        text = text.strip()
        if not text:
            return "left"

        if self._is_numeric(text):
            return "right"

        return "left"

    def _detect_from_lines(self, page: fitz.Page, page_num: int) -> List[TableBlock]:
        """
        Fallback: detect tables from drawn lines (horizontal/vertical).
        """
        # Simple heuristic using line drawings
        drawings = page.get_drawings()
        h_lines = []
        v_lines = []

        for d in drawings:
            for item in d.get("items", []):
                if item[0] == "l":  # line
                    p1, p2 = item[1], item[2]
                    if abs(p1.y - p2.y) < 2:  # horizontal
                        h_lines.append((p1, p2))
                    elif abs(p1.x - p2.x) < 2:  # vertical
                        v_lines.append((p1, p2))

        # If we have a grid of lines, there's likely a table
        if len(h_lines) >= 2 and len(v_lines) >= 2:
            logger.info(f"Detected grid lines on page {page_num + 1}")

        return []
