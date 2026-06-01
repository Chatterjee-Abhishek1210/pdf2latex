import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

from app.services.text_extractor import TextExtractor
extractor = TextExtractor()
blocks = extractor.extract(page, 0)

for idx, b in enumerate(blocks):
    print(f"\nBlock {idx}: bbox=({b.x:.1f}, {b.y:.1f}, {b.width:.1f}, {b.height:.1f}) alignment={b.alignment}")
    print(f"  text={repr(b.text)}")
    for s_idx, s in enumerate(b.spans):
        print(f"    Span {s_idx}: bbox=({s.x:.1f}, {s.y:.1f}, {s.width:.1f}, {s.height:.1f}) text={repr(s.text)}")
