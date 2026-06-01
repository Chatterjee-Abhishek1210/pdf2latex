import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

for idx, img_info in enumerate(page.get_image_info(xrefs=True)):
    xref = img_info.get("xref")
    print(f"Xref: {xref}")
    try:
        pix = fitz.Pixmap(doc, xref)
        print(f"Successfully loaded Pixmap for xref {xref}")
    except Exception as e:
        print(f"Error loading Pixmap for xref {xref}: {e}")
