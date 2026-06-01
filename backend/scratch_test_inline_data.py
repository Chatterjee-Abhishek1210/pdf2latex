import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

for idx, img_info in enumerate(page.get_image_info(xrefs=True)):
    xref = img_info.get("xref")
    if xref == 0:
        print(f"\nInline image {idx}: keys: {list(img_info.keys())}")
        image_data = img_info.get("image")
        if image_data:
            print(f"  image data type: {type(image_data)}, length: {len(image_data)}")
            try:
                # Can we load it using fitz.Pixmap(img_info.get("image")) or fitz.Pixmap(None, image_data)?
                pix = fitz.Pixmap(image_data)
                print("  Successfully loaded Pixmap from raw image data!")
            except Exception as e:
                print(f"  Error loading Pixmap from raw image data: {e}")
