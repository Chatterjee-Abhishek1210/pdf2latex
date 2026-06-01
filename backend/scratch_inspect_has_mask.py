import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

for idx, img_info in enumerate(page.get_image_info(xrefs=True)):
    xref = img_info.get("xref")
    has_mask = img_info.get("has-mask")
    print(f"Image {idx}: xref={xref}, has-mask={has_mask}")
