import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

for idx, img_info in enumerate(page.get_image_info()):
    xref = img_info.get("xref")
    print(f"Index {idx}, xref: {xref}, keys: {list(img_info.keys())}")
    if 'image' in img_info:
        print(f"  Has image data: type={type(img_info['image'])}, len={len(img_info['image'])}")
