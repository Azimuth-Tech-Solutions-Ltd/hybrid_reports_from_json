import os
import json
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

# Azimuth Branding Colors
AZIMUTH_BLUE = colors.HexColor('#003366')

def generate_cover_page(property_data: dict, enrichment_data: dict, output_path: str):
    """Generate cover page with property photo, address, and Azimuth branding"""
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='CoverTitle',
        parent=styles['Normal'],
        fontSize=28,
        textColor=AZIMUTH_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=30
    )
    
    address_style = ParagraphStyle(
        name='CoverAddress',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=20,
        leading=24
    )
    
    logo_style = ParagraphStyle(
        name='CoverLogo',
        parent=styles['Normal'],
        fontSize=32,
        textColor=AZIMUTH_BLUE,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        spaceAfter=40
    )
    
    elements = []
    
    # Azimuth Logo/Title (top left)
    elements.append(Paragraph("AZIMUTH", logo_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Property Address (centered, large)
    paon = property_data.get('paon', '')
    saon = property_data.get('saon', '')
    street = property_data.get('street', '')
    postcode = property_data.get('postcode', '')
    
    # Format address
    address_parts = []
    if saon:
        address_parts.append(saon)
    if paon:
        address_parts.append(paon)
    if street:
        address_parts.append(street)
    if postcode:
        address_parts.append(postcode)
    
    full_address = ", ".join(address_parts)
    
    # Address in multiple lines for better display
    address_lines = []
    if paon and street:
        address_lines.append(f"{paon} {street}")
    if postcode:
        address_lines.append(postcode)
    if not address_lines:
        address_lines.append(full_address)
    
    for line in address_lines:
        elements.append(Paragraph(line.upper(), address_style))
    
    elements.append(Spacer(1, 0.8*inch))
    
    # Property Image
    image_url = None
    if enrichment_data:
        visuals = enrichment_data.get('visuals', {})
        # Prefer street view, then satellite
        image_url = visuals.get('street_view_url') or visuals.get('satellite_map_url')
    
    if image_url:
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            img = Image(BytesIO(response.content))
            # Make image large but fit on page
            img.drawWidth = 5.5*inch
            img.drawHeight = 4*inch
            elements.append(img)
        except Exception as e:
            print(f"Warning: Could not load cover image: {e}")
    
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer text
    footer_style = ParagraphStyle(
        name='CoverFooter',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    elements.append(Paragraph("INSTITUTIONAL VALUATION REPORT", footer_style))
    
    doc.build(elements)
    return output_path

