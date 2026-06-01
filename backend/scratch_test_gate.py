import logging
import sys
import os
import importlib

import app.models.schemas
import app.services.image_extractor
import app.services.layout_analyzer
import app.services.latex_generator
importlib.reload(app.models.schemas)
importlib.reload(app.services.image_extractor)
importlib.reload(app.services.layout_analyzer)
importlib.reload(app.services.latex_generator)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from app.services.pdf_parser import PDFParser
from app.services.latex_generator import LaTeXGenerator

output_dir = 'backend/outputs/scratch_gate_test'
os.makedirs(output_dir, exist_ok=True)

parser = PDFParser(
    pdf_path='backend/uploads/6c3664e8-71b/GATE_recipt.pdf',
    output_dir=output_dir
)
structure = parser.parse()

print(f"\n=== Images: {len(structure.image_blocks)} ===")
for img in structure.image_blocks:
    print(f"  {img.filename}: pos=({img.x:.1f},{img.y:.1f}) size=({img.width:.1f}x{img.height:.1f})")

print(f"\n=== Drawings (first 10): {len(structure.page_layouts[0].drawings)} total ===")
for d in structure.page_layouts[0].drawings[:10]:
    print(f"  type={d.draw_type} fill={d.fill_color} opacity={d.fill_opacity:.3f} path_len={len(d.path_data)}")

gen = LaTeXGenerator()
latex = gen.generate(structure)

tex_path = os.path.join(output_dir, 'output.tex')
with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(latex)
print(f"\nWrote {len(latex)} chars to {tex_path}")
