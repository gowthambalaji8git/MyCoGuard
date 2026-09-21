"""Generates a downloadable PDF analysis report for a mushroom scan."""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                 Table, TableStyle)

BASE = os.path.dirname(os.path.abspath(__file__))

CATEGORY_COLORS = {
    "healthy": colors.HexColor("#2f8f4e"),
    "unhealthy": colors.HexColor("#c98a14"),
    "poisonous": colors.HexColor("#c0392b"),
}


def generate_report_pdf(output_path, *, user, result, uploaded_image_path):
    match = result["match"]
    category = result["category"]
    accent = CATEGORY_COLORS.get(category, colors.HexColor("#6b4226"))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("MCGTitle", parent=styles["Title"], textColor=colors.HexColor("#4a2c14"))
    h2 = ParagraphStyle("MCGH2", parent=styles["Heading2"], textColor=accent, spaceBefore=14)
    body = ParagraphStyle("MCGBody", parent=styles["BodyText"], leading=15)
    small = ParagraphStyle("MCGSmall", parent=styles["BodyText"], fontSize=8.5, textColor=colors.grey)

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                             leftMargin=1.8 * cm, rightMargin=1.8 * cm)
    story = []

    logo_path = os.path.join(BASE, "static", "img", "logo.png")
    header_cells = []
    if os.path.exists(logo_path):
        header_cells.append(Image(logo_path, width=2.3 * cm, height=2.3 * cm))
    else:
        header_cells.append(Paragraph("", body))
    header_cells.append(Paragraph(
        "<b>MyCoGuard (MCG)</b><br/><font size=9 color='#6b6b6b'>Mushroom Safety Analysis Report</font>",
        title_style))
    header_table = Table([header_cells], colWidths=[2.6 * cm, None])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # status banner
    status_table = Table(
        [[Paragraph(f"<b>{result['meta']['headline']}</b>", ParagraphStyle(
            "banner", parent=body, textColor=colors.white, fontSize=12))]],
        colWidths=[None])
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 16))

    # image + key facts side-by-side
    img_cell = ""
    if uploaded_image_path and os.path.exists(uploaded_image_path):
        try:
            img_cell = Image(uploaded_image_path, width=6.5 * cm, height=6.5 * cm)
        except Exception:
            img_cell = Paragraph("(image unavailable)", small)

    facts = [
        ["Mushroom name", match["display_name"]],
        ["Scientific name", match["scientific_name"]],
        ["Status / Type", result["meta"]["label"]],
        ["Edibility", match["edibility"]],
        ["Confidence score", f"{result['confidence']}%"],
        ["Report generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Requested by", user],
    ]
    facts_table = Table(facts, colWidths=[4.2 * cm, 7.2 * cm])
    facts_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a2c14")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e0d8c8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    top_row = [[img_cell, facts_table]]
    top_table = Table(top_row, colWidths=[7 * cm, None])
    top_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(top_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Summary", h2))
    story.append(Paragraph(match.get("summary", "-"), body))

    story.append(Paragraph("Details", h2))
    story.append(Paragraph(match.get("details", "-"), body))

    story.append(Paragraph("Other close matches considered", h2))
    cand_rows = [["Species", "Category", "Similarity"]]
    for c in result["candidates"]:
        cand_rows.append([c["name"], c["category_label"], f"{c['score']}%"])
    cand_table = Table(cand_rows, colWidths=[6.5 * cm, 4.5 * cm, 3 * cm])
    cand_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eee3d2")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0d8c8")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cand_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Sources", h2))
    story.append(Paragraph(match.get("sources", "-"), small))

    story.append(Spacer(1, 18))
    disclaimer = (
        "<b>Safety notice:</b> MyCoGuard is a visual reference tool and does NOT replace "
        "identification by a qualified mycologist. Do not eat any wild mushroom based on this "
        "report. If poisoning is suspected, contact emergency medical services or a poison "
        "control center immediately."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle(
        "disclaimer", parent=small, textColor=colors.HexColor("#c0392b"), fontSize=9)))

    doc.build(story)
    return output_path
