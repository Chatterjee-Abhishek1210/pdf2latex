"""
Export Router — Handles exporting LaTeX code, compiled PDF, and ZIP packages.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.config import OUTPUT_DIR
from app.utils.helpers import create_zip_package

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/tex/{job_id}")
async def export_tex(job_id: str):
    """
    Download the generated LaTeX source file.
    """
    tex_path = os.path.join(str(OUTPUT_DIR), job_id, "output.tex")

    if not os.path.exists(tex_path):
        raise HTTPException(status_code=404, detail="LaTeX file not found")

    return FileResponse(
        tex_path,
        media_type="application/x-tex",
        filename=f"{job_id}_output.tex",
    )


@router.get("/export/pdf/{job_id}")
async def export_pdf(job_id: str):
    """
    Download the compiled PDF.
    """
    pdf_path = os.path.join(str(OUTPUT_DIR), job_id, "output.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Compiled PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{job_id}_output.pdf",
    )


@router.get("/export/docx/{job_id}")
async def export_docx(job_id: str):
    """
    Download the generated content as a Word document (.docx).
    """
    pdf_path = os.path.join(str(OUTPUT_DIR), job_id, "output.pdf")
    docx_path = os.path.join(str(OUTPUT_DIR), job_id, "output.docx")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Compiled PDF not found")

    # If DOCX doesn't exist yet, convert it on the fly
    if not os.path.exists(docx_path):
        try:
            from pdf2docx import Converter
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None)
            cv.close()
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Failed to convert PDF to DOCX: {error_trace}")
            raise HTTPException(status_code=500, detail=f"Failed to generate Word document: {str(e)}")

    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{job_id}_output.docx",
    )


@router.get("/export/zip/{job_id}")
async def export_zip(job_id: str):
    """
    Download complete LaTeX package as ZIP (tex + images + PDF).
    """
    output_dir = os.path.join(str(OUTPUT_DIR), job_id)

    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    zip_path = create_zip_package(output_dir, job_id)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{job_id}_latex_package.zip",
    )


@router.get("/export/original/{job_id}")
async def get_original_pdf(job_id: str):
    """
    Serve the original uploaded PDF for side-by-side comparison.
    """
    from app.config import UPLOAD_DIR
    upload_dir = os.path.join(str(UPLOAD_DIR), job_id)

    if not os.path.exists(upload_dir):
        raise HTTPException(status_code=404, detail="Original PDF not found")

    pdf_files = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No PDF file found")

    return FileResponse(
        os.path.join(upload_dir, pdf_files[0]),
        media_type="application/pdf",
        filename=f"original_{pdf_files[0]}",
    )


@router.get("/preview/{job_id}/{page_num}")
async def get_page_preview(job_id: str, page_num: int = 0):
    """
    Get a page preview image of the original PDF.
    """
    import fitz
    from app.config import UPLOAD_DIR, DPI_FOR_PREVIEW

    upload_dir = os.path.join(str(UPLOAD_DIR), job_id)
    pdf_files = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]

    if not pdf_files:
        raise HTTPException(status_code=404, detail="PDF not found")

    pdf_path = os.path.join(upload_dir, pdf_files[0])
    output_dir = os.path.join(str(OUTPUT_DIR), job_id)
    os.makedirs(output_dir, exist_ok=True)

    preview_path = os.path.join(output_dir, f"preview_p{page_num}.png")

    if not os.path.exists(preview_path):
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            raise HTTPException(status_code=404, detail="Page not found")

        page = doc[page_num]
        mat = fitz.Matrix(DPI_FOR_PREVIEW / 72, DPI_FOR_PREVIEW / 72)
        pix = page.get_pixmap(matrix=mat)
        pix.save(preview_path)
        doc.close()

    return FileResponse(preview_path, media_type="image/png")
