import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

drawings = page.get_drawings()
for idx in [7, 8, 9, 10, 11]:
    d = drawings[idx]
    print(f"\nDrawing {idx}:")
    for k, v in d.items():
        if k != 'items':
            print(f"  {k}: {v}")
