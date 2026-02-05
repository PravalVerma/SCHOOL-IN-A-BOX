"""
OCR utilities for School in a Box.
Uses Tesseract via pytesseract to extract text from images.
"""

from __future__ import annotations

from PIL import Image
import pytesseract
import io
import os
import platform

# import subprocess
# print(subprocess.run(["tesseract", "--version"], capture_output=True).stdout)



def _configure_tesseract():
    """
    Configure Tesseract path if needed.
    On Linux (HF Spaces), Tesseract is usually in PATH.
    On Windows, set explicit path if necessary.
    """
    if platform.system() == "Windows":
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path


_configure_tesseract()


def extract_text_from_image(image_bytes: bytes, lang: str = "eng") -> str:
    image = Image.open(io.BytesIO(image_bytes))
    try:
        text: str = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        return f"OCR error: {str(e)}"
    
