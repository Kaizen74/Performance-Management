"""
Test Fixture Generator
Creates mock documents for testing the document processor.
"""

import os
from pathlib import Path

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent


def create_mock_pdf(output_path: str = None) -> str:
    """
    Create a mock strategy PDF document.
    Uses reportlab if available, otherwise creates a minimal PDF.
    """
    if output_path is None:
        output_path = FIXTURES_DIR / "mock_strategy_doc.pdf"

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        c = canvas.Canvas(str(output_path), pagesize=letter)
        width, height = letter

        # Page 1 - Vision and Mission
        y = height - inch

        c.setFont("Helvetica-Bold", 24)
        c.drawString(inch, y, "STRATEGIC PLAN 2025-2030")
        y -= 0.5 * inch

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, "VISION")
        y -= 0.3 * inch

        c.setFont("Helvetica", 12)
        vision_text = "To be the leading sustainable logistics provider in Asia-Pacific by 2030, "
        vision_text += "connecting businesses to opportunities while setting new standards for "
        vision_text += "environmental responsibility and operational excellence."
        c.drawString(inch, y, vision_text[:80])
        y -= 0.2 * inch
        c.drawString(inch, y, vision_text[80:])
        y -= 0.5 * inch

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, "MISSION")
        y -= 0.3 * inch

        c.setFont("Helvetica", 12)
        mission_text = "We deliver excellence through innovation, connecting businesses to global "
        mission_text += "opportunities while minimizing environmental impact and maximizing value "
        mission_text += "for all stakeholders."
        c.drawString(inch, y, mission_text[:80])
        y -= 0.2 * inch
        c.drawString(inch, y, mission_text[80:])
        y -= 0.5 * inch

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, "STRATEGIC PRIORITIES")
        y -= 0.3 * inch

        priorities = [
            "1. Digital Transformation - Implement AI-driven route optimization and real-time tracking",
            "2. Sustainability Leadership - Achieve carbon neutrality by 2028 through fleet electrification",
            "3. Customer Excellence - Achieve NPS > 70 across all customer segments",
            "4. Operational Efficiency - 15% reduction in unit costs through process automation",
            "5. Talent Development - Build future-ready workforce with digital skills"
        ]

        c.setFont("Helvetica", 11)
        for priority in priorities:
            if y < inch:
                c.showPage()
                y = height - inch
            c.drawString(inch, y, priority[:90])
            if len(priority) > 90:
                y -= 0.2 * inch
                c.drawString(inch + 0.2 * inch, y, priority[90:])
            y -= 0.3 * inch

        # Page 2 - Values and KPIs
        c.showPage()
        y = height - inch

        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, "CORE VALUES")
        y -= 0.3 * inch

        values = [
            "Innovation - We embrace change and continuously seek better solutions",
            "Integrity - We act with honesty and transparency in all dealings",
            "Sustainability - We protect our planet for future generations",
            "Excellence - We strive for the highest quality in everything we do",
            "Collaboration - We achieve more together than alone"
        ]

        c.setFont("Helvetica", 11)
        for value in values:
            c.drawString(inch, y, value)
            y -= 0.25 * inch

        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, y, "KEY PERFORMANCE INDICATORS")
        y -= 0.3 * inch

        c.setFont("Helvetica", 11)
        kpis = [
            "Revenue Growth: 12% CAGR",
            "EBITDA Margin: > 18%",
            "Customer NPS: > 70",
            "Carbon Intensity: -30% by 2028",
            "Employee Engagement: > 80%"
        ]
        for kpi in kpis:
            c.drawString(inch, y, kpi)
            y -= 0.25 * inch

        c.save()
        return str(output_path)

    except ImportError:
        # Create a minimal valid PDF without reportlab
        # This is a minimal PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 24 Tf
50 700 Td
(STRATEGIC PLAN 2025-2030) Tj
0 -40 Td
/F1 12 Tf
(Vision: Leading sustainable logistics provider) Tj
0 -20 Td
(Mission: Excellence through innovation) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
464
%%EOF
"""
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
        return str(output_path)


def create_mock_docx(output_path: str = None) -> str:
    """
    Create a mock employee goals DOCX document.
    """
    if output_path is None:
        output_path = FIXTURES_DIR / "mock_employee_goals.docx"

    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # Title
        title = doc.add_heading('Employee Performance Goals FY2025', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Employee Info
        doc.add_paragraph('Employee: Jane Smith')
        doc.add_paragraph('Role: Operations Manager')
        doc.add_paragraph('Department: Supply Chain')
        doc.add_paragraph('Review Period: January 2025 - December 2025')
        doc.add_paragraph()

        # Goal 1
        doc.add_heading('Goal 1: Process Improvement', level=1)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text = 'Objective'
        cells[1].text = 'Reduce warehouse processing time by 20% through lean methodology implementation'
        cells = table.rows[1].cells
        cells[0].text = 'Measure'
        cells[1].text = 'Average processing time per unit (hours)'
        cells = table.rows[2].cells
        cells[0].text = 'Target'
        cells[1].text = 'From 4.5 hours to 3.6 hours per unit'
        cells = table.rows[3].cells
        cells[0].text = 'Timeline'
        cells[1].text = 'Q4 2025'

        doc.add_paragraph()

        # Goal 2
        doc.add_heading('Goal 2: System Implementation', level=1)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text = 'Objective'
        cells[1].text = 'Implement new inventory management system across all warehouses'
        cells = table.rows[1].cells
        cells[0].text = 'Measure'
        cells[1].text = 'System deployment status and inventory accuracy rate'
        cells = table.rows[2].cells
        cells[0].text = 'Target'
        cells[1].text = '100% deployment, 99% inventory accuracy'
        cells = table.rows[3].cells
        cells[0].text = 'Timeline'
        cells[1].text = 'Q2 2025'

        doc.add_paragraph()

        # Goal 3
        doc.add_heading('Goal 3: Team Engagement', level=1)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text = 'Objective'
        cells[1].text = 'Improve team engagement and satisfaction scores'
        cells = table.rows[1].cells
        cells[0].text = 'Measure'
        cells[1].text = 'Annual engagement survey score'
        cells = table.rows[2].cells
        cells[0].text = 'Target'
        cells[1].text = 'Achieve team engagement score of 4.2/5.0 (up from 3.8)'
        cells = table.rows[3].cells
        cells[0].text = 'Timeline'
        cells[1].text = 'December 2025'

        doc.add_paragraph()

        # Goal 4
        doc.add_heading('Goal 4: Professional Development', level=1)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text = 'Objective'
        cells[1].text = 'Complete Six Sigma Green Belt certification'
        cells = table.rows[1].cells
        cells[0].text = 'Measure'
        cells[1].text = 'Certification completion and project application'
        cells = table.rows[2].cells
        cells[0].text = 'Target'
        cells[1].text = 'Obtain certification and apply to one improvement project'
        cells = table.rows[3].cells
        cells[0].text = 'Timeline'
        cells[1].text = 'Q3 2025'

        doc.add_paragraph()

        # Goal 5
        doc.add_heading('Goal 5: Cost Reduction', level=1)
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = table.rows[0].cells
        cells[0].text = 'Objective'
        cells[1].text = 'Identify and implement cost savings in logistics operations'
        cells = table.rows[1].cells
        cells[0].text = 'Measure'
        cells[1].text = 'Total cost savings achieved (USD)'
        cells = table.rows[2].cells
        cells[0].text = 'Target'
        cells[1].text = '$250,000 annual cost reduction'
        cells = table.rows[3].cells
        cells[0].text = 'Timeline'
        cells[1].text = 'December 2025'

        doc.save(str(output_path))
        return str(output_path)

    except ImportError:
        # Create a simple text file as fallback (not a real DOCX)
        text_content = """Employee Performance Goals FY2025

Employee: Jane Smith
Role: Operations Manager
Department: Supply Chain

Goal 1: Process Improvement
Objective: Reduce warehouse processing time by 20% through lean methodology
Measure: Average processing time per unit
Target: From 4.5 hours to 3.6 hours
Timeline: Q4 2025

Goal 2: System Implementation
Objective: Implement new inventory management system
Measure: System deployment status
Target: 100% deployment, 99% accuracy
Timeline: Q2 2025

Goal 3: Team Engagement
Objective: Improve team engagement scores
Measure: Annual engagement survey
Target: 4.2/5.0 score
Timeline: December 2025

Goal 4: Professional Development
Objective: Complete Six Sigma Green Belt certification
Measure: Certification completion
Target: Obtain certification
Timeline: Q3 2025

Goal 5: Cost Reduction
Objective: Identify and implement cost savings
Measure: Total savings
Target: $250,000 annual reduction
Timeline: December 2025
"""
        # For testing, we'll still try to create a real DOCX
        raise ImportError("python-docx required to create DOCX fixtures")


def create_mock_xlsx(output_path: str = None) -> str:
    """
    Create a mock KPI tracker XLSX document.
    """
    if output_path is None:
        output_path = FIXTURES_DIR / "mock_kpi_tracker.xlsx"

    try:
        import pandas as pd

        # Sheet 1: KPI Tracker
        kpi_data = {
            'KPI': [
                'Revenue Growth',
                'EBITDA Margin',
                'Customer NPS',
                'On-Time Delivery',
                'Carbon Intensity',
                'Employee Engagement',
                'Inventory Turnover',
                'Order Accuracy',
                'Customer Retention',
                'Cost per Unit',
                'Fleet Utilization',
                'Safety Incidents'
            ],
            'Target': [
                '12%', '18%', '70', '95%', '-30%',
                '80%', '8x', '99.5%', '92%', '$45', '85%', '0'
            ],
            'Actual': [
                '10.5%', '16.2%', '65', '93%', '-18%',
                '75%', '7.2x', '99.1%', '89%', '$48', '82%', '2'
            ],
            'Owner': [
                'CFO', 'CFO', 'CMO', 'COO', 'CSO',
                'CHRO', 'COO', 'COO', 'CMO', 'COO', 'COO', 'COO'
            ],
            'Category': [
                'Financial', 'Financial', 'Customer', 'Customer', 'Sustainability',
                'People', 'Operations', 'Operations', 'Customer', 'Operations',
                'Operations', 'Safety'
            ],
            'Status': [
                'At Risk', 'At Risk', 'At Risk', 'On Track', 'At Risk',
                'On Track', 'At Risk', 'On Track', 'At Risk', 'At Risk',
                'On Track', 'At Risk'
            ]
        }
        df_kpi = pd.DataFrame(kpi_data)

        # Sheet 2: Strategic Initiatives
        initiatives_data = {
            'Initiative': [
                'AI Route Optimization',
                'Fleet Electrification',
                'Customer Portal 2.0',
                'Warehouse Automation',
                'Digital Skills Program'
            ],
            'Strategic Priority': [
                'Digital Transformation',
                'Sustainability',
                'Customer Excellence',
                'Operational Efficiency',
                'Talent Development'
            ],
            'Budget ($M)': [2.5, 15.0, 1.2, 8.0, 0.5],
            'Progress': ['60%', '25%', '80%', '40%', '70%'],
            'Due Date': ['Q2 2025', 'Q4 2028', 'Q1 2025', 'Q3 2025', 'Q4 2025']
        }
        df_initiatives = pd.DataFrame(initiatives_data)

        # Sheet 3: Quarterly Performance
        quarterly_data = {
            'Quarter': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
            'Revenue ($M)': [125, 132, 128, 145],
            'EBITDA ($M)': [22, 24, 21, 26],
            'NPS': [62, 64, 63, 65],
            'Deliveries (000s)': [450, 475, 460, 520]
        }
        df_quarterly = pd.DataFrame(quarterly_data)

        # Write to Excel with multiple sheets
        with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
            df_kpi.to_excel(writer, sheet_name='KPI Tracker', index=False)
            df_initiatives.to_excel(writer, sheet_name='Strategic Initiatives', index=False)
            df_quarterly.to_excel(writer, sheet_name='Quarterly Performance', index=False)

        return str(output_path)

    except ImportError:
        raise ImportError("pandas and openpyxl required to create XLSX fixtures")


def create_mock_pptx(output_path: str = None) -> str:
    """
    Create a mock strategy presentation PPTX document.
    """
    if output_path is None:
        output_path = FIXTURES_DIR / "mock_strategy_presentation.pptx"

    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()

        # Slide 1: Title
        slide_layout = prs.slide_layouts[0]  # Title slide
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        title.text = "Strategic Plan 2025-2030"
        subtitle.text = "Building a Sustainable Future"

        # Slide 2: Vision
        slide_layout = prs.slide_layouts[1]  # Title and content
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        body = slide.placeholders[1]
        title.text = "Our Vision"
        tf = body.text_frame
        tf.text = "To be the leading sustainable logistics provider in Asia-Pacific by 2030"

        # Slide 3: Strategic Priorities
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        body = slide.placeholders[1]
        title.text = "Strategic Priorities"
        tf = body.text_frame
        tf.text = "Digital Transformation"
        p = tf.add_paragraph()
        p.text = "Sustainability Leadership"
        p = tf.add_paragraph()
        p.text = "Customer Excellence"
        p = tf.add_paragraph()
        p.text = "Operational Efficiency"
        p = tf.add_paragraph()
        p.text = "Talent Development"

        # Slide 4: Key Metrics
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        body = slide.placeholders[1]
        title.text = "Key Success Metrics"
        tf = body.text_frame
        tf.text = "Revenue Growth: 12% CAGR"
        p = tf.add_paragraph()
        p.text = "Customer NPS: > 70"
        p = tf.add_paragraph()
        p.text = "Carbon Neutral by 2028"
        p = tf.add_paragraph()
        p.text = "Employee Engagement: > 80%"

        prs.save(str(output_path))
        return str(output_path)

    except ImportError:
        raise ImportError("python-pptx required to create PPTX fixtures")


def create_all_fixtures() -> dict:
    """
    Create all mock fixtures for testing.

    Returns:
        Dictionary with fixture paths
    """
    fixtures = {}
    errors = []

    try:
        fixtures['pdf_strategy'] = create_mock_pdf()
        print(f"Created: {fixtures['pdf_strategy']}")
    except Exception as e:
        errors.append(f"PDF: {e}")

    try:
        fixtures['docx_goals'] = create_mock_docx()
        print(f"Created: {fixtures['docx_goals']}")
    except Exception as e:
        errors.append(f"DOCX: {e}")

    try:
        fixtures['xlsx_kpis'] = create_mock_xlsx()
        print(f"Created: {fixtures['xlsx_kpis']}")
    except Exception as e:
        errors.append(f"XLSX: {e}")

    try:
        fixtures['pptx_strategy'] = create_mock_pptx()
        print(f"Created: {fixtures['pptx_strategy']}")
    except Exception as e:
        errors.append(f"PPTX: {e}")

    if errors:
        print(f"Errors creating fixtures: {errors}")

    return fixtures


if __name__ == '__main__':
    print("Creating test fixtures...")
    create_all_fixtures()
    print("Done!")
