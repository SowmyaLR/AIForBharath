"""
PDF text extraction service using pypdf.
Handles single and multiple PDF files.
"""
import io
from typing import Union


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract raw text from a PDF given as bytes.
    Returns cleaned plain text.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def extract_text_from_file(filepath: str) -> str:
    """Extract text from a PDF file path."""
    with open(filepath, "rb") as f:
        return extract_text_from_bytes(f.read())


def clean_extracted_text(text: str) -> str:
    """
    Basic cleanup of extracted PDF text:
    - Remove excessive whitespace
    - Remove form feed characters
    - Normalize line endings
    """
    import re
    text = text.replace("\x0c", "\n")           # form feed → newline
    text = re.sub(r"\n{3,}", "\n\n", text)       # collapse 3+ blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)       # collapse multiple spaces
    return text.strip()
