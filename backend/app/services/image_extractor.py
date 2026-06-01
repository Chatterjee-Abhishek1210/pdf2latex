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
        Handles transparency masks (smasks) to avoid black backgrounds.
        """
        image_blocks = []

        # Build xref → smask mapping from get_images(full=True)
        # Tuple: (xref, smask, width, height, bpc, colorspace, alt, name, filter, invoker)
        smask_map = {}
        for img_tuple in page.get_images(full=True):
            xref = img_tuple[0]
            smask = img_tuple[1]
            smask_map[xref] = smask

        image_list = page.get_image_info(xrefs=True)
        page_dict = None

        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info.get("xref")
                pix = None

                if not xref or xref == 0:
                    # Extract inline image from page text dictionary
                    bbox = img_info.get("bbox")
                    if bbox:
                        if page_dict is None:
                            page_dict = page.get_text("dict")
                        for b in page_dict.get("blocks", []):
                            if b.get("type") == 1 and "image" in b:
                                b_bbox = b.get("bbox")
                                if (b_bbox and 
                                    abs(b_bbox[0] - bbox[0]) < 2 and 
                                    abs(b_bbox[1] - bbox[1]) < 2 and 
                                    abs(b_bbox[2] - bbox[2]) < 2 and 
                                    abs(b_bbox[3] - bbox[3]) < 2):
                                    try:
                                        pix = fitz.Pixmap(b["image"])
                                        break
                                    except Exception:
                                        pass
                    if not pix:
                        continue
                else:
                    # Build the pixmap
                    pix = fitz.Pixmap(page.parent, xref)

                # Convert CMYK → RGB before applying mask to preserve transparency
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                smask_xref = smask_map.get(xref, 0) if xref else 0
                if smask_xref > 0:
                    try:
                        pix_mask = fitz.Pixmap(page.parent, smask_xref)
                        # The Pixmap(base, mask) constructor requires the base
                        # to NOT have an alpha channel already.
                        if pix.alpha:
                            pix = fitz.Pixmap(pix, 0)  # drop existing alpha
                        pix = fitz.Pixmap(pix, pix_mask)
                    except Exception as e:
                        logger.warning(
                            f"Could not apply smask {smask_xref} to image "
                            f"xref {xref} on page {page_num}: {e}"
                        )

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

