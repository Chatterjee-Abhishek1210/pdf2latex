import fitz
doc = fitz.open('backend/uploads/fc42c525-748/Front_page_dl_ac.pdf')
page = doc[0]
for img in page.get_image_info(xrefs=True):
    xref = img.get("xref")
    if xref:
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(f"backend/outputs/test_run/img_{xref}.png")
