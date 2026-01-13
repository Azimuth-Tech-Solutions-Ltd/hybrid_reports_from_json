import json
import os
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

def get_image_from_url(url):
    """Downloads an image from a URL and returns a BytesIO object."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def create_enhanced_report_pdf(json_data, filename):
    data = json_data[0]  # Focus on the first property as requested
    
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # AZIMUTH BRAND COLORS
    AZIMUTH_BLUE = colors.HexColor("#004A99")
    AZIMUTH_LIGHT_BLUE = colors.HexColor("#E6F2FF")
    
    # CUSTOM STYLES
    styles.add(ParagraphStyle(
        name='Justify', 
        parent=styles['Normal'], 
        alignment=TA_JUSTIFY, 
        fontSize=10, 
        leading=14,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='AzimuthTitle', 
        parent=styles['Heading1'], 
        alignment=TA_CENTER, 
        fontSize=24, 
        textColor=AZIMUTH_BLUE,
        spaceAfter=30,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='AzimuthSubHeader', 
        parent=styles['Heading2'], 
        fontSize=14, 
        textColor=AZIMUTH_BLUE,
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        keepWithNext=True  # CRITICAL: Prevents header orphans
    ))

    styles.add(ParagraphStyle(
        name='AzimuthSmallHeader', 
        parent=styles['Heading3'], 
        fontSize=11, 
        textColor=AZIMUTH_BLUE,
        spaceBefore=10,
        spaceAfter=5,
        fontName='Helvetica-Bold',
        keepWithNext=True
    ))
    
    body_style = styles["Justify"]
    
    elements = []
    
    # --- HEADER SECTION ---
    elements.append(Paragraph("Neighbourhood & Location Overview", styles['AzimuthTitle']))
    elements.append(HRFlowable(width="100%", thickness=2, color=AZIMUTH_BLUE, spaceAfter=20))
    
    # --- 1. LOCATION SUMMARY ---
    addr = data.get('address', {})
    formatted_addr = addr.get('formatted_address', data.get('input_address', 'N/A'))
    
    elements.append(Paragraph("Location Summary", styles['AzimuthSubHeader']))
    summary_text = (
        f"The subject property is located at <b>{formatted_addr}</b>. "
        "Situated in one of London's most prestigious residential districts, the area is characterized by "
        "its historical significance and architectural elegance. Campden Hill is known for its quiet, tree-lined streets "
        "and proximity to high-end amenities. The urban character is a sophisticated blend of prime residential tranquility "
        "and central London vibrancy, offering an unparalleled living experience."
    )
    elements.append(Paragraph(summary_text, body_style))
    
    # ROADMAP IMAGE (Top Context)
    visuals = data.get('visuals', {})
    roadmap_url = visuals.get('roadmap_url')
    if roadmap_url:
        img_data = get_image_from_url(roadmap_url)
        if img_data:
            img = Image(img_data, width=5.5*inch, height=3*inch)
            elements.append(KeepTogether([
                Paragraph("<b>Area Roadmap</b>", styles['AzimuthSmallHeader']),
                img,
                Spacer(1, 0.2*inch)
            ]))

    # --- 2. ACCESSIBILITY & CONNECTIVITY ---
    transport = data.get('transport', [])
    if transport:
        elements.append(Paragraph("Accessibility & Connectivity", styles['AzimuthSubHeader']))
        elements.append(Paragraph(
            "The property enjoys superior connectivity to the London transit network. "
            "Strategic access to multiple Underground lines facilitates seamless travel to key commercial and cultural hubs.", body_style))
        
        transport_rows = [["Transport Node", "Rating", "Status"]]
        for t in transport:
            rating = t.get('rating', 'N/A')
            status = "Walking distance (approx.)"
            dist = t.get('distance_estimate_m')
            if dist is not None:
                status = f"{dist}m approx."
            transport_rows.append([t.get('name', 'N/A'), str(rating), status])
            
        t1 = Table(transport_rows, colWidths=[2.5*inch, 1*inch, 2*inch])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZIMUTH_LIGHT_BLUE])
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 0.2 * inch))

    # --- 3. LOCAL AMENITIES ---
    amenities = data.get('amenities', {})
    if amenities:
        elements.append(Paragraph("Local Amenities", styles['AzimuthSubHeader']))
        
        # SATELLITE IMAGE (Integrated with amenities)
        sat_url = visuals.get('satellite_map_url')
        if sat_url:
            img_data = get_image_from_url(sat_url)
            if img_data:
                img = Image(img_data, width=3*inch, height=2.2*inch)
                
                amenities_summary = []
                total_count = 0
                for cat_name, cat_data in amenities.items():
                    count = cat_data.get('count', 0)
                    total_count += count
                    top_pick = cat_data.get('top_pick')
                    name = top_pick.get('name', 'N/A') if top_pick else 'N/A'
                    amenities_summary.append(Paragraph(f"<b>{cat_name.capitalize()}:</b> {count} found (Top: {name})", styles['Normal']))
                
                # Table to put text next to satellite image
                data_side = [
                    [img, [Paragraph("<b>Satellite Context</b>", styles['AzimuthSmallHeader'])] + amenities_summary]
                ]
                t_side = Table(data_side, colWidths=[3.2*inch, 2.5*inch])
                t_side.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
                elements.append(t_side)
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph(
                    f"The locality boasts a rich density of <b>{total_count}</b> identified amenities, "
                    "underscoring a highly mature residential environment. The high concentration of quality "
                    "establishments within immediate reach is a hallmark of this prestigious district.", body_style))
        
    # --- 4. EDUCATION ---
    schools = data.get('schools', [])
    if schools:
        elements.append(Paragraph("Education", styles['AzimuthSubHeader']))
        school_text = "The area is exceptionally well-served by premium educational institutions, reflecting its family-oriented character. "
        notable_schools = [s.get('name') for s in schools[:3] if s.get('name')]
        if notable_schools:
            school_text += f"Notable nearby facilities include {', '.join(notable_schools)}. "
        school_text += "High performance ratings across these institutions confirm a robust educational infrastructure."
        elements.append(Paragraph(school_text, body_style))

    # --- 5. ENVIRONMENTAL & LIVEABILITY ---
    elements.append(Paragraph("Environmental & Liveability Factors", styles['AzimuthSubHeader']))
    
    # CRIME (Keep Together to avoid orphans)
    crime = data.get('crime', {})
    if crime:
        total_crime = crime.get('total_incidents', 0)
        top_cats = crime.get('top_categories', [])
        crime_desc = f"Recent data indicates <b>{total_crime}</b> recorded incidents in the vicinity. "
        if top_cats:
            cat_list = [f"{c[0].replace('-', ' ')} ({c[1]})" for c in top_cats]
            crime_desc += f"Primary categories: {', '.join(cat_list)}. "
        
        elements.append(KeepTogether([
            Paragraph("Crime & Safety", styles['AzimuthSmallHeader']),
            Paragraph(crime_desc, body_style)
        ]))

    # AIR QUALITY & GREEN SPACES
    aq = data.get('air_quality', {})
    if aq:
        aqi = aq.get('aqi', 'N/A')
        cat = aq.get('category', 'N/A')
        elements.append(KeepTogether([
            Paragraph("Air Quality", styles['AzimuthSmallHeader']),
            Paragraph(f"Air Quality Index (AQI) is <b>{aqi}</b> ({cat}).", body_style)
        ]))

    # STREET VIEW IMAGE
    sv_url = visuals.get('street_view_url')
    if sv_url:
        img_data = get_image_from_url(sv_url)
        if img_data:
            img = Image(img_data, width=5.5*inch, height=3*inch)
            elements.append(KeepTogether([
                Paragraph("<b>Street Frontage Context</b>", styles['AzimuthSmallHeader']),
                img,
                Spacer(1, 0.2*inch)
            ]))

    # --- 6. COMMUTE & SUSTAINABILITY ---
    commute = data.get('commute_to_city', {})
    solar = data.get('solar', {})
    
    if commute or solar:
        elements.append(Paragraph("Connectivity & Sustainability", styles['AzimuthSubHeader']))
        
        cs_text = ""
        if commute:
            dist = commute.get('distance', 'N/A')
            dur = commute.get('duration', 'N/A')
            cs_text += f"The property is <b>{dist}</b> from central London (approx. <b>{dur}</b> commute). "
        
        if solar:
            panels = solar.get('max_panels', 0)
            kw = solar.get('estimated_kw', 0)
            cs_text += f"Identified potential for <b>{panels}</b> solar panels (est. <b>{kw}kW</b> capacity)."
            
        elements.append(Paragraph(cs_text, body_style))

    # --- 7. VALUATION RELEVANCE ---
    # Using KeepTogether to ensure the header and paragraph stay on the same page
    elements.append(KeepTogether([
        Paragraph("Valuation Relevance", styles['AzimuthSubHeader']),
        Paragraph(
            "The neighbourhood's prestige, coupled with its robust amenity density and superior connectivity, "
            "forms a strong foundation for property value. The balance of residential tranquility and urban access "
            "is a primary driver of demand. Quality indicators in education and environmental factors further "
            "underpin the location's long-term investment appeal and capital value stability.", body_style)
    ]))
    
    # FOOTER LOGO OR TEXT
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=20))
    elements.append(Paragraph("Confidential Valuation Report - Azimuth Tech Solutions", 
                             ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.grey)))
    
    doc.build(elements)

if __name__ == "__main__":
    try:
        with open('enrichment_results.json', 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        create_enhanced_report_pdf(full_data, "Azimuth_Premium_Report.pdf")
        print("Azimuth Premium PDF generated successfully.")
    except Exception as e:
        print(f"Error during PDF generation: {e}")
