from datetime import datetime
from io import BytesIO

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BRAND  = HexColor("#1a3c6e")
GREY   = HexColor("#555555")
LIGHT  = HexColor("#f0f4f8")
GREEN  = HexColor("#2e7d32")
MONO   = "Courier"


def _fmt_price(precio: str) -> str:
    try:
        value = float(precio.replace(",", "."))
        # "150,000.00"  →  swap separators  →  "150.000,00"
        s = f"{value:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${s}"
    except (ValueError, TypeError):
        return f"${precio}"


def _styles():
    return {
        "title": ParagraphStyle(
            "title", fontSize=26, textColor=BRAND,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
            leading=32, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=11, textColor=GREY,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "label", fontSize=10, textColor=GREY,
            fontName="Helvetica-Bold",
        ),
        "value": ParagraphStyle(
            "value", fontSize=15, textColor=colors.black,
        ),
        "price": ParagraphStyle(
            "price", fontSize=18, textColor=BRAND,
            fontName="Helvetica-Bold",
        ),
        "hash_label": ParagraphStyle(
            "hash_label", fontSize=9, textColor=GREY,
            fontName="Helvetica-Bold",
        ),
        "hash_val": ParagraphStyle(
            "hash_val", fontSize=8, fontName=MONO,
            textColor=GREY, leading=12,
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=7, textColor=GREY, alignment=TA_CENTER,
        ),
    }


def build_pdf(
    output_path: str,
    nombre: str,
    precio: str,
    numero: int,
    hmac_hash: str,
    qr_pil: Image.Image,
) -> None:
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    s = _styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
    )

    W = A4[0] - 44 * mm  # usable width

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("COMPROBANTE", s["title"]))
    story.append(Paragraph(f"N° {numero:04d}  ·  {fecha}", s["subtitle"]))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=2.5, color=BRAND, spaceAfter=6 * mm))

    # ── Data rows ─────────────────────────────────────────────────────────────
    rows = [
        [Paragraph("Cliente",        s["label"]), Paragraph(nombre,    s["value"])],
        [Paragraph("Precio",         s["label"]), Paragraph(_fmt_price(precio), s["price"])],
        [Paragraph("N° Comprobante", s["label"]), Paragraph(f"{numero:04d}", s["value"])],
    ]
    col_w = [42 * mm, W - 42 * mm]
    tbl = Table(rows, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, HexColor("#dddddd")),
        ("BACKGROUND",    (0, 0), (0, -1),  LIGHT),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 7 * mm))

    # ── Digital signature ────────────────────────────────────────────────────
    story.append(Paragraph("FIRMA DIGITAL (HMAC-SHA256)", s["hash_label"]))
    story.append(Spacer(1, 1 * mm))
    # Split hash across two lines for readability
    half = len(hmac_hash) // 2
    sig_tbl = Table(
        [[Paragraph(hmac_hash[:half] + "\n" + hmac_hash[half:], s["hash_val"])]],
        colWidths=[W],
    )
    sig_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 8 * mm))

    # ── QR code ───────────────────────────────────────────────────────────────
    qr_buf = BytesIO()
    qr_pil.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_size = 55 * mm
    qr_img = RLImage(qr_buf, width=qr_size, height=qr_size)

    qr_tbl = Table([[qr_img]], colWidths=[W])
    qr_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(qr_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"), spaceBefore=0))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Generado el {fecha}  ·  Documento con firma criptográfica  ·  "
        f"Comprobante N° {numero:04d}",
        s["footer"],
    ))

    doc.build(story)
