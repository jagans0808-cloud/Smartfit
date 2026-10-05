"""
Smart Cardiac Chest Belt - PDF Report & Data Export Generator
Generates clinical session summary PDF reports using ReportLab,
incorporating metadata, statistical aggregates, fall events, alert logs,
and high-resolution ECG waveform plots.
"""

import os
from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

import config
from database.database import db


class ReportGenerator:
    """PDF and CSV export engine for Smart Cardiac Chest Belt."""

    def __init__(self, output_dir: str = config.REPORTS_OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf(self, session_id: int) -> Optional[str]:
        """
        Compiles a publication-grade PDF report for a session.
        Returns the absolute filepath of the generated PDF.
        """
        session = db.get_session(session_id)
        if not session:
            return None

        sensor_df = db.get_session_sensor_data(session_id)
        alerts = db.get_session_alerts(session_id)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"SmartCardiac_Report_Session_{session_id}_{timestamp_str}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0284c7'),
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#1e293b')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#64748b'),
            alignment=1
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph(config.PROJECT_TITLE, title_style))
        elements.append(Paragraph(config.PROJECT_SUBTITLE, subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=14))

        # 2. Session Summary Metadata Table
        start_t = session.get("start_time") or "N/A"
        end_t = session.get("end_time") or "N/A"
        duration_s = session.get("duration", 0.0)
        dur_mins = int(duration_s // 60)
        dur_secs = int(duration_s % 60)
        duration_str = f"{dur_mins}m {dur_secs:02d}s ({duration_s:.1f} seconds)"

        meta_data = [
            [
                Paragraph("<b>Session ID:</b>", body_style), Paragraph(f"#{session_id}", body_style),
                Paragraph("<b>Generated Date:</b>", body_style), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), body_style)
            ],
            [
                Paragraph("<b>Start Time:</b>", body_style), Paragraph(str(start_t), body_style),
                Paragraph("<b>End Time:</b>", body_style), Paragraph(str(end_t), body_style)
            ],
            [
                Paragraph("<b>Duration:</b>", body_style), Paragraph(duration_str, body_style),
                Paragraph("<b>Status:</b>", body_style), Paragraph("Completed & Archived", body_style)
            ]
        ]

        t_meta = Table(meta_data, colWidths=[100, 170, 110, 160])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 14))

        # 3. Aggregated Physiological & Kinetic Parameters
        elements.append(Paragraph("1. Physiological & Biomechanical Summary", section_style))

        avg_hr = session.get("average_hr")
        min_hr = session.get("min_hr")
        max_hr = session.get("max_hr")
        avg_rr = session.get("average_rr")
        avg_temp = session.get("average_temperature")
        max_temp = session.get("max_temperature")
        fall_count = session.get("fall_count", 0)

        # Fallback to computing from dataframe if not in session row
        if not sensor_df.empty:
            if avg_hr is None and 'heart_rate' in sensor_df.columns:
                valid_hr = sensor_df['heart_rate'].dropna()
                if not valid_hr.empty:
                    avg_hr = valid_hr.mean()
                    min_hr = valid_hr.min()
                    max_hr = valid_hr.max()

            if avg_rr is None and 'rr_interval' in sensor_df.columns:
                valid_rr = sensor_df['rr_interval'].dropna()
                if not valid_rr.empty:
                    avg_rr = valid_rr.mean()

            if avg_temp is None and 'temperature' in sensor_df.columns:
                valid_temp = sensor_df['temperature'].dropna()
                if not valid_temp.empty:
                    avg_temp = valid_temp.mean()
                    max_temp = valid_temp.max()

            if fall_count == 0 and 'fall' in sensor_df.columns:
                fall_count = int(sensor_df['fall'].sum())

        vitals_table_data = [
            [
                Paragraph("<b>Parameter</b>", body_style),
                Paragraph("<b>Average</b>", body_style),
                Paragraph("<b>Minimum</b>", body_style),
                Paragraph("<b>Maximum</b>", body_style),
                Paragraph("<b>Normative Baseline</b>", body_style)
            ],
            [
                Paragraph("<b>Heart Rate (BPM)</b>", body_style),
                Paragraph(f"{avg_hr:.1f} BPM" if avg_hr is not None else "--", body_style),
                Paragraph(f"{min_hr:.1f} BPM" if min_hr is not None else "--", body_style),
                Paragraph(f"{max_hr:.1f} BPM" if max_hr is not None else "--", body_style),
                Paragraph("60 - 100 BPM (Resting)", body_style)
            ],
            [
                Paragraph("<b>RR Interval (ms)</b>", body_style),
                Paragraph(f"{avg_rr:.1f} ms" if avg_rr is not None else "--", body_style),
                Paragraph("--", body_style),
                Paragraph("--", body_style),
                Paragraph("600 - 1200 ms", body_style)
            ],
            [
                Paragraph("<b>Body Temperature (°C)</b>", body_style),
                Paragraph(f"{avg_temp:.1f} °C" if avg_temp is not None else "--", body_style),
                Paragraph("--", body_style),
                Paragraph(f"{max_temp:.1f} °C" if max_temp is not None else "--", body_style),
                Paragraph("36.1 - 37.5 °C (Normative)", body_style)
            ],
            [
                Paragraph("<b>Fall Events (MPU6050)</b>", body_style),
                Paragraph(f"<b>{fall_count} Fall(s) Detected</b>", body_style),
                Paragraph("0", body_style),
                Paragraph(str(fall_count), body_style),
                Paragraph("0 Falls Expected", body_style)
            ]
        ]

        t_vitals = Table(vitals_table_data, colWidths=[150, 95, 80, 85, 130])
        t_vitals.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_vitals)
        elements.append(Spacer(1, 14))

        # 4. ECG Waveform Snapshot Plot
        plot_image_path = self._generate_ecg_plot_image(session_id, sensor_df)
        if plot_image_path and os.path.exists(plot_image_path):
            elements.append(Paragraph("2. Electrocardiogram (AD8232) Waveform Trace", section_style))
            elements.append(Image(plot_image_path, width=540, height=140))
            elements.append(Spacer(1, 14))

        # 5. Alert History Summary
        elements.append(Paragraph("3. Event & Alert Audit Log", section_style))
        if alerts:
            alert_rows = [
                [
                    Paragraph("<b>Timestamp</b>", body_style),
                    Paragraph("<b>Type</b>", body_style),
                    Paragraph("<b>Severity</b>", body_style),
                    Paragraph("<b>Message</b>", body_style)
                ]
            ]
            for a in alerts[:10]:
                alert_rows.append([
                    Paragraph(str(a.get("timestamp", "")), body_style),
                    Paragraph(str(a.get("alert_type", "")), body_style),
                    Paragraph(str(a.get("severity", "")), body_style),
                    Paragraph(str(a.get("message", "")), body_style),
                ])
            t_alerts = Table(alert_rows, colWidths=[80, 110, 80, 270])
            t_alerts.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_alerts)
        else:
            elements.append(Paragraph("✓ No adverse physiological threshold alarms or fall events triggered during this session.", body_style))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=8))

        # 6. Bottom Prototype Disclaimer
        elements.append(Paragraph(config.PROJECT_DISCLAIMER, disclaimer_style))
        elements.append(Paragraph("This prototype is designed solely for educational, engineering, and investigative research.", disclaimer_style))

        # Build document
        doc.build(elements)

        # Clean temporary plot image
        if plot_image_path and os.path.exists(plot_image_path):
            try:
                os.remove(plot_image_path)
            except Exception:
                pass

        return pdf_path

    def _generate_ecg_plot_image(self, session_id: int, df: pd.DataFrame) -> Optional[str]:
        """Renders an ECG waveform snippet to a temporary PNG file."""
        if df.empty or 'ecg' not in df.columns:
            return None

        valid_ecg = df['ecg'].dropna()
        if len(valid_ecg) < 10:
            return None

        # Take up to 1000 samples for clean crisp replay
        snippet = valid_ecg.iloc[:1000]
        x_vals = range(len(snippet))

        fig, ax = plt.subplots(figsize=(8.0, 2.0), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')

        ax.plot(x_vals, snippet.values, color='#059669', linewidth=1.2)
        ax.set_title("AD8232 ECG Biopotential Waveform Trace", fontsize=9, fontweight='bold', color='#0f172a', pad=4)
        ax.set_xlabel("Sample Index (250 Hz)", fontsize=8, color='#64748b')
        ax.set_ylabel("Amplitude (ADC)", fontsize=8, color='#64748b')

        ax.grid(True, linestyle='--', alpha=0.35, color='#cbd5e1')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.tick_params(colors='#64748b', labelsize=7)

        plt.tight_layout()
        img_path = os.path.join(self.output_dir, f"temp_ecg_session_{session_id}.png")
        plt.savefig(img_path, format='png', facecolor='#ffffff', edgecolor='none')
        plt.close(fig)

        return img_path


# Global report generator singleton
report_gen = ReportGenerator()
