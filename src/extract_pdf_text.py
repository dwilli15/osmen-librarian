import os
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path, output_path):
    """Extract text from a PDF file and save to output path."""
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


# Configuration - UPDATE THESE PATHS for your environment
# Or set via environment variables: LIBRARIAN_PDF_DIR, LIBRARIAN_OUTPUT_DIR
base_dir = os.environ.get("LIBRARIAN_PDF_DIR", "./source_pdfs")
output_dir = os.environ.get("LIBRARIAN_OUTPUT_DIR", "./data")

# Example PDF configuration - add your PDFs here
pdfs = [
    # ("your_document.pdf", "Output_Name.md"),
]


if __name__ == "__main__":
    if not pdfs:
        print("No PDFs configured. Edit this file to add your PDF sources.")
        print("Example: pdfs = [('document.pdf', 'Document.md')]")
    else:
        for pdf_file, md_file in pdfs:
            pdf_path = os.path.join(base_dir, pdf_file)
            md_path = os.path.join(output_dir, md_file)
            extract_text_from_pdf(pdf_path, md_path)
