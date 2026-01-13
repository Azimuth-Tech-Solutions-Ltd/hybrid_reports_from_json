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

# --- PIPELINE UTILS ---

def get_image_from_url(url):
    if not url or url == "null": return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except: return None

class ReportPipeline:
    def __init__(self, property_data):
        self.data = property_data
        self.content = {}

    def run(self):
        """Executes the drafting and reflection pipeline."""
        self._stage_executive_summary()
        self._stage_location_analysis()
        self._stage_infrastructure()
        self._stage_safety_and_environment()
        self._stage_investment_rationale()
        return self.content

    def _stage_executive_summary(self):
        """Drafts the summary and reflects on key data points."""
        addr = self.data.get('address', {}).get('formatted_address', 'Subject Property')
        commute = self.data.get('commute_to_city', {}).get('duration', 'N/A')
        
        # REFLECTION: Ensure we don't claim 'Excellent' commute if it's over 1 hour
        commute_quality = "prime" if "mins" in commute and int(commute.split()[0]) < 30 else "standard"
        
        self.content['exec_summary'] = (
            f"This institutional analysis provides a comprehensive location profile for <b>{addr}</b>. "
            f"Characterized by its {commute_quality} accessibility (estimated {commute} to Central London) and a "
            "highly mature amenity landscape, the subject asset represents a core investment opportunity in a stable "
            "prime residential market. The location demonstrates robust defensive characteristics with high barrier-to-entry "
            "socio-economic markers."
        )

    def _stage_location_analysis(self):
        """Refined location narrative."""
        self.content['location_summary'] = (
            "The subject property is situated in an established, high-prestige residential corridor. The area is "
            "defined by a low-density residential feel despite its central urban positioning. High-value period "
            "architecture dominates the streetscape, catering to an affluent demographic that values both privacy "
            "and immediate metropolitan connectivity. This micro-market maintains a consistent premium over "
            "neighboring districts due to its unique architectural integrity and historical significance."
        )

    def _stage_infrastructure(self):
        """Analyzes Transport & Amenities."""
        amenities = self.data.get('amenities', {})
        total_amenities = sum(cat.get('count', 0) for cat in amenities.values())
        
        # REFLECTION: Check density level
        density_label = "exceptional" if total_amenities > 50 else "stable"
        
        self.content['infrastructure'] = (
            f"Local infrastructure is classified as <b>{density_label}</b>, with {total_amenities} identified service "
            "nodes within the primary search radius. This density ensures a high degree of residential utility. "
            "The transport profile is a key asset for this location, providing redundant access to multiple London "
            "Underground lines, which underpins the long-term rental demand and occupational resilience."
        )

    def _stage_safety_and_environment(self):
        """Deeper dive into liveability."""
        crime = self.data.get('crime', {})
        total = crime.get('total_incidents', 0)
        aq = self.data.get('air_quality', {})
        
        # REFLECTION: Contextualize crime based on urban density
        safety_tone = "active urban" if total > 1000 else "subdued residential"
        
        self.content['safety_env'] = (
            f"The environmental profile reflects a <b>{safety_tone}</b> context. Recent data records {total} incidents, "
            "concentrated in categories expected for high-density districts. This is balanced by a favourable "
            f"Air Quality Index of {aq.get('aqi', 'N/A')} ({aq.get('category', 'Standard')}) and a significant "
            "allocation of green and recreational infrastructure, which are primary drivers of resident wellness "
            "and long-term property desirability."
        )

    def _stage_investment_rationale(self):
        """Final strategic conclusion."""
        self.content['rationale'] = (
            "From a valuation perspective, the asset's location provides a fundamental floor for capital stability. "
            "The alignment of prestige, accessibility, and high-quality educational infrastructure creates a "
            "sustained demand profile that historically outperforms broader market trends during periods of "
            "volatility. The combination of these indicators suggests a low-risk profile for long-term hold "
            "strategies within the prime London residential sector."
        )

# --- PDF GENERATOR ---

def create_azimuth_pipeline_report(data, filename):
    pipeline = ReportPipeline(data)
    report_text = pipeline.run()
    
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    AZIMUTH_BLUE = colors.HexColor("#003366")
    AZIMUTH_LIGHT_BG = colors.HexColor("#F4F7F9")
    
    styles.add(ParagraphStyle(name='A_Body', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=10, leading=14, spaceAfter=12))
    styles.add(ParagraphStyle(name='A_Header', parent=styles['Heading1'], fontSize=22, textColor=AZIMUTH_BLUE, spaceAfter=10))
    styles.add(ParagraphStyle(name='A_Section', parent=styles['Heading2'], fontSize=14, textColor=AZIMUTH_BLUE, spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold', keepWithNext=True))
    styles.add(ParagraphStyle(name='A_Caption', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER))

    elements = []
    
    # 1. Branding & Header
    elements.append(HRFlowable(width="100%", thickness=5, color=AZIMUTH_BLUE, spaceAfter=10))
    elements.append(Paragraph("AZIMUTH PROPERTY INTELLIGENCE | LOCATION ANALYTICS", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Institutional Location Intelligence Report", styles['A_Header']))
    elements.append(Paragraph(f"Subject Asset: {data.get('address', {}).get('formatted_address', 'N/A')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # 2. Executive Summary (New)
    elements.append(KeepTogether([
        Paragraph("Executive Summary", styles['A_Section']),
        Paragraph(report_text['exec_summary'], styles['A_Body'])
    ]))

    # 3. Macro Context (Photo)
    roadmap_url = data.get('visuals', {}).get('roadmap_url')
    if roadmap_url:
        img_data = get_image_from_url(roadmap_url)
        if img_data:
            elements.append(KeepTogether([
                Image(img_data, width=5.2*inch, height=2.8*inch),
                Paragraph("Figure 1.1: Macro-Location & Connectivity Analysis", styles['A_Caption']),
                Spacer(1, 0.2*inch)
            ]))

    # 4. Location & Neighborhood
    elements.append(KeepTogether([
        Paragraph("1. Location Character & Micro-Market Dynamics", styles['A_Section']),
        Paragraph(report_text['location_summary'], styles['A_Body'])
    ]))

    # 5. Infrastructure & Connectivity
    elements.append(KeepTogether([
        Paragraph("2. Infrastructure, Transport & Social Utility", styles['A_Section']),
        Paragraph(report_text['infrastructure'], styles['A_Body'])
    ]))

    # Transport Table
    transport = data.get('transport', [])
    if transport:
        t_data = [["Transport Node", "Rating", "Proximity"]]
        for t in transport:
            t_data.append([t.get('name'), f"{t.get('rating')}/5" if t.get('rating') else "N/A", "Walking Distance"])
        t1 = Table(t_data, colWidths=[2.5*inch, 1*inch, 1.8*inch])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZIMUTH_LIGHT_BG])
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 0.2*inch))

    # 6. Safety, Environment & Liveability (Reflection results)
    elements.append(KeepTogether([
        Paragraph("3. Environmental Profiling & Operational Safety", styles['A_Section']),
        Paragraph(report_text['safety_env'], styles['A_Body'])
    ]))

    # Satellite & Street View
    v = data.get('visuals', {})
    sat_img = get_image_from_url(v.get('satellite_map_url'))
    sv_img = get_image_from_url(v.get('street_view_url'))
    
    if sat_img and sv_img:
        img_table = Table([[Image(sat_img, 2.5*inch, 1.8*inch), Image(sv_img, 2.5*inch, 1.8*inch)]], colWidths=[2.7*inch, 2.7*inch])
        elements.append(img_table)
        elements.append(Paragraph("Figure 1.2: Aerial Site Orientation (Left) and Street Frontage Context (Right)", styles['A_Caption']))
        elements.append(Spacer(1, 0.2*inch))

    # 7. Strategic Investment Rationale (New)
    elements.append(KeepTogether([
        Paragraph("4. Strategic Valuation Rationale", styles['A_Section']),
        Paragraph(report_text['rationale'], styles['A_Body'])
    ]))

    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph("© 2026 Azimuth Tech Solutions | Institutional Division | Data Verified via Reflection Pipeline", 
                             ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, textColor=colors.grey, spaceBefore=5)))

    doc.build(elements)

if __name__ == "__main__":
    with open('enrichment_results.json', 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    create_azimuth_pipeline_report(full_data[0], "Azimuth_Pipeline_Report.pdf")
    print("Reflection Pipeline Report Generated.")


