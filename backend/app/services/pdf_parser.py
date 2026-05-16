"""
PDF Parser Service — Main orchestrator for PDF analysis.
Coordinates text extraction, image extraction, table detection,
layout analysis, and equation detection.
"""
import fitz  # PyMuPDF
import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from app.models.schemas import (
    DocumentStructure, PageLayout, TextBlock, TextSpan, ImageBlock,
    TableBlock, EquationBlock, DrawingElement, FontInfo, ConversionStatus
)
from app.services.text_extractor import TextExtractor
from app.services.image_extractor import ImageExtractor
from app.services.table_detector import TableDetector
from app.services.layout_analyzer import LayoutAnalyzer
from app.services.equation_detector import EquationDetector
from app.services.color_extractor import ColorExtractor
from app.services.font_analyzer import FontAnalyzer

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Main PDF parsing pipeline that orchestrates all extraction services.
    """

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)

        self.doc = fitz.open(pdf_path)
        self.text_extractor = TextExtractor()
        self.image_extractor = ImageExtractor(self.images_dir)
        self.table_detector = TableDetector()
        self.layout_analyzer = LayoutAnalyzer()
        self.equation_detector = EquationDetector()
        self.color_extractor = ColorExtractor()
        self.font_analyzer = FontAnalyzer()

    def parse(self, progress_callback=None) -> DocumentStructure:
        """
        Full parsing pipeline: extracts all document elements.
        """
        logger.info(f"Starting PDF parsing: {self.pdf_path}")

        total_pages = len(self.doc)
        all_text_blocks = []
        all_image_blocks = []
        all_table_blocks = []
        all_equation_blocks = []
        page_layouts = []

        for page_num in range(total_pages):
            page = self.doc[page_num]
            logger.info(f"Processing page {page_num + 1}/{total_pages}")

            if progress_callback:
                progress = (page_num / total_pages) * 80
                progress_callback(progress, f"Analyzing page {page_num + 1}/{total_pages}")

            # 1. Layout analysis
            layout = self.layout_analyzer.analyze_page(page, page_num)
            page_layouts.append(layout)

            # 2. Text extraction with formatting
            text_blocks = self.text_extractor.extract(page, page_num)
            all_text_blocks.extend(text_blocks)

            # 3. Image extraction
            image_blocks = self.image_extractor.extract(page, page_num)
            all_image_blocks.extend(image_blocks)

            # 4. Table detection
            table_blocks = self.table_detector.detect(page, page_num)
            all_table_blocks.extend(table_blocks)

            # 5. Equation detection
            equation_blocks = self.equation_detector.detect(
                page, page_num, text_blocks
            )
            all_equation_blocks.extend(equation_blocks)

        # Extract document metadata
        metadata = self.doc.metadata or {}
        title = metadata.get("title", None)
        author = metadata.get("author", None)

        # Classify text blocks (headings, paragraphs, etc.)
        all_text_blocks = self._classify_blocks(all_text_blocks)

        # Remove text blocks that overlap with tables
        all_text_blocks = self._remove_table_overlaps(
            all_text_blocks, all_table_blocks
        )

        structure = DocumentStructure(
            pages=total_pages,
            page_layouts=page_layouts,
            text_blocks=all_text_blocks,
            image_blocks=all_image_blocks,
            table_blocks=all_table_blocks,
            equation_blocks=all_equation_blocks,
            title=title,
            author=author,
            metadata=metadata,
        )

        if progress_callback:
            progress_callback(85, "Document structure analysis complete")

        logger.info(
            f"Parsing complete: {len(all_text_blocks)} text blocks, "
            f"{len(all_image_blocks)} images, {len(all_table_blocks)} tables, "
            f"{len(all_equation_blocks)} equations"
        )

        self.doc.close()
        return structure

    def _classify_blocks(self, text_blocks: list) -> list:
        """
        Classify text blocks as headings, titles, paragraphs, etc.
        based on font size, weight, and position.
        """
        if not text_blocks:
            return text_blocks

        # Compute font size statistics
        sizes = [b.font.size for b in text_blocks if b.text.strip()]
        if not sizes:
            return text_blocks

        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)

        for block in text_blocks:
            size = block.font.size
            is_bold = block.font.weight == "bold"
            text = block.text.strip()

            if not text:
                continue

            # Title: largest font or significantly larger than average
            if size >= max_size * 0.9 and size > avg_size * 1.5:
                block.block_type = "title"
                block.level = 0
            # Major heading
            elif size > avg_size * 1.3 and is_bold:
                block.block_type = "heading"
                block.level = 1
            # Sub-heading
            elif size > avg_size * 1.1 and is_bold:
                block.block_type = "heading"
                block.level = 2
            # Minor heading (bold at normal size)
            elif is_bold and len(text) < 100:
                block.block_type = "heading"
                block.level = 3
            else:
                block.block_type = "paragraph"

        return text_blocks

    def _remove_table_overlaps(self, text_blocks, table_blocks):
        """
        Remove text blocks that fall within detected table regions.
        """
        if not table_blocks:
            return text_blocks

        filtered = []
        for tb in text_blocks:
            overlaps = False
            for table in table_blocks:
                if (tb.page == table.page and
                    tb.x >= table.x - 5 and
                    tb.y >= table.y - 5 and
                    tb.x + tb.width <= table.x + table.width + 5 and
                    tb.y + tb.height <= table.y + table.height + 5):
                    overlaps = True
                    break
            if not overlaps:
                filtered.append(tb)
        return filtered
