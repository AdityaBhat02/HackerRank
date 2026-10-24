import os
import glob
import pdfplumber

print("--- Inspecting PDFs ---")
for p in glob.glob('dataset/evidence/documents/*.pdf'):
    print(f"\nPDF: {p}")
    try:
        with pdfplumber.open(p) as pdf:
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text()
                print(f"Page {i+1} ({len(txt) if txt else 0} chars):")
                if txt:
                    for line in txt.split('\n')[:10]:
                        print("  ", line)
    except Exception as e:
        print("Error reading PDF:", e)
