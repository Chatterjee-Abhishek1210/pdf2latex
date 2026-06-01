import fitz
doc = fitz.open('backend/uploads/fc42c525-748/Front_page_dl_ac.pdf')
page = doc[0]

print("=== page.get_images() ===")
for img in page.get_images(full=True):
    print(img)

print("\n=== page.get_image_info() ===")
for img in page.get_image_info(xrefs=True):
    print({k: v for k, v in img.items() if k != 'image'})
