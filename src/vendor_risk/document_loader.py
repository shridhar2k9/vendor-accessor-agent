from pathlib import Path
import fitz
from docx import Document


def load_pdf(path: str) -> list[dict]:
    pages = []
    pdf = fitz.open(path)
    try:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "text": text,
                    "source": Path(path).name,
                    "page": page_number,
                })
    finally:
        pdf.close()

    return pages


def load_docx(path: str) -> list[dict]:
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return [{
        "text": text,
        "source": Path(path).name,
        "page": None,
    }]


def load_txt(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()

    if not text:
        return []

    return [{
        "text": text,
        "source": Path(path).name,
        "page": None,
    }]


def load_document(path: str) -> list[dict]:
    suffix = Path(path).suffix.lower()
    loaders = {
        ".pdf": load_pdf,
        ".docx": load_docx,
        ".txt": load_txt,
    }

    loader = loaders.get(suffix)
    if loader is None:
        raise ValueError(f"Unsupported document type: {suffix or '(no extension)'}")

    return loader(path)