"""
Image Extractor — Extracts all images from PDF pages at original quality.
Preserves transparency, positioning, and scaling information.
"""
import fitz
import os
import logging
from typing import List
from PIL import Image
import io

from app.models.schemas import ImageBlock

logger = logging.getLogger(__name__)


class ImageExtractor:
    """
    Extracts embedded images from PDF pages and saves them
    to the output directory with original quality.
    """

    def __init__(self, images_dir: str):
        self.images_dir = images_dir
        self.image_counter = 0

    def extract(self, page: fitz.Page, page_num: int) -> List[ImageBlock]:
        """
        Extract all images from a PDF page.
        """
        image_blocks = []
        image_list = page.get_image_info(xrefs=True)

        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info.get("xref")
                if not xref:
                    continue

                # Skip images with masks (drop shadows, etc.) as they render as black rectangles
                if img_info.get("has-mask", False):
                    logger.info(f"Skipping masked image/shadow (xref {xref}) to prevent black rectangles.")
                    continue

                # Use Pixmap to correctly handle transparency and smasks
                pix = fitz.Pixmap(page.parent, xref)

                if not pix:
                    continue

                # Convert colorspace to RGB if it's CMYK or others
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                image_ext = "png"
                width = pix.width
                height = pix.height

                # Generate filename
                self.image_counter += 1
                filename = f"image_p{page_num + 1}_{self.image_counter}.{image_ext}"
                filepath = os.path.join(self.images_dir, filename)

                # Save image
                pix.save(filepath)

                bbox = img_info.get("bbox")

                image_block = ImageBlock(
                    filename=filename,
                    x=bbox[0] if bbox else 0,
                    y=bbox[1] if bbox else 0,
                    width=bbox[2] - bbox[0] if bbox else width,
                    height=bbox[3] - bbox[1] if bbox else height,
                    page=page_num,
                    original_width=width,
                    original_height=height,
                )

                image_blocks.append(image_block)
                logger.info(f"Extracted image: {filename} ({width}x{height})")

            except Exception as e:
                logger.error(f"Error extracting image {img_index} on page {page_num}: {e}")

        return image_blocks

