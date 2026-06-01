import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

drawings = page.get_drawings()
for idx, d in enumerate(drawings):
    rect = d.get('rect')
    # Look for drawings around the green circle (x in 120-150, y in 190-220)
    if rect and 120 <= rect.x0 <= 150 and 190 <= rect.y0 <= 220:
        print(f"\nDrawing {idx}: rect={rect} fill={d.get('fill')} color={d.get('color')} width={d.get('width')} type={d.get('type')}")
        print(f"  fill_opacity: {d.get('fill_opacity')}, stroke_opacity: {d.get('stroke_opacity')}")
        items = d.get('items', [])
        print(f"  items count: {len(items)}")
        for item in items:
            print(f"    {item}")
