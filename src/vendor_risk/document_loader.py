from pathlib import Path
import fitz
from docx import Document


def load_pdf(path: str) -> list[dict]:
    pages = []
    pdf = fitz.open(path)

    for page_number, page in enumerate(pdf, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({
                "text": text,
                "source": Path(path).name,
                "page": page_number,
            })

    return pages


def load_docx(path: str) -> list[dict]:
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return [{
        "text": text,
        "source": Path(path).name,
        "page": None,
    }]