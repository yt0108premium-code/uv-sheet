"""Generate an editable Markdown draft and a professional PDF visa letter.

Replace every bracketed value in DETAILS and LARGE_DEPOSITS with truthful,
document-supported information before using the letter in an application.
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
    Paragraph,
    PageBreak,
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

# Keep the company name exactly as it appears on the employment documents.
DETAILS = {
    "letter_date": "[DD Month YYYY]",
    "applicant_name": "[FULL NAME]",
    "passport_number": "[PASSPORT NUMBER]",
    "uci_number": "[UCI, IF AVAILABLE]",
    "previous_application_number": "[PREVIOUS APPLICATION NUMBER]",
    "travel_start": "[ARRIVAL DATE]",
    "travel_end": "[DEPARTURE DATE]",
    "trip_length": "[NUMBER OF DAYS] days",
    "destinations": "[CANADIAN CITIES AND ATTRACTIONS]",
    "accommodation": "[HOTEL NAME(S) AND ADDRESS(ES)]",
    "trip_cost_cad": "[AMOUNT]",
    "funding_arrangement": "[EXPLAIN WHETHER THE TRIP IS SELF-FUNDED OR IDENTIFY THE SPONSOR]",
    "employer": "Dili Private Limited",
    "job_title": "Software Engineer",
    "employment_start": "3 January 2025",
    "work_location": "[CITY, STATE]",
    "monthly_salary_inr": "[AMOUNT]",
    "leave_start": "[APPROVED LEAVE START DATE]",
    "leave_end": "[APPROVED LEAVE END DATE]",
    "return_to_work": "[DATE OF RETURN TO WORK]",
    "previous_business": "Om Sai Ram Enterprises",
    "business_status": "[EXPLAIN WHETHER THE BUSINESS IS CLOSED, TRANSFERRED, OR INACTIVE, WITH DATE]",
    "bank_statement_period": "[SIX OR TWELVE] months",
    "previous_deposit_source": "[EXACT, TRUTHFUL SOURCE OF THE DEPOSITS]",
    "previous_deposit_evidence": "[DOCUMENTS THAT PROVE THE SOURCE]",
    "salary_account_balance_inr": "[AMOUNT]",
    "savings_fixed_deposits_inr": "[AMOUNT]",
    "investments_inr": "[AMOUNT]",
    "other_documented_funds_inr": "[AMOUNT OR NIL]",
    "total_available_funds_inr": "[AMOUNT]",
    "total_available_funds_cad": "[AMOUNT]",
    "funds_origin": "[SALARY, DOCUMENTED SAVINGS, INVESTMENTS, OR OTHER PROVABLE SOURCES]",
    "funds_ownership": "[CONFIRM WHETHER THE FUNDS ARE YOUR OWN; IF SPONSORED, EXPLAIN THE ARRANGEMENT]",
    "family_members": "[PARENTS, SPOUSE, CHILDREN, OR OTHER IMMEDIATE FAMILY IN INDIA]",
    "family_responsibilities": "[YOUR ACTUAL CARE, FINANCIAL, OR HOUSEHOLD RESPONSIBILITIES]",
    "other_india_ties": "[PROPERTY, TENANCY, INVESTMENTS, LOANS, OR OTHER DOCUMENTED COMMITMENTS]",
    "residential_address": "[COMPLETE RESIDENTIAL ADDRESS]",
    "mobile_number": "[MOBILE NUMBER]",
    "email_address": "[EMAIL ADDRESS]",
}

# Add one row for every unusual or large credit visible in the submitted statements.
LARGE_DEPOSITS = [
    {
        "date": "[DATE]",
        "amount": "INR [AMOUNT]",
        "source": "[ACTUAL SOURCE]",
        "evidence": "[SUPPORTING DOCUMENT]",
    }
]

INTRODUCTION = (
    "I am reapplying for a Canadian Temporary Resident Visa to visit Canada for "
    "tourism from {travel_start} to {travel_end}. I have written this letter to "
    "explain my travel plans, my present employment and finances, my ties to "
    "India, and the changes since my previous application.",
    "I respect the decision on my previous application. I understand that the "
    "visa officer was concerned about my family ties outside Canada, my financial "
    "position, the low ongoing balance in my bank account, and recent large "
    "deposits whose source was not sufficiently documented. I also understand "
    "that these points caused concern about whether I would leave Canada at the "
    "end of my authorized stay. I address each point below and have included "
    "supporting records with this application.",
)

SECTIONS = (
    (
        "Purpose of my visit",
        (
            "My visit is solely for tourism and will last {trip_length}. I plan "
            "to visit {destinations} and will stay at {accommodation}. I have "
            "included a day-by-day itinerary and accommodation information with "
            "my application.",
            "The estimated total cost of the trip is CAD {trip_cost_cad}, "
            "including airfare, accommodation, food, local transportation, travel "
            "insurance, and sightseeing. {funding_arrangement}. I do not intend "
            "to work, study, or remain in Canada beyond the period authorized for "
            "my visit.",
        ),
    ),
    (
        "Change in my professional circumstances",
        (
            "At the time of my previous application, I was self-employed and "
            "operated {previous_business}. My professional circumstances have "
            "since changed. I have been employed full-time as a {job_title} with "
            "{employer} in {work_location} since {employment_start}. I currently "
            "earn INR {monthly_salary_inr} per month, and my salary is regularly "
            "credited to my bank account.",
            "My employer has approved leave from {leave_start} to {leave_end}, and "
            "I am required to resume my duties on {return_to_work}. My continuing "
            "employment, current projects, and long-term career in India require "
            "my return after this short visit. I have included my appointment and "
            "employment letters, approved leave letter, recent salary slips, and "
            "bank statements showing salary credits.",
            "The current status of {previous_business} is: {business_status}. I "
            "have included the available business, tax, closure, or transfer "
            "records that support this explanation.",
        ),
    ),
    (
        "Financial position and source of funds",
        (
            "I recognize that my previous statements showed a low regular balance "
            "followed by large deposits, and that my earlier application did not "
            "adequately establish where those deposits came from. The deposits "
            "were from {previous_deposit_source}. I am now providing "
            "{previous_deposit_evidence} to establish their source.",
            "My current application includes {bank_statement_period} of bank "
            "statements showing my normal account activity and regular salary "
            "credits. I have also listed each relevant large transaction and its "
            "supporting record in the schedule below. My available funds were "
            "accumulated from {funds_origin}. {funds_ownership}.",
            "My proposed trip cost of CAD {trip_cost_cad} is within the means "
            "shown by my documented income and savings. I have not relied on an "
            "unexplained account balance to demonstrate that I can pay for the "
            "visit.",
        ),
    ),
    (
        "Family, employment, and personal ties to India",
        (
            "My permanent home, employment, and personal responsibilities are in "
            "India. My immediate family in India includes {family_members}. I "
            "have continuing responsibilities for {family_responsibilities}, and "
            "I have included the relevant family and address documents that are "
            "available to support these facts.",
            "My other documented commitments in India are {other_india_ties}. In "
            "addition, my full-time position with {employer} and my obligation to "
            "return to work on {return_to_work} are important professional reasons "
            "for me to return as planned.",
        ),
    ),
    (
        "Commitment to leave Canada",
        (
            "My trip has a defined purpose and end date. I understand that a "
            "Temporary Resident Visa permits only a temporary stay and that I must "
            "comply with all conditions of entry. I will leave Canada by "
            "{travel_end} and return to India to resume my employment and personal "
            "responsibilities.",
            "I respectfully ask that my application be considered on the basis of "
            "my current circumstances and the additional evidence provided. Thank "
            "you for taking the time to review my application.",
        ),
    ),
)

SUPPORTING_DOCUMENTS = (
    "Previous refusal letter and available officer notes",
    "Employment confirmation and appointment or joining letter",
    "Employer-approved leave letter or No Objection Certificate",
    "Recent salary slips and bank statements showing salary credits",
    "Form 16 and income-tax returns, where applicable",
    "Evidence for every large or unusual bank deposit",
    "Savings, fixed-deposit, investment, and property records relied upon",
    "Family relationship, dependency, and address evidence relied upon",
    "Day-by-day itinerary, accommodation information, and trip budget",
    "Relevant records showing the current status of Om Sai Ram Enterprises",
)


def has_placeholders() -> bool:
    values = list(DETAILS.values())
    for deposit in LARGE_DEPOSITS:
        values.extend(deposit.values())
    return any("[" in value or "]" in value for value in values)


def format_text(template: str, *, for_pdf: bool) -> str:
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
                "> **Draft:** Replace every bracketed field with truthful information "
                "and remove any claim that is not supported by an enclosed document.",
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
        if heading == "Financial position and source of funds":
            lines.extend(
                [
                    "### Current financial position",
                    "",
                    "| Type of funds | Amount |",
                    "|---|---:|",
                    f"| Salary account | INR {DETAILS['salary_account_balance_inr']} |",
                    f"| Savings and fixed deposits | INR {DETAILS['savings_fixed_deposits_inr']} |",
                    f"| Investments | INR {DETAILS['investments_inr']} |",
                    f"| Other documented funds | INR {DETAILS['other_documented_funds_inr']} |",
                    f"| **Total available funds** | **INR {DETAILS['total_available_funds_inr']} "
                    f"(approximately CAD {DETAILS['total_available_funds_cad']})** |",
                    "",
                    "### Large-deposit explanation schedule",
                    "",
                    "| Date | Amount | Source | Supporting document |",
                    "|---|---:|---|---|",
                ]
            )
            for deposit in LARGE_DEPOSITS:
                lines.append(
                    "| {date} | {amount} | {source} | {evidence} |".format(
                        **{
                            key: markdown_table_value(value)
                            for key, value in deposit.items()
                        }
                    )
                )
            lines.append("")

    lines.extend(
        [
            "Yours sincerely,",
            "",
            f"**{DETAILS['applicant_name']}**<br>",
            f"{DETAILS['residential_address']}<br>",
            f"Mobile: {DETAILS['mobile_number']}<br>",
            f"Email: {DETAILS['email_address']}",
            "",
            "---",
            "",
            "## Supporting-document checklist",
            "",
            "Keep only the items that are genuinely enclosed with the application:",
            "",
        ]
    )
    lines.extend(f"- [ ] {item}" for item in SUPPORTING_DOCUMENTS)
    lines.extend(
        [
            "",
            "## Before submission",
            "",
            "- Replace every bracketed field; do not submit the draft with placeholders.",
            "- Use the employer's exact legal name as shown on official records.",
            "- Make the travel dates consistent across the letter, itinerary, leave "
            "approval, reservations, and application form.",
            "- Reconcile all INR and CAD figures using the exchange rate stated in "
            "the application package.",
            "- Explain every unusual credit in the submitted bank-statement period "
            "and attach evidence of its source.",
            "- Remove any sentence or checklist item that cannot be supported with "
            "truthful documentation.",
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
            spaceAfter=3.5 * mm,
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
            fontSize=9,
            leading=12.3,
            textColor=CHARCOAL,
            alignment=TA_LEFT,
            spaceAfter=2.4 * mm,
            splitLongWords=False,
        ),
        "heading": ParagraphStyle(
            "VisaHeading",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12.5,
            textColor=NAVY,
            spaceBefore=2 * mm,
            spaceAfter=1.3 * mm,
            keepWithNext=True,
        ),
        "small": ParagraphStyle(
            "VisaSmall",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=CHARCOAL,
        ),
        "small_bold": ParagraphStyle(
            "VisaSmallBold",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=10,
            textColor=NAVY,
        ),
        "recipient": ParagraphStyle(
            "VisaRecipient",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=CHARCOAL,
            spaceAfter=3 * mm,
        ),
        "subject": ParagraphStyle(
            "VisaSubject",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=NAVY,
            spaceAfter=3 * mm,
        ),
        "signature": ParagraphStyle(
            "VisaSignature",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=CHARCOAL,
        ),
    }


def pdf_cell(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def applicant_details_table(styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        (
            "Applicant",
            DETAILS["applicant_name"],
            "Passport no.",
            DETAILS["passport_number"],
        ),
        (
            "UCI",
            DETAILS["uci_number"],
            "Previous application",
            DETAILS["previous_application_number"],
        ),
    ]
    data = []
    for row in rows:
        data.append(
            [
                pdf_cell(escape(row[0]), styles["small_bold"]),
                pdf_cell(format_text("{" + ("applicant_name" if row[0] == "Applicant" else "uci_number") + "}", for_pdf=True), styles["small"]),
                pdf_cell(escape(row[2]), styles["small_bold"]),
                pdf_cell(format_text("{" + ("passport_number" if row[2] == "Passport no." else "previous_application_number") + "}", for_pdf=True), styles["small"]),
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


def financial_table(styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        ("Salary account", "INR {salary_account_balance_inr}"),
        ("Savings and fixed deposits", "INR {savings_fixed_deposits_inr}"),
        ("Investments", "INR {investments_inr}"),
        ("Other documented funds", "INR {other_documented_funds_inr}"),
        (
            "Total available funds",
            "INR {total_available_funds_inr} (approximately CAD "
            "{total_available_funds_cad})",
        ),
    ]
    data = [
        [
            pdf_cell("Type of funds", styles["small_bold"]),
            pdf_cell("Amount", styles["small_bold"]),
        ]
    ]
    for label, amount in rows:
        data.append(
            [
                pdf_cell(escape(label), styles["small"]),
                pdf_cell(format_text(amount, for_pdf=True), styles["small"]),
            ]
        )
    table = Table(data, colWidths=[85 * mm, 85 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -2), HexColor("#FAFCFD")),
                ("BACKGROUND", (0, -1), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
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
    table = Table(
        data,
        colWidths=[24 * mm, 32 * mm, 52 * mm, 62 * mm],
        repeatRows=1,
    )
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
        topMargin=14 * mm,
        bottomMargin=18 * mm,
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
                        "DRAFT — Replace every bracketed field and remove any "
                        "unsupported statement before submission.",
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
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.extend([draft_notice, Spacer(1, 3 * mm)])

    story.extend(
        [
            applicant_details_table(styles),
            Spacer(1, 4 * mm),
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
        if heading == "Financial position and source of funds":
            story.append(PageBreak())
        section_flowables = [Paragraph(escape(heading), styles["heading"])]
        section_flowables.extend(
            Paragraph(format_text(paragraph, for_pdf=True), styles["body"])
            for paragraph in paragraphs
        )
        story.extend(section_flowables)

        if heading == "Financial position and source of funds":
            story.extend(
                [
                    Paragraph("Current financial position", styles["heading"]),
                    financial_table(styles),
                    Spacer(1, 2.5 * mm),
                    Paragraph("Large-deposit explanation schedule", styles["heading"]),
                    deposit_table(styles),
                    Spacer(1, 2 * mm),
                ]
            )

    applicant = format_text("{applicant_name}", for_pdf=True)
    address = format_text("{residential_address}", for_pdf=True)
    mobile = format_text("{mobile_number}", for_pdf=True)
    email = format_text("{email_address}", for_pdf=True)
    story.extend(
        [
            Spacer(1, 2 * mm),
            KeepTogether(
                [
                    Paragraph("Yours sincerely,", styles["signature"]),
                    Spacer(1, 6 * mm),
                    Paragraph(f"<b>{applicant}</b>", styles["signature"]),
                    Paragraph(address, styles["signature"]),
                    Paragraph(f"Mobile: {mobile}", styles["signature"]),
                    Paragraph(f"Email: {email}", styles["signature"]),
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
