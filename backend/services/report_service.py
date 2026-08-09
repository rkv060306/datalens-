import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.config import REPORTS_DIR
from backend.services.profiling_service import profiling_service
from backend.services.statistics_service import statistics_service
from backend.services.insight_service import insight_service

class ReportService:
    @staticmethod
    def generate_pdf_report(dataset_name: str, df: pd.DataFrame) -> Path:
        pdf_path = REPORTS_DIR / f"DataLens_Report_{dataset_name.replace(' ', '_')}.pdf"
        
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1e1b4b")
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b")
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#4f46e5"),
            spaceBefore=12,
            spaceAfter=6
        )
        normal_text = ParagraphStyle(
            'ReportText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )
        bullet_text = ParagraphStyle(
            'ReportBullet',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            leftIndent=15,
            spaceBefore=3
        )

        story = []

        # Title Header
        story.append(Paragraph("DataLens — Automated Analytics Report", title_style))
        story.append(Paragraph(f"Dataset Name: <b>{dataset_name}</b> | Generated automatically by DataLens Engine", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4f46e5"), spaceAfter=15))

        # 1. Executive Summary & Quality Score
        profile = profiling_service.profile_dataframe(df)
        story.append(Paragraph("1. Executive Summary & Data Quality", section_heading))
        
        summary_table_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Rows", f"{profile['rows']:,}", "Data Quality Score", f"{profile['qualityScore']}/100"],
            ["Total Columns", str(profile['columns']), "Quality Rating", profile['qualityBreakdown']['status']],
            ["Memory Usage", f"{profile['memoryUsageMB']} MB", "Duplicate Rows", str(profile['duplicateRows'])],
            ["Missing Cells", f"{profile['missingCells']} ({profile['missingPercentage']}%)", "Numeric Columns", str(profile['columnTypesSummary']['numeric'])]
        ]

        t_summary = Table(summary_table_data, colWidths=[130, 130, 130, 130])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 15))

        # 2. Key Statistical Insights
        insights = insight_service.generate_insights(df)
        story.append(Paragraph("2. Automated Key Insights", section_heading))
        for ins in insights:
            icon = "🔴" if ins['type'] == "warning" else ("🟡" if ins['type'] == "anomaly" else "🟢")
            story.append(Paragraph(f"{icon} <b>{ins['title']}</b> — {ins['description']}", bullet_text))
            story.append(Paragraph(f"<i>Technical Context:</i> {ins['explanation']}", ParagraphStyle('SubText', parent=bullet_text, fontSize=8, leading=10, textColor=colors.HexColor('#64748b'), leftIndent=25)))
        
        story.append(Spacer(1, 15))

        # 3. Numeric Features Summary Table
        stats = statistics_service.calculate_statistics(df)
        num_stats = stats.get("numeric", {})
        if num_stats:
            story.append(Paragraph("3. Numeric Summary Statistics", section_heading))
            num_headers = ["Column", "Count", "Mean", "Std Dev", "Min", "Median", "Max", "IQR"]
            table_rows = [num_headers]
            for col, s in list(num_stats.items())[:12]:
                table_rows.append([
                    col[:18], str(s['count']), str(s['mean']), str(s['std']),
                    str(s['min']), str(s['median']), str(s['max']), str(s['iqr'])
                ])
            
            t_stats = Table(table_rows, colWidths=[100, 50, 60, 60, 50, 60, 60, 50])
            t_stats.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ]))
            story.append(t_stats)
            story.append(Spacer(1, 15))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=10))
        story.append(Paragraph("Report produced by DataLens Universal Analytics Platform. Open-source & zero registration required.", subtitle_style))

        doc.build(story)
        return pdf_path

report_service = ReportService()
