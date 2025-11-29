import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path, output_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Successfully extracted text to {output_path}")
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")

base_dir = r"c:\Users\armad\OneDrive\Documents\Professional\MLTS\Timeline\Fall 2025\Courses\Healthy Boundaries\Projects\Final Project"
output_dir = os.path.join(base_dir, "hb_final", "2_sources_md")

pdfs = [
    ("__Cortina-Liotti_Attachment-Intersubjectivity_2010.pdf", "Cortina_Liotti.md"),
    ("__Gillespie-Cornish_Dialogical-Intersubjectivity.pdf", "Gillespie_Cornish.md")
]

for pdf_file, md_file in pdfs:
    pdf_path = os.path.join(base_dir, pdf_file)
    md_path = os.path.join(output_dir, md_file)
    extract_text_from_pdf(pdf_path, md_path)
