import fitz
def extract_pdf_text(path):
    with fitz.open(path) as doc:
        return "\n\n".join(f"[Halaman {i+1}]\n{p.get_text('text').strip()}" for i,p in enumerate(doc) if p.get_text("text").strip()).strip()
