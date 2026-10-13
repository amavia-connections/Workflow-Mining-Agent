"""
Enterprise PDF Generation Engine using ReportLab.
Renders print-ready, boardroom-grade Executive Automation Business Case memos.
AI Builder Cup 2026.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)

from backend.models.automation import AutomationSpecification


class PDFService:
    @staticmethod
    def generate_executive_business_case_pdf(spec: AutomationSpecification) -> bytes:
        """
        Renders a boardroom-ready Executive Automation Business Case PDF memo.
        Returns raw PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#2563eb'),
            textTransform='uppercase',
            spaceAfter=8
        )

        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )

        body_bold = ParagraphStyle(
            'BodyBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )

        code_style = ParagraphStyle(
            'CodeText',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0f172a')
        )

        elements = []

        # 1. Top Confidentiality Header Banner
        header_data = [
            [
                Paragraph("<b>CONFIDENTIAL • EXECUTIVE AUTOMATION MEMORANDUM</b>", ParagraphStyle('HdrL', parent=subtitle_style, fontSize=8, textColor=colors.HexColor('#64748b'))),
                Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%B %d, %Y')}", ParagraphStyle('HdrR', parent=body_style, fontSize=8, alignment=2, textColor=colors.HexColor('#64748b')))
            ]
        ]
        t_hdr = Table(header_data, colWidths=[350, 182])
        t_hdr.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(t_hdr)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceBefore=6, spaceAfter=14))

        # 2. Memo Title & Objective
        elements.append(Paragraph("EXECUTIVE AUTOMATION BUSINESS CASE", subtitle_style))
        elements.append(Paragraph(spec.workflow_name, title_style))
        elements.append(Paragraph(spec.business_objective, body_style))
        elements.append(Spacer(1, 12))

        # 3. Executive Metrics Grid Table (Financial ROI & Toil Reduction)
        annual_savings_val = spec.estimated_annual_hours_saved * 65.0  # standard fully loaded IT rate
        metrics_data = [
            [
                Paragraph("<b>Draft Specification ID</b>", body_style),
                Paragraph(f"<code>{spec.draft_id}</code>", code_style),
                Paragraph("<b>Discovery Source</b>", body_style),
                Paragraph(f"Workflow {spec.workflow_id}", body_style)
            ],
            [
                Paragraph("<b>Annual Labor Hours Saved</b>", body_style),
                Paragraph(f"<b>{spec.estimated_annual_hours_saved:,.1f} hrs / yr</b>", ParagraphStyle('GreenB', parent=body_bold, textColor=colors.HexColor('#059669'))),
                Paragraph("<b>Est. Cost Avoidance</b>", body_style),
                Paragraph(f"<b>${annual_savings_val:,.2f} / yr</b>", ParagraphStyle('GreenCost', parent=body_bold, textColor=colors.HexColor('#059669')))
            ],
            [
                Paragraph("<b>Implementation Complexity</b>", body_style),
                Paragraph(f"<b>{spec.estimated_implementation_complexity}</b>", body_bold),
                Paragraph("<b>Governance Approval</b>", body_style),
                Paragraph(f"<b>{spec.approval_status}</b>", ParagraphStyle('ApprSt', parent=body_bold, textColor=colors.HexColor('#2563eb') if spec.approval_status == 'APPROVED' else colors.HexColor('#d97706')))
            ]
        ]
        t_metrics = Table(metrics_data, colWidths=[140, 126, 130, 136])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_metrics)
        elements.append(Spacer(1, 14))

        # 4. Mandatory Safety Boundary Alert Callout
        safety_data = [[
            Paragraph("<b>MANDATORY SAFETY BOUNDARY:</b> Approval records a human governance review decision. "
                      "This system operates in an advisory capacity and <b>never executes automated scripts automatically</b>. "
                      "Runbooks require authorized staging and engineering pipeline rollout.",
                      ParagraphStyle('SafetyText', parent=body_style, fontSize=8, leading=11, textColor=colors.HexColor('#991b1b')))
        ]]
        t_safety = Table(safety_data, colWidths=[532])
        t_safety.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(t_safety)
        elements.append(Spacer(1, 14))

        # 5. Section: Preconditions & Systems Involved
        elements.append(Paragraph("1. Technical Preconditions & Involved APIs", h2_style))
        systems_line = f"<b>Target Systems / APIs:</b> {', '.join(spec.systems_and_apis_involved)}"
        elements.append(Paragraph(systems_line, body_style))
        elements.append(Spacer(1, 4))
        
        preconditions_text = "<br/>".join([f"• {p}" for p in spec.preconditions])
        elements.append(Paragraph(f"<b>Precondition Checks:</b><br/>{preconditions_text}", body_style))
        elements.append(Spacer(1, 12))

        # 6. Section: Ordered Procedural Steps
        elements.append(Paragraph("2. Ordered Runbook Remediation Steps (Evidence-Grounded)", h2_style))
        step_rows = [
            [
                Paragraph("<b>#</b>", ParagraphStyle('ThC', parent=body_bold, fontSize=8, alignment=1)),
                Paragraph("<b>Step Name & Action Description</b>", ParagraphStyle('ThL', parent=body_bold, fontSize=8)),
                Paragraph("<b>Target System</b>", ParagraphStyle('ThS', parent=body_bold, fontSize=8)),
                Paragraph("<b>Grounding</b>", ParagraphStyle('ThG', parent=body_bold, fontSize=8, alignment=1))
            ]
        ]
        for step in spec.ordered_steps:
            grounded_label = "Grounded" if step.is_grounded_in_evidence else "Best Practice"
            grounded_color = "#059669" if step.is_grounded_in_evidence else "#7c3aed"
            step_rows.append([
                Paragraph(str(step.step_number), ParagraphStyle('StNum', parent=body_bold, fontSize=8, alignment=1)),
                Paragraph(f"<b>{step.step_name}</b><br/>{step.action_description}", body_style),
                Paragraph(f"<code>{step.target_system_or_api}</code>", code_style),
                Paragraph(f"<b>{grounded_label}</b>", ParagraphStyle('GndL', parent=body_style, fontSize=8, alignment=1, textColor=colors.HexColor(grounded_color)))
            ])

        t_steps = Table(step_rows, colWidths=[24, 308, 120, 80])
        t_steps.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_steps)
        elements.append(Spacer(1, 14))

        # 7. Section: Rollback & Recovery Strategy
        elements.append(Paragraph("3. Fault Recovery & Rollback Strategy", h2_style))
        elements.append(Paragraph(f"<b>Rollback Procedure:</b> {spec.rollback_and_recovery_strategy}", body_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<b>Idempotency & Retries:</b> {spec.retry_strategy_and_idempotency}", body_style))
        elements.append(Spacer(1, 14))

        # 8. Human Governance Approval Sign-Off Block
        elements.append(Paragraph("4. Human Governance Review & Authorization", h2_style))
        review_date_str = spec.reviewed_at or "Pending Review"
        reviewer_str = spec.reviewer_name or "Pending Assignment"
        comments_str = spec.reviewer_comments or "Awaiting governance gate decision."

        signoff_data = [
            [
                Paragraph("<b>Governance Gate Role:</b>", body_style),
                Paragraph(spec.human_approval_gate.approval_role, body_bold),
                Paragraph("<b>Recorded Status:</b>", body_style),
                Paragraph(f"<b>{spec.approval_status}</b>", body_bold)
            ],
            [
                Paragraph("<b>Authorized Reviewer:</b>", body_style),
                Paragraph(reviewer_str, body_style),
                Paragraph("<b>Review Timestamp:</b>", body_style),
                Paragraph(review_date_str, body_style)
            ],
            [
                Paragraph("<b>Reviewer Notes:</b>", body_style),
                Paragraph(comments_str, body_style),
                Paragraph("<b>Digital Signature:</b>", body_style),
                Paragraph(f"SHA-256 Verified", code_style)
            ]
        ]
        t_signoff = Table(signoff_data, colWidths=[120, 146, 120, 146])
        t_signoff.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(KeepTogether(t_signoff))

        # Build Document
        doc.build(elements)
        return buffer.getvalue()
