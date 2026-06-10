#!/usr/bin/env python3
"""Generate NexValue Financial sample policy documents for the demo."""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

DOCUMENTS: list[tuple[str, list]] = []


def _header(styles, title: str, subtitle: str) -> list:
    return [
        Paragraph(f"NexValue Financial — {title}", styles["Title"]),
        Paragraph(f"<i>Internal use only · Effective January 2026</i>", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(subtitle, styles["Normal"]),
        Spacer(1, 14),
    ]


def _table(headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None):
    data = [headers, *rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#001d6c")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def build_aml_kyc(styles) -> list:
    story = _header(
        styles,
        "AML &amp; KYC Procedures",
        "Procedures for anti-money laundering controls and know-your-customer verification across retail and corporate banking.",
    )
    story += [
        Paragraph("1. Purpose", styles["Heading1"]),
        Paragraph(
            "NexValue Financial must verify customer identity, assess money-laundering risk, and maintain "
            "records in line with regulatory obligations. These procedures apply to all onboarding and periodic review activities.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("2. Required KYC Documents", styles["Heading1"]),
        Paragraph("The following documents are required for customer due diligence:", styles["Normal"]),
        Spacer(1, 6),
        _table(
            ["Customer type", "Required documents", "Verification"],
            [
                ["Retail individual", "Government ID, proof of address, tax ID", "In-branch or digital IDV"],
                ["SME business", "Certificate of incorporation, UBO register, director IDs", "Enhanced review if >25% foreign ownership"],
                ["Corporate", "Board resolution, beneficial ownership chart, audited accounts", "Relationship manager sign-off"],
            ],
            [120, 220, 150],
        ),
        Spacer(1, 12),
        Paragraph("3. Enhanced Due Diligence Triggers", styles["Heading1"]),
        Paragraph(
            "Enhanced due diligence (EDD) is required when a customer is classified as high-risk, operates in a "
            "high-risk jurisdiction, is a politically exposed person (PEP), or shows unusual transaction patterns. "
            "EDD includes source-of-funds verification, senior management approval, and quarterly review.",
            styles["Normal"],
        ),
    ]
    return story


def build_cdd_guide(styles) -> list:
    story = _header(
        styles,
        "Customer Due Diligence Guide",
        "Practical guide for relationship managers completing customer due diligence at onboarding and review.",
    )
    story += [
        Paragraph("Overview", styles["Heading1"]),
        Paragraph(
            "Customer due diligence (CDD) ensures NexValue Financial understands who the customer is, the nature "
            "of the business relationship, and the expected activity on the account.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("Document Checklist", styles["Heading1"]),
        _table(
            ["Step", "Action", "Owner"],
            [
                ["1", "Collect identity documents per AML & KYC Procedures", "RM / Onboarding"],
                ["2", "Verify beneficial owners for entities", "KYC Operations"],
                ["3", "Screen against sanctions and PEP lists", "Compliance"],
                ["4", "Record risk rating in core banking system", "RM"],
            ],
            [40, 300, 120],
        ),
        Spacer(1, 12),
        Paragraph("When to Escalate", styles["Heading1"]),
        Paragraph(
            "Escalate to the Financial Crime team when documents are incomplete, ownership structures are opaque, "
            "or the customer requests exceptions to standard verification steps.",
            styles["Normal"],
        ),
    ]
    return story


def build_privacy(styles) -> list:
    story = _header(
        styles,
        "Data Privacy &amp; Retention Policy",
        "Policy governing collection, use, and retention of customer and employee personal data.",
    )
    story += [
        Paragraph("Data Retention Principles", styles["Heading1"]),
        Paragraph(
            "NexValue Financial retains personal data only as long as necessary for the purpose collected, "
            "regulatory compliance, or legitimate business needs.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("Retention Schedule", styles["Heading1"]),
        _table(
            ["Data category", "Retention period", "Basis"],
            [
                ["KYC identity records", "7 years after relationship ends", "AML regulation"],
                ["Transaction records", "7 years", "Tax and AML requirements"],
                ["Customer correspondence", "5 years", "Operational need"],
                ["Employee HR files", "7 years after employment ends", "Employment law"],
            ],
            [140, 160, 180],
        ),
        Spacer(1, 12),
        Paragraph("Customer Data Requests", styles["Heading1"]),
        Paragraph(
            "Customers may request access, correction, or deletion of personal data subject to regulatory "
            "exemptions. KYC and transaction records required for compliance cannot be deleted before the "
            "retention period expires.",
            styles["Normal"],
        ),
    ]
    return story


def build_high_risk(styles) -> list:
    story = _header(
        styles,
        "High-Risk Customer Review Manual",
        "Manual for reviewing and monitoring high-risk customer relationships.",
    )
    story += [
        Paragraph("High-Risk Classification", styles["Heading1"]),
        Paragraph(
            "A customer is classified high-risk based on jurisdiction, industry sector, product usage, "
            "PEP status, or adverse media findings. High-risk customers require enhanced due diligence.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("Review Process", styles["Heading1"]),
        _table(
            ["Stage", "Activity", "Frequency"],
            [
                ["Initial EDD", "Source-of-funds review, senior approval", "At onboarding"],
                ["Ongoing monitoring", "Transaction monitoring alerts, adverse media", "Continuous"],
                ["Periodic review", "Full relationship review and risk re-rating", "Every 12 months"],
                ["Exit", "Document closure rationale and final screening", "At offboarding"],
            ],
            [100, 260, 100],
        ),
        Spacer(1, 12),
        Paragraph("Approval Requirements", styles["Heading1"]),
        Paragraph(
            "All high-risk onboarding and annual reviews require approval from the Head of Financial Crime "
            "and a second-line compliance sign-off before account activity limits are raised.",
            styles["Normal"],
        ),
    ]
    return story


def build_faq(styles) -> list:
    story = _header(
        styles,
        "Employee Compliance FAQ",
        "Frequently asked questions for employees on compliance, KYC, and internal policy search.",
    )
    story += [
        Paragraph("General", styles["Heading1"]),
        Paragraph("<b>Q: What documents are required for customer due diligence?</b>", styles["Normal"]),
        Paragraph(
            "A: Requirements depend on customer type. Retail customers need government ID and proof of address. "
            "Business customers need incorporation documents and beneficial ownership information. "
            "See the Customer Due Diligence Guide and AML & KYC Procedures for the full checklist.",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph("<b>Q: When is enhanced due diligence needed?</b>", styles["Normal"]),
        Paragraph(
            "A: EDD is required for high-risk customers, PEPs, high-risk jurisdictions, and unusual activity patterns. "
            "Refer to the High-Risk Customer Review Manual for the step-by-step process.",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph("<b>Q: How long should customer data be retained?</b>", styles["Normal"]),
        Paragraph(
            "A: KYC and transaction records are retained for 7 years after the customer relationship ends. "
            "See the Data Privacy & Retention Policy for the full schedule.",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph("<b>Q: What is the process for high-risk customers?</b>", styles["Normal"]),
        Paragraph(
            "A: High-risk customers go through enhanced due diligence at onboarding, continuous transaction "
            "monitoring, and annual periodic review with Financial Crime approval.",
            styles["Normal"],
        ),
    ]
    return story


def _load_fonts(size_title: int = 34, size_body: int = 22) -> tuple:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size_title), ImageFont.truetype(path, size_body)
        except OSError:
            continue
    default = ImageFont.load_default()
    return default, default


def _write_scanned_image(path: Path) -> None:
    """Raster-only page (no text layer) — Docling must use OCR."""
    width, height = 1224, 1584
    img = Image.new("RGB", (width, height), (247, 244, 236))
    draw = ImageDraw.Draw(img)
    font_title, font_body = _load_fonts()

    rng = random.Random(42)
    for _ in range(1800):
        x, y = rng.randint(0, width - 1), rng.randint(0, height - 1)
        draw.point((x, y), fill=(rng.randint(230, 245),) * 3)

    y = 72
    draw.text((72, y), "NexValue Financial", fill=(25, 25, 25), font=font_title)
    y += 52
    draw.text((72, y), "KYC Verification Form (Scanned Copy)", fill=(45, 45, 45), font=font_body)
    y += 44
    draw.text((72, y), "Internal use only · Branch onboarding", fill=(90, 90, 90), font=font_body)
    y += 56

    lines = [
        "Customer full name: ________________________________",
        "Date of birth: ____ / ____ / ______",
        "Nationality: ______________________________________",
        "",
        "Identity document presented:",
        "  [ ] Passport    [ ] National ID card    [ ] Residence permit",
        "",
        "Document number: ____________________________________",
        "Issuing country: ____________________________________",
        "Expiry date: ____ / ____ / ______",
        "",
        "Proof of address (utility bill or bank statement, < 3 months):",
        "  [ ] Provided    [ ] Pending",
        "",
        "Relationship manager: _______________________________",
        "Branch / location: __________________________________",
        "",
        "Certification: I confirm the customer appeared in person and",
        "original documents were verified per NexValue AML & KYC Procedures.",
        "",
        "RM signature: _____________________   Date: __________",
    ]
    for line in lines:
        draw.text((72, y), line, fill=(30, 30, 30), font=font_body)
        y += 36 if line else 18

    img.save(path, format="PNG", dpi=(200, 200))


def build_kyc_scanned_pdf() -> None:
    """Image-only PDF — forces Docling OCR path."""
    import tempfile

    pdf_path = DATA_DIR / "KYC Verification Form (Scanned).pdf"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        png_path = Path(tmp.name)
    try:
        _write_scanned_image(png_path)
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawImage(str(png_path), 0, 0, width=letter[0], height=letter[1])
        c.save()
        print(f"Wrote {pdf_path}")
    finally:
        png_path.unlink(missing_ok=True)


def build_retention_matrix(styles) -> list:
    story = _header(
        styles,
        "Regulatory Retention Matrix",
        "Multi-jurisdiction retention requirements for customer and transaction data — complex reference table.",
    )
    story += [
        Paragraph("Matrix Overview", styles["Heading1"]),
        Paragraph(
            "The matrix below consolidates minimum and maximum retention periods across retail, corporate, "
            "and SME banking lines. Cells marked with asterisks require legal hold review before destruction.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("Retention Schedule by Segment", styles["Heading1"]),
    ]

    data = [
        ["Data category", "Retail banking", "", "Corporate banking", "", "SME banking", "", "Regulatory basis"],
        ["", "Min (yrs)", "Max (yrs)", "Min (yrs)", "Max (yrs)", "Min (yrs)", "Max (yrs)", ""],
        ["KYC identity records", "7", "10", "7", "12", "7", "10", "AML / KYC directive"],
        ["Beneficial ownership files", "7", "10*", "7", "15*", "7", "12*", "AML / UBO register"],
        ["Transaction records", "7", "7", "7", "10", "7", "7", "Tax & AML"],
        ["Sanctions screening logs", "5", "7", "5", "7", "5", "7", "Sanctions compliance"],
        ["Customer correspondence", "5", "5", "5", "8", "5", "5", "Operational policy"],
        ["EDD case files", "7", "12*", "7", "15*", "7", "12*", "Financial crime manual"],
    ]
    col_widths = [108, 44, 44, 52, 52, 44, 44, 108]
    table = Table(data, colWidths=col_widths, repeatRows=2)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#001d6c")),
                ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 2), (0, -1), "LEFT"),
                ("ALIGN", (-1, 2), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.whitesmoke, colors.white]),
                ("SPAN", (0, 0), (0, 1)),
                ("SPAN", (1, 0), (2, 0)),
                ("SPAN", (3, 0), (4, 0)),
                ("SPAN", (5, 0), (6, 0)),
                ("SPAN", (7, 0), (7, 1)),
            ]
        )
    )
    story += [table, Spacer(1, 12)]
    story += [
        Paragraph("Footnotes", styles["Heading1"]),
        Paragraph(
            "* Maximum periods require Legal & Compliance approval before record destruction. "
            "Cross-reference the Data Privacy &amp; Retention Policy for customer erasure requests.",
            styles["Normal"],
        ),
    ]
    return story


BUILDERS = {
    "NexValue AML & KYC Procedures.pdf": build_aml_kyc,
    "Regulatory Retention Matrix.pdf": build_retention_matrix,
}

SAMPLE_MANIFEST = {
    "KYC Verification Form (Scanned).pdf": {
        "tags": ["ocr"],
        "label": "OCR showcase",
        "description": "Scanned PDF with an image-only page — Docling OCR + layout",
    },
    "Regulatory Retention Matrix.pdf": {
        "tags": ["complex-table"],
        "label": "Complex table",
        "description": "Merged headers and multi-segment retention grid",
    },
}


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    for filename, builder in BUILDERS.items():
        path = DATA_DIR / filename
        doc = SimpleDocTemplate(str(path), pagesize=letter, topMargin=48, bottomMargin=48)
        doc.build(builder(styles))
        print(f"Wrote {path}")

    build_kyc_scanned_pdf()

    manifest_path = DATA_DIR / ".samples_manifest.json"
    manifest_path.write_text(json.dumps(SAMPLE_MANIFEST, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
