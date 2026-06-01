import fitz
doc = fitz.open('backend/uploads/6c3664e8-71b/GATE_recipt.pdf')
page = doc[0]

page_dict = page.get_text("dict")
print(f"Total blocks: {len(page_dict.get('blocks', []))}")
for idx, b in enumerate(page_dict.get('blocks', [])):
    if b.get('type') == 1: # Image block
        print(f"\nImage Block {idx}:")
        print(f"  bbox: {b.get('bbox')}")
        print(f"  width: {b.get('width')}")
        print(f"  height: {b.get('height')}")
        print(f"  ext: {b.get('ext')}")
        print(f"  keys: {list(b.keys())}")
        if 'image' in b:
            print(f"  image bytes length: {len(b['image'])}")
            try:
                pix = fitz.Pixmap(b['image'])
                print(f"  Successfully loaded Pixmap! colorspace={pix.colorspace}, alpha={pix.alpha}")
            except Exception as e:
                print(f"  Error loading Pixmap: {e}")
