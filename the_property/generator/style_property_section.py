import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

# Azimuth Branding Colors
AZIMUTH_BLUE = colors.HexColor('#003366')
AZIMUTH_ACCENT = colors.HexColor('#E5EDF5')

def create_styled_pdf(md_input_path, pdf_output_path, title):
    doc = SimpleDocTemplate(
        pdf_output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(
        name='AZ_Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=AZIMUTH_BLUE,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='AZ_Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=AZIMUTH_BLUE,
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderPadding=(2, 0, 5, 0),
        borderWidth=0,
        borderColor=AZIMUTH_BLUE
    ))

    styles.add(ParagraphStyle(
        name='AZ_Body',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName='Helvetica',
        hyphenation=True
    ))

    story = []

    # Title
    story.append(Paragraph(f"Azimuth Premium Valuation: {title}", styles['AZ_Title']))
    story.append(HRFlowable(width="100%", thickness=2, color=AZIMUTH_BLUE, spaceBefore=0, spaceAfter=20))

    if not os.path.exists(md_input_path):
        story.append(Paragraph(f"Error: Markdown file not found at {md_input_path}", styles['AZ_Body']))
    else:
        with open(md_input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                # We skip the main title as we added a custom one
                continue
            elif line.startswith('## '):
                header_text = line.replace('## ', '')
                story.append(Paragraph(header_text, styles['AZ_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=10))
            elif line.startswith('### '):
                header_text = line.replace('### ', '')
                story.append(Paragraph(header_text, styles['AZ_Header']))
            else:
                story.append(Paragraph(line, styles['AZ_Body']))

    doc.build(story)
    print(f"Success: PDF generated at {pdf_output_path}")

if __name__ == "__main__":
    # Version 1: LLM Deep
    create_styled_pdf(
        'the_property/outputs/the_property_section.md',
        'the_property/outputs/V1_Gemini_Deep_Report.pdf',
        "Version 1 (AI Deep Analysis)"
    )
    
    # Version 2: Reflection Deep
    create_styled_pdf(
        'the_property/outputs/the_property_section_v2_reflection.md',
        'the_property/outputs/V2_Reflection_Deep_Report.pdf',
        "Version 2 (Reflection Engine)"
    )
