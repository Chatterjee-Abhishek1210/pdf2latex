import os
import fitz

uploads_dir = 'backend/uploads'
for root, dirs, files in os.walk(uploads_dir):
    for file in files:
        if file.endswith('.pdf'):
            pdf_path = os.path.join(root, file)
            try:
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                if "Sarala Birla" in text or "Fee Receipt" in text or "SBU221026" in text:
                    print(f"Found: {pdf_path}")
                    print(f"  First 200 chars: {text[:200]}")
            except Exception as e:
                pass
