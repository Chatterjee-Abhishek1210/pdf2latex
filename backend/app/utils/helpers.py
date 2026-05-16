"""
Utility helpers for the PDF-to-LaTeX system.
"""
import os
import uuid
import zipfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())[:12]


def create_output_directory(base_dir: str, job_id: str) -> str:
    """Create and return a job-specific output directory."""
    output_dir = os.path.join(base_dir, job_id)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    return output_dir


def create_zip_package(output_dir: str, job_id: str) -> str:
    """
    Create a ZIP package containing the LaTeX source, images, and compiled PDF.
    """
    zip_path = os.path.join(output_dir, f"{job_id}_latex_package.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".zip"):
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, output_dir)
                zf.write(filepath, arcname)

    logger.info(f"Created ZIP package: {zip_path}")
    return zip_path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system usage."""
    # Remove potentially dangerous characters
    safe = "".join(c for c in filename if c.isalnum() or c in "._-")
    return safe or "document"


def points_to_inches(points: float) -> float:
    """Convert points to inches."""
    return points / 72.0


def points_to_cm(points: float) -> float:
    """Convert points to centimeters."""
    return points / 72.0 * 2.54


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple (0-255)."""
    hex_clean = hex_color.lstrip("#")
    return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"
