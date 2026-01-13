import json
import os
import sys
import requests
import re
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

# --- 1. VALUATION MATH ENGINE (For Section 4) ---

def calculate_dispersion(comparables):
    """Calculates the similarity-weighted CV and dispersion score."""
    valid_comps = []
    for c in comparables:
        price, size, sim = c.get('price', 0), c.get('total_size_sqm', 0), c.get('similarity_score', 0)
        if size > 10 and price > 0 and sim > 0:
            valid_comps.append({'ppsqm': price/size, 'sim': sim})
    
    if not valid_comps: return None
    
    total_sim = sum(c['sim'] for c in valid_comps)
    w_mean = sum((c['sim']/total_sim) * c['ppsqm'] for c in valid_comps)
    w_var = sum((c['sim']/total_sim) * ((c['ppsqm'] - w_mean)**2) for c in valid_comps)
    cv = math.sqrt(w_var) / w_mean if w_mean > 0 else 0
    
    score = math.exp(-6.0 * cv)
    if cv > 0.35: score *= 0.6
    if cv > 0.50: score *= 0.4
    return {"cv": cv, "score": max(0, min(1, score)), "mean": w_mean, "count": len(valid_comps)}

# --- 2. DATA REFLECTION ENGINE ---

class AzimuthReflector:
    def __init__(self, data):
        self.data = data
        self.narrative = {}
        self._reflect()

    def _reflect(self):
        addr = self.data.get('address', {}).get('formatted_address', self.data.get('input_address', 'N/A'))
        
        # 1. Location
        self.narrative['location'] = (
            f"The subject asset at <b>{addr}</b> is situated in a high-prestige residential enclave. "
            "The micro-location is defined by mature architectural elegance and high-value period properties, "
            "offering a rare balance of residential seclusion and central London accessibility."
        )

        # 2. Transport
        dur = self.data.get('commute_to_city', {}).get('duration', 'N/A')
        self.narrative['transport'] = (
            "The property benefits from an exceptional accessibility profile. Strategic proximity to "
            "multiple Underground stations facilities seamless travel, providing a commute of approximately "
            f"<b>{dur}</b> to the traditional center. This is a primary driver of occupational demand."
        )

        # 3. Amenities
        total_amenities = sum(cat.get('count', 0) for cat in self.data.get('amenities', {}).values())
        self.narrative['amenities'] = (
            f"The locality boasts a dense social infrastructure with <b>{total_amenities}</b> identified amenity nodes. "
            "The concentration of luxury dining and wellness facilities serves as a powerful anchor for property value."
        )

        # 4. COMPARABLE CONSISTENCY (The New Section 4)
        comps = self.data.get('comparables', [])
        disp = calculate_dispersion(comps)
        if disp:
            tone = "high" if disp['score'] > 0.8 else "moderate" if disp['score'] > 0.5 else "low"
            self.narrative['comparables'] = (
                f"Valuation analysis identifies a <b>{tone} degree of price consistency</b> across similarity-weighted comparables. "
                f"The weighted Coefficient of Variation (CV) is <b>{disp['cv']:.2f}</b>, resulting in a dispersion-adjusted "
                f"quality score of <b>{disp['score']:.2f}</b>. This indicates a {tone} level of market agreement on the "
                f"PPSQM basis (Mean: £{disp['mean']:,.2f}), providing a robust foundation for the primary valuation estimate."
            )
        else:
            self.narrative['comparables'] = "Direct comparable PPSQM dispersion data is currently restricted or insufficient for weighted analysis."

        # 5. Education
        self.narrative['education'] = "The area is served by an elite educational network, sustaining strong family-oriented demand."

        # 6. Crime & Safety
        crime_total = self.data.get('crime', {}).get('total_incidents', 0)
        self.narrative['crime'] = (
            f"Localized safety data records <b>{crime_total}</b> incidents, a figure consistent with high-density "
            "Central London intersections. This context is monitored to ensure alignment with institutional standards."
        )

        # 7. Environment
        aq = self.data.get('air_quality', {})
        self.narrative['environment'] = (
            f"Environmental indicators are stable, with an Air Quality Index of <b>{aq.get('aqi', 'N/A')}</b>. "
            "The abundance of local green infrastructure provides a significant environmental premium."
        )

        # 8. Rationale
        self.narrative['rationale'] = (
            "In conclusion, the asset's value is anchored by its location quality. The synergy of prestige, "
            "connectivity, and infrastructure forms a robust defensive profile against market volatility."
        )

# --- 3. PREMIUM PDF GENERATOR ---

class AzimuthPDFGenerator:
    def __init__(self, data, narrative, output_path):
        self.data, self.narrative, self.output_path = data, narrative, output_path
        self.AZ_BLUE = colors.HexColor("#003366")
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(name='AZ_Body', parent=self.styles['Normal'], alignment=TA_JUSTIFY, fontSize=10, leading=14, spaceAfter=12))
        self.styles.add(ParagraphStyle(name='AZ_Header', parent=self.styles['Heading1'], fontSize=22, textColor=self.AZ_BLUE, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='AZ_Section', parent=self.styles['Heading2'], fontSize=14, textColor=self.AZ_BLUE, spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold', keepWithNext=True))
        self.styles.add(ParagraphStyle(name='AZ_Caption', parent=self.styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER))

    def _get_img(self, url):
        if not url or url == "null": return None
        try:
            res = requests.get(url, timeout=10)
            return Image(BytesIO(res.content)) if res.status_code == 200 else None
        except: return None

    def build(self):
        doc = SimpleDocTemplate(self.output_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        elements = []

        # Header
        elements.append(HRFlowable(width="100%", thickness=5, color=self.AZ_BLUE, spaceAfter=10))
        elements.append(Paragraph("AZIMUTH PROPERTY ANALYTICS | INSTITUTIONAL REPORT", self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Institutional Location Intelligence", self.styles['AZ_Header']))
        elements.append(Spacer(1, 0.2*inch))

        # Sections 1-3
        elements.append(KeepTogether([Paragraph("1. Location Summary", self.styles['AZ_Section']), Paragraph(self.narrative['location'], self.styles['AZ_Body'])]))
        
        roadmap = self._get_img(self.data.get('visuals', {}).get('roadmap_url'))
        if roadmap:
            roadmap.drawWidth=5.2*inch; roadmap.drawHeight=2.8*inch
            elements.append(KeepTogether([Paragraph("2. Transport & Connectivity", self.styles['AZ_Section']), Paragraph(self.narrative['transport'], self.styles['AZ_Body']), roadmap, Paragraph("Fig 1.1: Connectivity Context", self.styles['AZ_Caption'])]))
        
        sat = self._get_img(self.data.get('visuals', {}).get('satellite_map_url'))
        if sat:
            sat.drawWidth=2.8*inch; sat.drawHeight=2*inch
            elements.append(KeepTogether([Paragraph("3. Local Social Infrastructure", self.styles['AZ_Section']), Table([[sat, Paragraph(self.narrative['amenities'], self.styles['AZ_Body'])]], colWidths=[3*inch, 2.5*inch])]))

        # SECTION 4: COMPARABLE ANALYSIS
        elements.append(KeepTogether([
            Paragraph("4. Valuation Quality & Comparable Consistency", self.styles['AZ_Section']),
            Paragraph(self.narrative['comparables'], self.styles['AZ_Body'])
        ]))

        # Sections 5-8
        elements.append(KeepTogether([Paragraph("5. Education", self.styles['AZ_Section']), Paragraph(self.narrative['education'], self.styles['AZ_Body'])]))
        
        sv = self._get_img(self.data.get('visuals', {}).get('street_view_url'))
        if sv:
            sv.drawWidth=5.2*inch; sv.drawHeight=2.8*inch
            elements.append(KeepTogether([Paragraph("6. Crime & Safety", self.styles['AZ_Section']), Paragraph(self.narrative['crime'], self.styles['AZ_Body']), sv, Paragraph("Fig 1.2: Street Frontage", self.styles['AZ_Caption'])]))

        elements.append(KeepTogether([Paragraph("7. Environmental Liveability", self.styles['AZ_Section']), Paragraph(self.narrative['environment'], self.styles['AZ_Body'])]))
        elements.append(KeepTogether([Paragraph("8. Strategic Rationale", self.styles['AZ_Section']), Paragraph(self.narrative['rationale'], self.styles['AZ_Body'])]))

        elements.append(Spacer(1, 0.5*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Paragraph("© 2026 Azimuth Tech Solutions | Institutional Property Intelligence", 
                                 ParagraphStyle(name='F', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=7, textColor=colors.grey, spaceBefore=5)))

        doc.build(elements)

# --- 4. RUNNER ---

if __name__ == "__main__":
    with open('enrichment_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)[0]
    
    # MOCK COMP DATA FOR TESTING SECTION 4
    data['comparables'] = [
        {"price": 500000, "total_size_sqm": 50, "similarity_score": 0.95},
        {"price": 510000, "total_size_sqm": 52, "similarity_score": 0.90},
        {"price": 480000, "total_size_sqm": 48, "similarity_score": 0.85}
    ]
    
    AzimuthPDFGenerator(data, AzimuthReflector(data).narrative, "Azimuth_Consolidated_Report.pdf").build()
    print("Success: Integrated report with Section 4 generated.")
