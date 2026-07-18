from pathlib import Path
from pypdf import PdfReader
from rag.cleaner import clean_text


def load_pdf(pdf_path: str):
    reader = PdfReader(pdf_path)
    source = Path(pdf_path).name

    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        if not text:
            continue

        pages.append({
            "source": source,
            "page": i + 1,
            "text": clean_text(text)
        })

    return pages