import logging
import sys
from app.services.pdf_parser import PDFParser

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

parser = PDFParser(
    pdf_path='backend/uploads/6c3664e8-71b/GATE_recipt.pdf',
    output_dir='backend/outputs/scratch_run'
)
structure = parser.parse()

print("\n=== Extracted Image Blocks ===")
for img in structure.image_blocks:
    print(f"Filename: {img.filename}, x={img.x}, y={img.y}, w={img.width}, h={img.height}")
