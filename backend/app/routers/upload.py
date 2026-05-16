"""
Upload Router — Handles PDF file uploads.
"""
import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.config import UPLOAD_DIR, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from app.utils.helpers import generate_job_id, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for conversion.
    Returns a job_id for tracking the conversion.
    """
    # Validate file extension
    filename = file.filename or "document.pdf"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size_mb:.1f}MB. Maximum: {MAX_FILE_SIZE_MB}MB"
        )

    # Generate job ID and save file
    job_id = generate_job_id()
    safe_filename = sanitize_filename(filename)
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    file_path = os.path.join(job_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded PDF: {safe_filename} ({file_size_mb:.1f}MB) -> job {job_id}")

    return JSONResponse(content={
        "job_id": job_id,
        "filename": safe_filename,
        "size_mb": round(file_size_mb, 2),
        "status": "uploaded",
        "message": "PDF uploaded successfully. Ready for conversion."
    })
