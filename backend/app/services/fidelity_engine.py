"""
Fidelity Engine — Compares original and generated PDFs for visual similarity.
Uses SSIM, pixel-level comparison, and structural analysis.
"""
import fitz
import numpy as np
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    logger.warning("scikit-image not available, SSIM comparison disabled")


class FidelityEngine:
    """
    Visual comparison engine that measures the similarity
    between the original PDF and the generated PDF.
    """

    def __init__(self, dpi: int = 150):
        self.dpi = dpi

    def compare(self, original_pdf: str, generated_pdf: str) -> dict:
        """
        Compare two PDFs and return similarity metrics.
        """
        result = {
            "ssim_score": 0.0,
            "pixel_match_percentage": 0.0,
            "structural_accuracy": 0.0,
            "color_accuracy": 0.0,
            "page_scores": [],
            "overall_score": 0.0,
        }

        try:
            orig_doc = fitz.open(original_pdf)
            gen_doc = fitz.open(generated_pdf)

            # Compare page by page
            min_pages = min(len(orig_doc), len(gen_doc))
            page_scores = []

            for page_num in range(min_pages):
                score = self._compare_pages(
                    orig_doc[page_num], gen_doc[page_num]
                )
                page_scores.append(score)

            orig_doc.close()
            gen_doc.close()

            if page_scores:
                result["page_scores"] = page_scores
                result["ssim_score"] = np.mean([s["ssim"] for s in page_scores])
                result["pixel_match_percentage"] = np.mean(
                    [s["pixel_match"] for s in page_scores]
                )
                result["structural_accuracy"] = np.mean(
                    [s["structural"] for s in page_scores]
                )
                result["color_accuracy"] = np.mean(
                    [s["color"] for s in page_scores]
                )
                result["overall_score"] = (
                    result["ssim_score"] * 0.4 +
                    result["pixel_match_percentage"] * 0.3 +
                    result["structural_accuracy"] * 0.2 +
                    result["color_accuracy"] * 0.1
                )

        except Exception as e:
            logger.error(f"Fidelity comparison failed: {e}")

        return result

    def _compare_pages(self, orig_page, gen_page) -> dict:
        """
        Compare two PDF pages.
        """
        score = {
            "ssim": 0.0,
            "pixel_match": 0.0,
            "structural": 0.0,
            "color": 0.0,
        }

        try:
            # Render pages to images
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            orig_pix = orig_page.get_pixmap(matrix=mat)
            gen_pix = gen_page.get_pixmap(matrix=mat)

            # Convert to numpy arrays
            orig_img = np.frombuffer(orig_pix.samples, dtype=np.uint8).reshape(
                orig_pix.height, orig_pix.width, orig_pix.n
            )
            gen_img = np.frombuffer(gen_pix.samples, dtype=np.uint8).reshape(
                gen_pix.height, gen_pix.width, gen_pix.n
            )

            # Resize to match dimensions if needed
            min_h = min(orig_img.shape[0], gen_img.shape[0])
            min_w = min(orig_img.shape[1], gen_img.shape[1])
            orig_crop = orig_img[:min_h, :min_w]
            gen_crop = gen_img[:min_h, :min_w]

            # Ensure same number of channels
            if orig_crop.shape[2] != gen_crop.shape[2]:
                min_c = min(orig_crop.shape[2], gen_crop.shape[2])
                orig_crop = orig_crop[:, :, :min_c]
                gen_crop = gen_crop[:, :, :min_c]

            # SSIM
            if SSIM_AVAILABLE:
                try:
                    # Convert to grayscale for SSIM
                    orig_gray = np.mean(orig_crop[:, :, :3], axis=2).astype(np.uint8)
                    gen_gray = np.mean(gen_crop[:, :, :3], axis=2).astype(np.uint8)

                    score["ssim"] = float(ssim(orig_gray, gen_gray))
                except Exception as e:
                    logger.warning(f"SSIM calculation failed: {e}")

            # Pixel match percentage
            diff = np.abs(orig_crop.astype(float) - gen_crop.astype(float))
            threshold = 30  # Allow small differences
            matching_pixels = np.sum(diff < threshold) / diff.size
            score["pixel_match"] = float(matching_pixels)

            # Structural comparison (edges)
            try:
                import cv2
                orig_edges = cv2.Canny(
                    cv2.cvtColor(orig_crop[:, :, :3], cv2.COLOR_RGB2GRAY), 50, 150
                )
                gen_edges = cv2.Canny(
                    cv2.cvtColor(gen_crop[:, :, :3], cv2.COLOR_RGB2GRAY), 50, 150
                )
                edge_match = np.sum(orig_edges == gen_edges) / orig_edges.size
                score["structural"] = float(edge_match)
            except ImportError:
                score["structural"] = score["ssim"]

            # Color accuracy
            orig_mean_color = np.mean(orig_crop[:, :, :3], axis=(0, 1))
            gen_mean_color = np.mean(gen_crop[:, :, :3], axis=(0, 1))
            color_diff = np.mean(np.abs(orig_mean_color - gen_mean_color))
            score["color"] = float(max(0, 1 - color_diff / 255))

        except Exception as e:
            logger.error(f"Page comparison error: {e}")

        return score

    def generate_diff_image(self, original_pdf: str, generated_pdf: str,
                            page_num: int, output_path: str) -> Optional[str]:
        """
        Generate a visual diff image highlighting differences.
        """
        try:
            orig_doc = fitz.open(original_pdf)
            gen_doc = fitz.open(generated_pdf)

            if page_num >= len(orig_doc) or page_num >= len(gen_doc):
                return None

            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            orig_pix = orig_doc[page_num].get_pixmap(matrix=mat)
            gen_pix = gen_doc[page_num].get_pixmap(matrix=mat)

            orig_img = np.frombuffer(orig_pix.samples, dtype=np.uint8).reshape(
                orig_pix.height, orig_pix.width, orig_pix.n
            )
            gen_img = np.frombuffer(gen_pix.samples, dtype=np.uint8).reshape(
                gen_pix.height, gen_pix.width, gen_pix.n
            )

            min_h = min(orig_img.shape[0], gen_img.shape[0])
            min_w = min(orig_img.shape[1], gen_img.shape[1])

            diff = np.abs(
                orig_img[:min_h, :min_w, :3].astype(float) -
                gen_img[:min_h, :min_w, :3].astype(float)
            )

            # Normalize and colorize differences
            diff_normalized = (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)

            from PIL import Image
            diff_image = Image.fromarray(diff_normalized)
            diff_image.save(output_path)

            orig_doc.close()
            gen_doc.close()

            return output_path

        except Exception as e:
            logger.error(f"Diff image generation failed: {e}")
            return None
