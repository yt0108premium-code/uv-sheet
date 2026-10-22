"""Generate a professional two-page Shri Ji Enterprises letterhead PDF."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "shri-ji-enterprises-kyc-declaration.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
NAVY = HexColor("#17324D")
GOLD = HexColor("#B89045")
CHARCOAL = HexColor("#252B31")
MUTED = HexColor("#5F6872")
PAPER = HexColor("#FFFEFB")
LIGHT_GOLD = HexColor("#EEE4CF")

COMPANY_NAME = "SHRI JI ENTERPRISES"
ADDRESS = "972 Ground Floor, Palam Extension, Street 10, Near Ramphal Chowk, Delhi 110075"

BODY_PARAGRAPHS = (
    "I/We (Full Name) ______________________________ (accountholder/s) do solemnly declare that there is no change in my/our existing KYC details already submitted by me/us to the Bank with respect to my/our above mentioned Customer ID number.",
    "I/We confirm that the information provided by me/us earlier to the Bank is correct and continues to be valid and updated as on date.",
    "I/We authorize the Bank to verify my/our existing KYC details already updated in the records of the Bank is correct and up to date.",
    "I/We undertake that I shall duly inform the Bank immediately for any change in KYC details/information.",
    "We understand that the Bank is relying on this declaration for the purpose of KYC updation of customers in compliance with RBI guidelines on Know Your Customer (KYC).",
)


def draw_letterhead(pdf: canvas.Canvas) -> None:
    """Draw the company identity and restrained decorative frame."""
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    pdf.setFillColor(NAVY)
    pdf.rect(0, PAGE_HEIGHT - 34 * mm, PAGE_WIDTH, 34 * mm, fill=1, stroke=0)
    pdf.setFillColor(GOLD)
    pdf.rect(0, PAGE_HEIGHT - 35.5 * mm, PAGE_WIDTH, 1.5 * mm, fill=1, stroke=0)

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.1)
    pdf.circle(25 * mm, PAGE_HEIGHT - 17 * mm, 8.5 * mm, fill=0, stroke=1)
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(25 * mm, PAGE_HEIGHT - 19.1 * mm, "SJE")

    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(41 * mm, PAGE_HEIGHT - 14.8 * mm, COMPANY_NAME)
    pdf.setFillColor(LIGHT_GOLD)
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(41 * mm, PAGE_HEIGHT - 21.8 * mm, ADDRESS)

    pdf.setStrokeColor(LIGHT_GOLD)
    pdf.setLineWidth(0.7)
    pdf.line(13 * mm, 14 * mm, PAGE_WIDTH - 13 * mm, 14 * mm)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(0.9)
    pdf.line(13 * mm, 13 * mm, 43 * mm, 13 * mm)


def draw_label_and_line(
    pdf: canvas.Canvas,
    label: str,
    x: float,
    y: float,
    line_end: float,
    line_gap: float = 2 * mm,
) -> None:
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, label)
    line_start = x + stringWidth(label, "Helvetica", 10) + line_gap
    pdf.setStrokeColor(MUTED)
    pdf.setLineWidth(0.55)
    pdf.line(line_start, y - 0.7 * mm, line_end, y - 0.7 * mm)


def draw_paragraph(pdf: canvas.Canvas, text: str, y: float, style: ParagraphStyle) -> float:
    width = PAGE_WIDTH - 42 * mm
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, 55 * mm)
    paragraph.drawOn(pdf, 21 * mm, y - height)
    return y - height - 4.2 * mm


def draw_form_page(pdf: canvas.Canvas) -> None:
    """Draw one page while preserving the supplied form wording."""
    draw_letterhead(pdf)

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 12.5)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 48 * mm, "KYC UPDATION - SELF DECLARATION")

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawRightString(PAGE_WIDTH - 21 * mm, PAGE_HEIGHT - 47.5 * mm, "Annexure 5")
    draw_label_and_line(
        pdf,
        "Date:",
        PAGE_WIDTH - 65 * mm,
        PAGE_HEIGHT - 58 * mm,
        PAGE_WIDTH - 21 * mm,
    )

    y = PAGE_HEIGHT - 63 * mm
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(21 * mm, y, "To")
    y -= 5.8 * mm
    pdf.drawString(21 * mm, y, "The Branch Manager,")
    y -= 5.8 * mm
    pdf.drawString(21 * mm, y, "Utkarsh Small Finance Bank Ltd.")
    y -= 6.2 * mm
    pdf.setStrokeColor(MUTED)
    pdf.setLineWidth(0.55)
    pdf.line(21 * mm, y, 67 * mm, y)
    pdf.drawString(70 * mm, y - 1.1 * mm, "Branch")

    y -= 13 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(21 * mm, y, "Dear Sir/Madam,")

    y -= 12 * mm
    draw_label_and_line(
        pdf,
        "My/Our Customer ID Number :",
        21 * mm,
        y,
        PAGE_WIDTH - 21 * mm,
    )

    body_style = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=CHARCOAL,
        alignment=TA_JUSTIFY,
        spaceAfter=0,
        splitLongWords=False,
    )

    y -= 10 * mm
    for text in BODY_PARAGRAPHS:
        y = draw_paragraph(pdf, text, y, body_style)

    signature_y = max(34 * mm, y - 9 * mm)
    pdf.setStrokeColor(MUTED)
    pdf.setLineWidth(0.6)
    pdf.line(21 * mm, signature_y, 78 * mm, signature_y)
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(21 * mm, signature_y - 5 * mm, "Signature of the Customer")


def main() -> None:
    pdf = canvas.Canvas(str(OUTPUT_PATH), pagesize=A4, pageCompression=1)
    pdf.setTitle("KYC UPDATION - SELF DECLARATION")
    pdf.setAuthor(COMPANY_NAME)
    pdf.setSubject("Two-page KYC self-declaration on Shri Ji Enterprises letterhead")

    for _ in range(2):
        draw_form_page(pdf)
        pdf.showPage()

    pdf.save()
    print(f"Created {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
