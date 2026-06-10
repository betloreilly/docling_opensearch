#!/usr/bin/env python3
"""Generate a small demo PDF with headings, paragraphs, and a table."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "data" / "docling_demo_sample.pdf"


def main() -> None:
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Docling + OpenSearch Developer Demo", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This sample document demonstrates how Docling extracts structured elements "
            "including titles, headings, paragraphs, and tables before indexing into OpenSearch.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Document Ingestion", styles["Heading1"]))
    story.append(
        Paragraph(
            "Docling parses PDFs with layout awareness, preserving reading order and "
            "detecting section headers, tables, and captions.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Hybrid Search", styles["Heading1"]))
    story.append(
        Paragraph(
            "OpenSearch combines keyword (BM25) and semantic (vector) retrieval so users "
            "can find content by exact terms or by meaning.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 16))
    story.append(Paragraph("Feature Comparison", styles["Heading2"]))
    table_data = [
        ["Capability", "Keyword", "Semantic", "Hybrid"],
        ["Exact policy terms", "Strong", "Weak", "Strong"],
        ["Conceptual questions", "Weak", "Strong", "Strong"],
        ["Table content", "Moderate", "Moderate", "Strong"],
    ]
    table = Table(table_data, colWidths=[140, 90, 90, 90])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f62fe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "<i>Figure 1: Retrieval modes compared for enterprise document search.</i>",
            styles["Normal"],
        )
    )

    doc.build(story)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
