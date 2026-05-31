"""
Report Generation Agent — assembles multi-section PDF using ReportLab Platypus
"""
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

logger = logging.getLogger(__name__)

REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")


class ReportAgent:

    def __init__(self) -> None:
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate(
        self,
        dataset_name: str,
        df: pd.DataFrame,
        profiling:    Optional[Dict[str, Any]] = None,
        cleaning:     Optional[Dict[str, Any]] = None,
        insights:     Optional[List[str]] = None,
        chart_images: Optional[List[bytes]] = None,
    ) -> str:
        """
        Build a PDF report and return its file path.
        """
        timestamp   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_name = f"report_{dataset_name}_{timestamp}.pdf"
        report_path = os.path.join(REPORTS_DIR, report_name)

        doc    = SimpleDocTemplate(report_path, pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story: List = []

        # ── Style definitions ─────────────────────────────────────────────
        h1 = ParagraphStyle("H1", parent=styles["Heading1"],
                             fontSize=20, spaceAfter=6, textColor=colors.HexColor("#1D9E75"))
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             fontSize=14, spaceAfter=4, textColor=colors.HexColor("#0F6E56"))
        body = styles["BodyText"]
        mono = ParagraphStyle("Mono", parent=body, fontName="Courier", fontSize=9)

        # ── Cover ─────────────────────────────────────────────────────────
        story.append(Paragraph("AI Data Analyst Report", h1))
        story.append(Paragraph(f"Dataset: <b>{dataset_name}</b>", body))
        story.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#9FE1CB"), spaceAfter=12))

        # ── Dataset Overview ──────────────────────────────────────────────
        story.append(Paragraph("1. Dataset Overview", h2))
        story.append(Paragraph(f"Rows: {len(df):,} | Columns: {len(df.columns)}", body))
        story.append(Spacer(1, 0.3*cm))

        # Column table (first 15 cols)
        col_data = [["Column", "Type", "Null %"]]
        for col in df.columns[:15]:
            null_pct = f"{df[col].isna().mean()*100:.1f}%"
            col_data.append([col, str(df[col].dtype), null_pct])
        col_tbl = Table(col_data, colWidths=[7*cm, 4*cm, 3*cm])
        col_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D9E75")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#F0FBF6"), colors.white]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#9FE1CB")),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(col_tbl)
        story.append(Spacer(1, 0.5*cm))

        # ── Data Quality Summary ──────────────────────────────────────────
        if cleaning:
            story.append(Paragraph("2. Data Quality Summary", h2))
            for item in cleaning.get("summary", []):
                story.append(Paragraph(f"• {item}", body))
            story.append(Spacer(1, 0.3*cm))

        # ── Insights ──────────────────────────────────────────────────────
        if insights:
            story.append(Paragraph("3. AI-Generated Insights", h2))
            for ins in insights:
                story.append(Paragraph(f"• {ins}", body))
            story.append(Spacer(1, 0.3*cm))

        # ── Charts ────────────────────────────────────────────────────────
        if chart_images:
            story.append(Paragraph("4. Visualizations", h2))
            for img_bytes in chart_images[:4]:
                img_buf = io.BytesIO(img_bytes)
                rl_img  = RLImage(img_buf, width=14*cm, height=8*cm)
                story.append(rl_img)
                story.append(Spacer(1, 0.3*cm))

        # ── Statistical Summary ───────────────────────────────────────────
        story.append(Paragraph("5. Statistical Summary", h2))
        desc = df.describe(include="all").round(3)
        tbl_data = [["Stat"] + list(desc.columns[:8])]
        for idx_label in desc.index:
            row = [str(idx_label)]
            for col in list(desc.columns[:8]):
                val = desc.loc[idx_label, col]
                row.append("" if pd.isna(val) else str(val))
            tbl_data.append(row)

        n_cols = len(tbl_data[0])
        col_w  = [3*cm] + [(14*cm / (n_cols - 1))] * (n_cols - 1)
        stat_tbl = Table(tbl_data, colWidths=col_w)
        stat_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D9E75")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#F0FBF6"), colors.white]),
            ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#9FE1CB")),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(stat_tbl)

        doc.build(story)
        logger.info("Report saved: %s", report_path)
        return report_path


report_agent = ReportAgent()
