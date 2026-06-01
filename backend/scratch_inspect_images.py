import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

# Create mapping of xref to smask
smask_map = {}
for img in page.get_images(full=True):
    xref = img[0]
    smask = img[1]
    smask_map[xref] = smask

for idx, img_info in enumerate(page.get_image_info(xrefs=True)):
    xref = img_info.get("xref")
    bbox = img_info.get("bbox")
    print(f"Image {idx}: xref={xref} smask={smask_map.get(xref)} bbox={bbox} width={img_info.get('width')} height={img_info.get('height')}")
