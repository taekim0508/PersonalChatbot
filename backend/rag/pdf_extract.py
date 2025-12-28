from pypdf import PdfReader

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages).strip()
