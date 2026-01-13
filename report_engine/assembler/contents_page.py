import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

# Azimuth Branding Colors
AZIMUTH_BLUE = colors.HexColor('#003366')

def generate_contents_page(sections: list, section_pdfs: dict, output_path: str):
    """Generate contents page listing all sections with actual page numbers"""
    from PyPDF2 import PdfReader
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='ContentsTitle',
        parent=styles['Normal'],
        fontSize=24,
        textColor=AZIMUTH_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=30
    )
    
    section_style = ParagraphStyle(
        name='ContentsSection',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica',
        spaceAfter=12,
        leftIndent=20
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("CONTENTS", title_style))
    elements.append(HRFlowable(width="30%", thickness=2, color=AZIMUTH_BLUE, hAlign='CENTER', spaceAfter=30))
    elements.append(Spacer(1, 0.3*inch))
    
    # Section mapping (section name to display name)
    section_names = {
        'instructions': '1. Instructions',
        'property_overview': '2. The Property',
        'neighbourhood_overview': '3. Neighbourhood and Location Overview',
        'market_commentary': '4. Market Commentary',
        'valuation_methodology': '5. Valuation Methodology and Comparable Evidence',
        'location_analysis': '6. Location Analysis',
        'infrastructure': '7. Infrastructure',
        'safety': '8. Safety',
        'valuation_quality': '9. Valuation Quality'
    }
    
    # Calculate page numbers
    page_num = 3  # Start after cover (page 1) and contents (page 2)
    for section in sections:
        if section in section_pdfs:
            # Get actual page count from PDF
            try:
                reader = PdfReader(section_pdfs[section])
                num_pages = len(reader.pages)
            except:
                num_pages = 1  # Default to 1 if can't read
            
            display_name = section_names.get(section, section.replace('_', ' ').title())
            elements.append(Paragraph(f"{display_name} ................. {page_num}", section_style))
            page_num += num_pages
    
    doc.build(elements)
    return output_path

