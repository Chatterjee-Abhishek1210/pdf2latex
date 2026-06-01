import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

drawings = page.get_drawings()
print(f"Total drawings found: {len(drawings)}")
for idx, d in enumerate(drawings[:20]):
    print(f"\nDrawing {idx}: rect={d.get('rect')} fill={d.get('fill')} color={d.get('color')} width={d.get('width')} type={d.get('type')}")
    items = d.get('items', [])
    print(f"  items count: {len(items)}")
    for item in items[:3]:
        print(f"    {item}")
