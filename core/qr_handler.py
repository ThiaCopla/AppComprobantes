import os
from io import BytesIO

import cv2
import numpy as np
import qrcode
from PIL import Image


# ── QR generation ────────────────────────────────────────────────────────────

def make_qr_image(content: str) -> Image.Image:
    """Return a PIL Image of the QR code for the given content."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    wrapper = qr.make_image(fill_color="black", back_color="white")
    # Convert via BytesIO so we always get a plain PIL Image
    buf = BytesIO()
    wrapper.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf).copy()


def build_qr_content(nombre: str, precio: str, numero: str, hmac_hash: str) -> str:
    return f"{nombre}|{precio}|{numero}|{hmac_hash}"


def parse_qr_content(content: str):
    """Return dict with nombre/precio/numero/hash or None if format is invalid."""
    parts = content.split("|")
    if len(parts) != 4:
        return None
    return {
        "nombre": parts[0],
        "precio": parts[1],
        "numero": parts[2],
        "hash": parts[3],
    }


# ── QR decoding with OpenCV native detector ──────────────────────────────────

def _cv2_detect(img_bgr: np.ndarray):
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img_bgr)
    if data:
        return data

    # Retry with Otsu-thresholded grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    data, _, _ = detector.detectAndDecode(thresh)
    return data if data else None


def decode_qr_from_image(path: str):
    img = cv2.imread(path)
    if img is None:
        pil = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return _cv2_detect(img)


def decode_qr_from_pdf(pdf_path: str):
    import fitz
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        result = _cv2_detect(img)
        if result:
            doc.close()
            return result
    doc.close()
    return None


def decode_qr(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return decode_qr_from_pdf(file_path)
    if ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}:
        return decode_qr_from_image(file_path)
    return None
