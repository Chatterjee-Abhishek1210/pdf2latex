import fitz
import os

doc = fitz.open('backend/uploads/fc42c525-748/Front_page_dl_ac.pdf')
page = doc[0]
os.makedirs('backend/outputs/test_smask', exist_ok=True)

# Create mapping of xref to smask
smask_map = {}
for img in page.get_images(full=True):
    xref = img[0]
    smask = img[1]
    smask_map[xref] = smask

print("Xref -> Smask:", smask_map)

for img_info in page.get_image_info(xrefs=True):
    xref = img_info.get("xref")
    if not xref:
        continue
    
    smask = smask_map.get(xref, 0)
    print(f"Extracting xref {xref} with smask {smask}...")
    
    try:
        pix_base = fitz.Pixmap(doc, xref)
        if smask > 0:
            pix_mask = fitz.Pixmap(doc, smask)
            # Remove alpha channel from base image if it already has one
            if pix_base.alpha:
                pix_base = fitz.Pixmap(pix_base, 0)
            # Create a combined pixmap with alpha channel
            pix = fitz.Pixmap(pix_base, pix_mask)
        else:
            pix = pix_base
            
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
            
        pix.save(f"backend/outputs/test_smask/img_{xref}.png")
        print(f"Saved img_{xref}.png successfully!")
    except Exception as e:
        print(f"Error on xref {xref}: {e}")
