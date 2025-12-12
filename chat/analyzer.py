# chat/analyzer.py
import os
import docx
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(filepath):
    try:
        if filepath.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif filepath.lower().endswith(".pdf"):
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif filepath.lower().endswith(".docx"):
            doc = docx.Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.exception("Failed to extract text: %s", e)
    return ""
