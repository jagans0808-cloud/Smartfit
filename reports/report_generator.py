"""
SmartFit Report Generator Module
Compiles patient physiological metrics, exercise performance, sensor telemetry,
and posture analytics into a publication-quality PDF report using ReportLab.

DISCLAIMER:
Informational fitness monitoring only. Not for medical diagnosis or clinical use.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)

import config
from database.database import db


class ReportGenerator:
    """Generates PDF session reports from database records."""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.app_config.REPORT_OUTPUT_PATH if hasattr(config.app_config, 'REPORT_OUTPUT_PATH') else config.REPORT_OUTPUT_PATH
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf(self, session_id: int) -> Optional[str]:
        """
        Creates a PDF report for session_id.
        Returns the absolute filepath to the created PDF.
        """
        session = db.get_session(session_id)
        if not session:
            print(f"[ReportGenerator] Session {session_id} not found.")
            return None

        patient_name = session.get("patient_name") or "Anonymous"
        clean_patient_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"SmartFit_Report_Session_{session_id}_{clean_patient_name}.pdf".replace(" ", "_")
        pdf_path = os.path.join(self.output_dir, filename)

        # Retrieve session data, alerts, and repetitions
        alerts = db.get_session_alerts(session_id)
        reps = db.get_session_exercise_results(session_id)
        df_sensor = db.get_session_sensor_data(session_id)

        # Generate summary plot image
        plot_path = self._generate_session_plots(session_id, df_sensor)

        # Build PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom styling
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            alignment=1  # Centered
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            alignment=1
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0284c7'),
            spaceBefore=12,
            spaceAfter=6
        )

        cell_text = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )

        cell_bold = ParagraphStyle(
            'CellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        )

        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#dc2626'),
            alignment=1
        )

        # 1. Header Banner
        story.append(Paragraph("SMARTFIT FITNESS MONITORING REPORT", title_style))
        story.append(Paragraph("Real-Time Physiological & Biomechanical Session Evaluation", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=12))

        # 2. Patient & Session Overview Table
        patient_data = [
            [
                Paragraph("<b>Patient Name:</b>", cell_bold), Paragraph(str(session.get("patient_name") or "Unassigned"), cell_text),
                Paragraph("<b>Session ID:</b>", cell_bold), Paragraph(str(session["id"]), cell_text)
            ],
            [
                Paragraph("<b>Age / Gender:</b>", cell_bold), Paragraph(f"{session.get('patient_age') or 'N/A'} yrs / {session.get('patient_gender') or 'N/A'}", cell_text),
                Paragraph("<b>Exercise:</b>", cell_bold), Paragraph(str(session["exercise"]), cell_text)
            ],
            [
                Paragraph("<b>Height / Weight:</b>", cell_bold), Paragraph(f"{session.get('patient_height') or 'N/A'} cm / {session.get('patient_weight') or 'N/A'} kg", cell_text),
                Paragraph("<b>Start Time:</b>", cell_bold), Paragraph(str(session["start_time"]), cell_text)
            ],
            [
                Paragraph("<b>Duration:</b>", cell_bold), Paragraph(f"{session.get('duration', 0):.1f} seconds", cell_text),
                Paragraph("<b>End Time:</b>", cell_bold), Paragraph(str(session.get("end_time") or "N/A"), cell_text)
            ]
        ]

        t_overview = Table(patient_data, colWidths=[100, 170, 90, 180])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 12))

        # 3. Physiological & Exercise Metrics Table
        story.append(Paragraph("Physiological & Exercise Performance Summary", section_heading))

        avg_hr = f"{session['average_hr']:.1f} bpm" if session.get('average_hr') is not None else "N/A"
        min_hr = f"{session['min_hr']:.1f} bpm" if session.get('min_hr') is not None else "N/A"
        max_hr = f"{session['max_hr']:.1f} bpm" if session.get('max_hr') is not None else "N/A"
        avg_spo2 = f"{session['average_spo2']:.1f} %" if session.get('average_spo2') is not None else "N/A"
        avg_temp = f"{session['average_temperature']:.1f} °C" if session.get('average_temperature') is not None else "N/A"
        posture_score = f"{session['posture_score']:.1f} %" if session.get('posture_score') is not None else "100.0 %"

        tot_reps = session.get("total_repetitions", 0)
        corr_reps = session.get("correct_repetitions", 0)
        incorr_reps = session.get("incorrect_repetitions", 0)
        accuracy = f"{(corr_reps / tot_reps * 100):.1f} %" if tot_reps > 0 else "N/A"

        metrics_data = [
            [
                Paragraph("<b>Metric Category</b>", cell_bold),
                Paragraph("<b>Parameter</b>", cell_bold),
                Paragraph("<b>Recorded Value</b>", cell_bold),
                Paragraph("<b>Evaluation Notes</b>", cell_bold)
            ],
            [
                Paragraph("Cardiovascular", cell_text),
                Paragraph("Average Heart Rate", cell_text),
                Paragraph(avg_hr, cell_bold),
                Paragraph(f"Min: {min_hr} | Max: {max_hr}", cell_text)
            ],
            [
                Paragraph("Oxygenation", cell_text),
                Paragraph("Average SpO2", cell_text),
                Paragraph(avg_spo2, cell_bold),
                Paragraph("Normative range: >= 95%", cell_text)
            ],
            [
                Paragraph("Thermal", cell_text),
                Paragraph("Average Body Temp", cell_text),
                Paragraph(avg_temp, cell_bold),
                Paragraph("Normative range: 36.1 - 37.5 °C", cell_text)
            ],
            [
                Paragraph("Biomechanics", cell_text),
                Paragraph("Total Repetitions", cell_text),
                Paragraph(str(tot_reps), cell_bold),
                Paragraph(f"Correct: {corr_reps} | Incorrect: {incorr_reps}", cell_text)
            ],
            [
                Paragraph("Movement Quality", cell_text),
                Paragraph("Repetition Accuracy", cell_text),
                Paragraph(accuracy, cell_bold),
                Paragraph("Based on sensor inflection criteria", cell_text)
            ],
            [
                Paragraph("Alignment", cell_text),
                Paragraph("Posture Quality Score", cell_text),
                Paragraph(posture_score, cell_bold),
                Paragraph("Fusion of MPU6050, Flex, & FSR", cell_text)
            ]
        ]

        t_metrics = Table(metrics_data, colWidths=[110, 140, 110, 180])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 10))

        # 4. Sensor Telemetry Graph
        if plot_path and os.path.exists(plot_path):
            story.append(Paragraph("Session Telemetry Waveforms", section_heading))
            story.append(Image(plot_path, width=540, height=190))
            story.append(Spacer(1, 10))

        # 5. Alerts Summary Section
        story.append(Paragraph(f"System Alerts Recorded ({len(alerts)})", section_heading))
        if alerts:
            alerts_data = [
                [
                    Paragraph("<b>Time</b>", cell_bold),
                    Paragraph("<b>Alert Type</b>", cell_bold),
                    Paragraph("<b>Severity</b>", cell_bold),
                    Paragraph("<b>Description</b>", cell_bold)
                ]
            ]
            for a in alerts[:8]:  # Limit top 8 alerts for page layout
                dt = datetime.fromtimestamp(a["timestamp"] / 1000.0).strftime("%H:%M:%S")
                sev_color = '#dc2626' if a['severity'] == 'CRITICAL' else '#d97706'
                sev_p = Paragraph(f"<font color='{sev_color}'><b>{a['severity']}</b></font>", cell_text)
                alerts_data.append([
                    Paragraph(dt, cell_text),
                    Paragraph(a["alert_type"], cell_text),
                    sev_p,
                    Paragraph(a["message"], cell_text)
                ])

            t_alerts = Table(alerts_data, colWidths=[65, 120, 75, 280])
            t_alerts.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_alerts)
        else:
            story.append(Paragraph("No physiological or threshold alerts triggered during this session.", cell_text))

        story.append(Spacer(1, 14))

        # 6. Session Notes / Clinical Summary
        notes = session.get("notes") or "Session completed normally without interruption."
        story.append(Paragraph("Session Summary & Notes", section_heading))
        story.append(Paragraph(notes, cell_text))
        story.append(Spacer(1, 14))

        # 7. Medical Disclaimer Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8))
        story.append(Paragraph(
            "IMPORTANT MEDICAL DISCLAIMER: SmartFit is an educational, research, and fitness monitoring prototype. "
            "The data, waveforms, and automated assessments provided herein are NOT intended to diagnose, treat, cure, "
            "or prevent any disease or medical condition. For medical concerns, always consult a licensed physician.",
            disclaimer_style
        ))

        # Build document
        doc.build(story)

        # Cleanup temporary plot image
        if plot_path and os.path.exists(plot_path):
            try:
                os.remove(plot_path)
            except Exception:
                pass

        return pdf_path

    def _generate_session_plots(self, session_id: int, df) -> Optional[str]:
        """Generates a combined multi-panel plot image of session sensor data."""
        if df is None or df.empty or len(df) < 5:
            return None

        try:
            fig, axs = plt.subplots(3, 1, figsize=(8, 2.8), sharex=True)
            plt.subplots_adjust(hspace=0.25, top=0.92, bottom=0.18, left=0.08, right=0.96)

            # Elapsed time in seconds
            t0 = df['timestamp'].iloc[0]
            t = (df['timestamp'] - t0) / 1000.0

            # 1. Heart Rate & SpO2
            ax0 = axs[0]
            if 'heart_rate' in df.columns and df['heart_rate'].dropna().count() > 0:
                ax0.plot(t, df['heart_rate'], color='#ef4444', lw=1.2, label='HR (bpm)')
            ax0.set_ylabel('HR', fontsize=7, color='#ef4444')
            ax0.tick_params(axis='both', labelsize=6)
            ax0.grid(True, linestyle=':', alpha=0.5)

            # Secondary axis for SpO2
            if 'spo2' in df.columns and df['spo2'].dropna().count() > 0:
                ax0_r = ax0.twinx()
                ax0_r.plot(t, df['spo2'], color='#0284c7', lw=1.0, linestyle='--', label='SpO2 (%)')
                ax0_r.set_ylabel('SpO2', fontsize=7, color='#0284c7')
                ax0_r.tick_params(axis='both', labelsize=6)

            # 2. Movement / Acceleration Magnitude
            ax1 = axs[1]
            if all(col in df.columns for col in ['accel_x', 'accel_y', 'accel_z']):
                mag = (df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)**0.5
                ax1.plot(t, mag, color='#8b5cf6', lw=1.0)
            ax1.set_ylabel('Accel (m/s²)', fontsize=7, color='#8b5cf6')
            ax1.tick_params(axis='both', labelsize=6)
            ax1.grid(True, linestyle=':', alpha=0.5)

            # 3. Flex & FSR Pressure
            ax2 = axs[2]
            if 'flex' in df.columns and df['flex'].dropna().count() > 0:
                ax2.plot(t, df['flex'], color='#10b981', lw=1.0, label='Flex')
            if 'fsr_heel' in df.columns and df['fsr_heel'].dropna().count() > 0:
                ax2.plot(t, df['fsr_heel'], color='#f59e0b', lw=0.8, linestyle=':', label='FSR Heel')
            ax2.set_ylabel('Flex/FSR', fontsize=7, color='#10b981')
            ax2.set_xlabel('Elapsed Time (seconds)', fontsize=7)
            ax2.tick_params(axis='both', labelsize=6)
            ax2.grid(True, linestyle=':', alpha=0.5)

            temp_img = os.path.join(self.output_dir, f"temp_plot_{session_id}.png")
            fig.savefig(temp_img, dpi=180)
            plt.close(fig)
            return temp_img
        except Exception as e:
            print(f"[ReportGenerator] Error creating plot: {e}")
            return None


report_gen = ReportGenerator()
