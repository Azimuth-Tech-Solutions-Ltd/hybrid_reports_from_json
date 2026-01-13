"""
Standalone Neighbourhood & Location Overview PDF Generator
Based on the working azimuth_report_pipeline.py implementation
"""

import json
import os
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

# Import the reflection engine
from report_engine.sections.neighbourhood_reflector import NeighbourhoodReflector

class NeighbourhoodPDFGenerator:
    def __init__(self, enrichment_data, output_path):
        self.data = enrichment_data
        self.output_path = output_path
        self.AZ_BLUE = colors.HexColor("#003366")
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.narrative = NeighbourhoodReflector(enrichment_data).narrative

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='AZ_Body',
            parent=self.styles['Normal'],
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=14,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Header',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=self.AZ_BLUE,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Section',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.AZ_BLUE,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            keepWithNext=True
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Caption',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def _get_img(self, url):
        if not url or url == "null":
            return None
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                img = Image(BytesIO(res.content))
                return img
            return None
        except:
            return None

    def build(self):
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        elements = []

        # Section title only (no header)
        elements.append(Paragraph("3. Neighbourhood and Location Overview", self.styles['AZ_Header']))
        elements.append(Spacer(1, 0.2*inch))

        # Render narrative as separate paragraphs
        if 'paragraphs' in self.narrative:
            paragraphs = self.narrative['paragraphs']
            
            # Render first paragraph (location overview)
            if len(paragraphs) > 0:
                elements.append(Paragraph(paragraphs[0], self.styles['AZ_Body']))
                elements.append(Spacer(1, 0.15*inch))
            
            # Transportation paragraph with table
            if len(paragraphs) > 1:
                elements.append(Paragraph(paragraphs[1], self.styles['AZ_Body']))
                elements.append(Spacer(1, 0.1*inch))
                
                # Create transportation table (without distance column)
                if 'transport_data' in self.narrative and self.narrative['transport_data']:
                    transport_table_data = [["Station Name", "Type"]]
                    for station in self.narrative['transport_data'][:8]:  # Top 8 stations
                        name = station.get('name', '')
                        station_type = station.get('type', '').replace('_', ' ').title()
                        if name:
                            transport_table_data.append([name, station_type])
                    
                    if len(transport_table_data) > 1:  # Has data beyond header
                        transport_table = Table(transport_table_data, colWidths=[4.5*inch, 1.5*inch])
                        transport_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), self.AZ_BLUE),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('TOPPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(transport_table)
                        elements.append(Spacer(1, 0.15*inch))
                
                # Add roadmap image after transport section
                roadmap = self._get_img(self.data.get('visuals', {}).get('roadmap_url'))
                if roadmap:
                    roadmap.drawWidth = 5.2*inch
                    roadmap.drawHeight = 2.8*inch
                    elements.append(roadmap)
                    elements.append(Paragraph("Figure 3.1: Neighbourhood Connectivity Context", self.styles['AZ_Caption']))
                    elements.append(Spacer(1, 0.15*inch))
            
            # Remaining paragraphs (amenities, education, safety, environment, market)
            for para in paragraphs[2:]:
                elements.append(Paragraph(para, self.styles['AZ_Body']))
                elements.append(Spacer(1, 0.15*inch))
            
            # Add satellite image after amenities section (around paragraph 3)
            if len(paragraphs) > 3:
                sat = self._get_img(self.data.get('visuals', {}).get('satellite_map_url'))
                if sat:
                    sat.drawWidth = 5.2*inch
                    sat.drawHeight = 2.8*inch
                    elements.append(sat)
                    elements.append(Paragraph("Figure 3.2: Neighbourhood Aerial Context", self.styles['AZ_Caption']))
                    elements.append(Spacer(1, 0.15*inch))

        elements.append(Spacer(1, 0.5*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Paragraph(
            "© 2026 Azimuth Tech Solutions | Institutional Property Intelligence",
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                alignment=TA_CENTER,
                fontSize=7,
                textColor=colors.grey,
                spaceBefore=5
            )
        ))

        doc.build(elements)
        return self.output_path

def generate_neighbourhood_pdf(property_data, enrichment_data, output_path):
    """Generate neighbourhood PDF from enrichment data"""
    generator = NeighbourhoodPDFGenerator(enrichment_data, output_path)
    return generator.build()

