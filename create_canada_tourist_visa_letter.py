"""Generate the Canada tourist visa purpose letter as Markdown and PDF.

Replace every bracketed value below with truthful, document-supported details
before using the letter in a visa application.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
MARKDOWN_PATH = ROOT / "canada-tourist-visa-letter-of-purpose.md"
PDF_PATH = ROOT / "canada-tourist-visa-letter-of-purpose.pdf"

NAVY = HexColor("#17324D")
BLUE = HexColor("#285E8E")
CHARCOAL = HexColor("#252B31")
MUTED = HexColor("#606A73")
PALE_BLUE = HexColor("#EDF3F8")
LINE = HexColor("#CCD6DF")
DRAFT_RED = HexColor("#9C2F2F")
DRAFT_BG = HexColor("#FBEDED")

# Use the exact legal spelling shown on each supporting document.
DETAILS = {
    "letter_date": "[DD Month YYYY]",
    "applicant_name": "[FULL NAME]",
    "passport_number": "[PASSPORT NUMBER]",
    "uci_number": "[UCI, IF AVAILABLE]",
    "previous_application_number": "[PREVIOUS APPLICATION NUMBER]",
    "travel_start": "[ARRIVAL DATE]",
    "travel_end": "[DEPARTURE DATE]",
    "trip_length": "[NUMBER OF DAYS]",
    "destinations": "[CANADIAN CITIES AND MAIN ATTRACTIONS]",
    "accommodation": "[HOTEL NAME(S) AND ADDRESS(ES)]",
    "trip_cost_cad": "[AMOUNT]",
    "funding_arrangement": "[FOR EXAMPLE: I WILL PAY FOR THE TRIP FROM MY SALARY AND SAVINGS]",
    "employer": "Dili Private Limited",
    "job_title": "Software Engineer",
    "employment_start": "3 January 2025",
    "work_location": "[CITY, STATE]",
    "monthly_salary_inr": "[AMOUNT]",
    "leave_start": "[APPROVED LEAVE START DATE]",
    "leave_end": "[APPROVED LEAVE END DATE]",
    "return_to_work": "[DATE OF RETURN TO WORK]",
    "previous_business": "Om Sai Ram Enterprises",
    "business_status": "[CURRENT STATUS OF THE BUSINESS, WITH DATE IF APPLICABLE]",
    "bank_statement_period": "[SIX OR TWELVE]",
    "available_funds_inr": "[AMOUNT]",
    "available_funds_cad": "[AMOUNT]",
    "funds_origin": "[SALARY, SAVINGS, INVESTMENTS, OR OTHER DOCUMENTED SOURCES]",
    "deposit_source": "[EXACT SOURCE OF THE LARGE DEPOSITS]",
    "deposit_evidence": "[DOCUMENTS ENCLOSED TO PROVE THE SOURCE]",
    "family_members": "[IMMEDIATE FAMILY MEMBERS WHO LIVE IN INDIA]",
    "family_responsibilities": "[ACTUAL FAMILY OR HOUSEHOLD RESPONSIBILITIES]",
    "other_india_ties": "[PROPERTY, TENANCY, INVESTMENTS, LOANS, OR OTHER DOCUMENTED TIES]",
    "residential_address": "[COMPLETE RESIDENTIAL ADDRESS]",
    "mobile_number": "[MOBILE NUMBER]",
    "email_address": "[EMAIL ADDRESS]",
}

# Add one row for each unusual or large credit in the statements being submitted.
LARGE_DEPOSITS = [
    {
        "date": "[DATE]",
        "amount": "INR [AMOUNT]",
        "source": "[ACTUAL SOURCE]",
        "evidence": "[SUPPORTING DOCUMENT]",
    }
]

INTRODUCTION = (
    "I am reapplying for a Temporary Resident Visa to visit Canada for tourism "
    "from {travel_start} to {travel_end}.",
    "I understand that my previous application was refused because the evidence "
    "did not sufficiently establish my family ties outside Canada or my financial "
    "position. The officer also noted the low ongoing balance in my bank account, "
    "recent large deposits without clear source documents, and concern that I "
    "might not leave Canada at the end of my authorized stay. I have addressed "
    "those points below with updated information and supporting records.",
)

SECTIONS = (
    (
        "Purpose of visit",
        (
            "I plan to spend {trip_length} days in Canada and visit {destinations}. "
            "I will stay at {accommodation}. The estimated cost of the trip is CAD "
            "{trip_cost_cad}. {funding_arrangement}. My itinerary, accommodation "
            "information, and trip-cost estimate are included with my application. "
            "I will not work or study during this visit.",
        ),
    ),
    (
        "Employment and change in circumstances",
        (
            "When I submitted my previous application, I was self-employed and "
            "operated {previous_business}. Since {employment_start}, I have been "
            "working full-time as a {job_title} with {employer} in {work_location}. "
            "My monthly salary is INR {monthly_salary_inr}, which is credited to my "
            "bank account. I have included my employment letter, recent salary "
            "slips, and bank statements showing these credits.",
            "My employer has approved leave from {leave_start} to {leave_end}, and "
            "I must resume work on {return_to_work}. The current status of "
            "{previous_business} is {business_status}. Relevant records supporting "
            "this transition are included with my application.",
        ),
    ),
    (
        "Financial position and bank deposits",
        (
            "My application includes bank statements for the last "
            "{bank_statement_period} months. They show my regular salary and normal "
            "account activity. I currently have documented funds of INR "
            "{available_funds_inr}, approximately CAD {available_funds_cad}, against "
            "an estimated trip cost of CAD {trip_cost_cad}. These funds come from "
            "{funds_origin}.",
            "The large deposits referred to in my previous refusal came from "
            "{deposit_source}. I have enclosed {deposit_evidence} to verify their "
            "source. For clarity, the relevant transactions appearing in the bank "
            "statements submitted with this application are listed below.",
        ),
    ),
    (
        "Reasons for my return to India",
        (
            "My home, employment, and personal responsibilities are in India. My "
            "immediate family here includes {family_members}, and I am responsible "
            "for {family_responsibilities}. My other documented ties to India are "
            "{other_india_ties}.",
            "I have a continuing full-time position with {employer} and must return "
            "to work on {return_to_work}. I will leave Canada by {travel_end} and "
            "return to India to continue my employment and meet my family and "
            "personal responsibilities.",
        ),
    ),
)

CLOSING = (
    "I respectfully request that my application be considered in light of my "
    "current circumstances and the supporting evidence provided. Thank you for "
    "your time and consideration."
)


def has_placeholders() -> bool:
    values = list(DETAILS.values())
    for deposit in LARGE_DEPOSITS:
        values.extend(deposit.values())
    return any("[" in value or "]" in value for value in values)


def format_text(template: str, *, for_pdf: bool) -> str:
    """Insert details into a paragraph, highlighting unfinished PDF fields."""
    if not for_pdf:
        return template.format(**DETAILS)

    formatted_values = {}
    for key, raw_value in DETAILS.items():
        colour = "#9C2F2F" if "[" in raw_value else "#17324D"
        formatted_values[key] = (
            f'<font color="{colour}"><b>{escape(raw_value)}</b></font>'
        )
    return template.format(**formatted_values)


def markdown_table_value(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def build_markdown() -> str:
    lines = [
        "# Purpose of Travel and Letter of Explanation",
        "",
        "**Temporary Resident Visa Reapplication — Canada**",
        "",
    ]
    if has_placeholders():
        lines.extend(
            [
                "> **Draft:** Replace every bracketed field with truthful, "
                "document-supported information before submission.",
                "",
            ]
        )

    applicant_rows = (
        ("Date", DETAILS["letter_date"]),
        ("Applicant", DETAILS["applicant_name"]),
        ("Passport number", DETAILS["passport_number"]),
        ("UCI", DETAILS["uci_number"]),
        ("Previous application", DETAILS["previous_application_number"]),
    )
    lines.extend(["| Applicant detail | Information |", "|---|---|"])
    lines.extend(
        f"| {label} | {markdown_table_value(value)} |"
        for label, value in applicant_rows
    )
    lines.extend(
        [
            "",
            "**To:** The Visa Officer<br>",
            "Immigration, Refugees and Citizenship Canada",
            "",
            "**Subject: Temporary Resident Visa Reapplication — Purpose of Travel "
            "and Explanation of Changed Circumstances**",
            "",
            "Dear Visa Officer,",
            "",
        ]
    )

    for paragraph in INTRODUCTION:
        lines.extend([format_text(paragraph, for_pdf=False), ""])

    for heading, paragraphs in SECTIONS:
        lines.extend([f"## {heading}", ""])
        for paragraph in paragraphs:
            lines.extend([format_text(paragraph, for_pdf=False), ""])
        if heading == "Financial position and bank deposits":
            lines.extend(
                [
                    "| Financial detail | Amount / period |",
                    "|---|---:|",
                    f"| Monthly salary | INR {DETAILS['monthly_salary_inr']} |",
                    f"| Bank statements | Last {DETAILS['bank_statement_period']} months |",
                    f"| Documented available funds | INR {DETAILS['available_funds_inr']} "
                    f"(approximately CAD {DETAILS['available_funds_cad']}) |",
                    f"| Estimated trip cost | CAD {DETAILS['trip_cost_cad']} |",
                    "",
                    "| Date | Amount | Source | Supporting document |",
                    "|---|---:|---|---|",
                ]
            )
            for deposit in LARGE_DEPOSITS:
                safe_values = {
                    key: markdown_table_value(value)
                    for key, value in deposit.items()
                }
                lines.append(
                    "| {date} | {amount} | {source} | {evidence} |".format(
                        **safe_values
                    )
                )
            lines.append("")

    lines.extend(
        [
            CLOSING,
            "",
            "Yours sincerely,",
            "",
            f"**{DETAILS['applicant_name']}**<br>",
            f"{DETAILS['residential_address']}<br>",
            f"Mobile: {DETAILS['mobile_number']}<br>",
            f"Email: {DETAILS['email_address']}",
            "",
        ]
    )
    return "\n".join(lines)


def make_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "VisaTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=1.5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "VisaSubtitle",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        "draft": ParagraphStyle(
            "DraftNotice",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=DRAFT_RED,
            alignment=TA_CENTER,
        ),
        "body": ParagraphStyle(
            "VisaBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=CHARCOAL,
            alignment=TA_LEFT,
            spaceAfter=3.2 * mm,
            splitLongWords=False,
        ),
        "heading": ParagraphStyle(
            "VisaHeading",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=NAVY,
            spaceBefore=2.5 * mm,
            spaceAfter=1.8 * mm,
            keepWithNext=True,
        ),
        "small": ParagraphStyle(
            "VisaSmall",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=CHARCOAL,
        ),
        "small_bold": ParagraphStyle(
            "VisaSmallBold",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=NAVY,
        ),
        "recipient": ParagraphStyle(
            "VisaRecipient",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=CHARCOAL,
            spaceAfter=3.5 * mm,
        ),
        "subject": ParagraphStyle(
            "VisaSubject",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=NAVY,
            spaceAfter=3.5 * mm,
        ),
        "signature": ParagraphStyle(
            "VisaSignature",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=CHARCOAL,
        ),
    }


def pdf_cell(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def applicant_details_table(styles: dict[str, ParagraphStyle]) -> Table:
    rows = (
        ("Applicant", "{applicant_name}", "Passport no.", "{passport_number}"),
        ("UCI", "{uci_number}", "Previous application", "{previous_application_number}"),
    )
    data = []
    for left_label, left_value, right_label, right_value in rows:
        data.append(
            [
                pdf_cell(left_label, styles["small_bold"]),
                pdf_cell(format_text(left_value, for_pdf=True), styles["small"]),
                pdf_cell(right_label, styles["small_bold"]),
                pdf_cell(format_text(right_value, for_pdf=True), styles["small"]),
            ]
        )

    table = Table(data, colWidths=[27 * mm, 55 * mm, 34 * mm, 54 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def financial_summary_table(styles: dict[str, ParagraphStyle]) -> Table:
    rows = (
        ("Monthly salary", "INR {monthly_salary_inr}"),
        ("Bank statements", "Last {bank_statement_period} months"),
        (
            "Documented available funds",
            "INR {available_funds_inr} (approximately CAD {available_funds_cad})",
        ),
        ("Estimated trip cost", "CAD {trip_cost_cad}"),
    )
    data = [
        [
            pdf_cell("Financial detail", styles["small_bold"]),
            pdf_cell("Amount / period", styles["small_bold"]),
        ]
    ]
    for label, value in rows:
        data.append(
            [
                pdf_cell(label, styles["small"]),
                pdf_cell(format_text(value, for_pdf=True), styles["small"]),
            ]
        )

    table = Table(data, colWidths=[78 * mm, 92 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FAFCFD")),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def deposit_table(styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [
            pdf_cell("Date", styles["small_bold"]),
            pdf_cell("Amount", styles["small_bold"]),
            pdf_cell("Source", styles["small_bold"]),
            pdf_cell("Supporting document", styles["small_bold"]),
        ]
    ]
    for deposit in LARGE_DEPOSITS:
        row = []
        for key in ("date", "amount", "source", "evidence"):
            raw_value = deposit[key]
            colour = "#9C2F2F" if "[" in raw_value else "#17324D"
            row.append(
                pdf_cell(
                    f'<font color="{colour}"><b>{escape(raw_value)}</b></font>',
                    styles["small"],
                )
            )
        data.append(row)

    table = Table(data, colWidths=[24 * mm, 32 * mm, 52 * mm, 62 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FAFCFD")),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def draw_page(pdf, doc) -> None:
    pdf.saveState()
    pdf.setTitle("Canada Tourist Visa - Purpose of Travel and Letter of Explanation")
    pdf.setAuthor(DETAILS["applicant_name"])
    pdf.setSubject("Temporary Resident Visa reapplication letter")

    width, height = A4
    pdf.setFillColor(NAVY)
    pdf.rect(0, height - 8 * mm, width, 8 * mm, fill=1, stroke=0)
    pdf.setFillColor(BLUE)
    pdf.rect(0, height - 9.3 * mm, width, 1.3 * mm, fill=1, stroke=0)

    pdf.setStrokeColor(LINE)
    pdf.setLineWidth(0.45)
    pdf.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(20 * mm, 9.5 * mm, "Canada Temporary Resident Visa Reapplication")
    pdf.drawRightString(width - 20 * mm, 9.5 * mm, f"Page {doc.page}")
    pdf.restoreState()


def build_pdf() -> None:
    styles = make_styles()
    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        pageCompression=1,
    )

    story = [
        Paragraph("Purpose of Travel and Letter of Explanation", styles["title"]),
        Paragraph(
            "TEMPORARY RESIDENT VISA REAPPLICATION — CANADA",
            styles["subtitle"],
        ),
    ]
    if has_placeholders():
        draft_notice = Table(
            [
                [
                    Paragraph(
                        "DRAFT — Complete every bracketed field with verified "
                        "information before submission.",
                        styles["draft"],
                    )
                ]
            ],
            colWidths=[170 * mm],
        )
        draft_notice.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), DRAFT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.6, DRAFT_RED),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.extend([draft_notice, Spacer(1, 4 * mm)])

    story.extend(
        [
            applicant_details_table(styles),
            Spacer(1, 5 * mm),
            Paragraph(
                f"<b>Date:</b> {format_text('{letter_date}', for_pdf=True)}",
                styles["recipient"],
            ),
            Paragraph(
                "To<br/>The Visa Officer<br/>Immigration, Refugees and Citizenship Canada",
                styles["recipient"],
            ),
            Paragraph(
                "Subject: Temporary Resident Visa Reapplication — Purpose of Travel "
                "and Explanation of Changed Circumstances",
                styles["subject"],
            ),
            Paragraph("Dear Visa Officer,", styles["body"]),
        ]
    )

    for paragraph in INTRODUCTION:
        story.append(Paragraph(format_text(paragraph, for_pdf=True), styles["body"]))

    for heading, paragraphs in SECTIONS:
        if heading == "Financial position and bank deposits":
            story.append(PageBreak())

        story.append(Paragraph(heading, styles["heading"]))
        for paragraph in paragraphs:
            story.append(Paragraph(format_text(paragraph, for_pdf=True), styles["body"]))

        if heading == "Financial position and bank deposits":
            story.extend(
                [
                    financial_summary_table(styles),
                    Spacer(1, 3 * mm),
                    deposit_table(styles),
                    Spacer(1, 2 * mm),
                ]
            )

    applicant = format_text("{applicant_name}", for_pdf=True)
    address = format_text("{residential_address}", for_pdf=True)
    mobile = format_text("{mobile_number}", for_pdf=True)
    email_address = format_text("{email_address}", for_pdf=True)
    story.extend(
        [
            Paragraph(CLOSING, styles["body"]),
            Spacer(1, 2 * mm),
            KeepTogether(
                [
                    Paragraph("Yours sincerely,", styles["signature"]),
                    Spacer(1, 7 * mm),
                    Paragraph(applicant, styles["signature"]),
                    Paragraph(address, styles["signature"]),
                    Paragraph(f"Mobile: {mobile}", styles["signature"]),
                    Paragraph(f"Email: {email_address}", styles["signature"]),
                ]
            ),
        ]
    )

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)


def main() -> None:
    MARKDOWN_PATH.write_text(build_markdown(), encoding="utf-8")
    build_pdf()
    print(f"Created {MARKDOWN_PATH.name}")
    print(f"Created {PDF_PATH.name}")
    if has_placeholders():
        print("Draft placeholders remain; complete them before submission.")


if __name__ == "__main__":
    main()
