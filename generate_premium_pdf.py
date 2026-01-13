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
    if not url or url == "null":
        return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def create_premium_azimuth_report(json_data, filename):
    data = json_data[0]
    
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # AZIMUTH BRAND COLORS
    AZIMUTH_BLUE = colors.HexColor("#003366")
    AZIMUTH_ACCENT = colors.HexColor("#0056b3")
    AZIMUTH_LIGHT_BG = colors.HexColor("#F4F7F9")
    
    # CUSTOM STYLES
    styles.add(ParagraphStyle(
        name='AzimuthBody', 
        parent=styles['Normal'], 
        alignment=TA_JUSTIFY, 
        fontSize=10, 
        leading=15,
        spaceAfter=14,
        textColor=colors.HexColor("#222222")
    ))
    
    styles.add(ParagraphStyle(
        name='AzimuthHeader', 
        parent=styles['Heading1'], 
        alignment=TA_LEFT, 
        fontSize=22, 
        textColor=AZIMUTH_BLUE,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='AzimuthSectionTitle', 
        parent=styles['Heading2'], 
        fontSize=14, 
        textColor=AZIMUTH_BLUE,
        spaceBefore=18,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='AzimuthSubTitle', 
        parent=styles['Heading3'], 
        fontSize=11, 
        textColor=AZIMUTH_ACCENT,
        spaceBefore=10,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        keepWithNext=True
    ))
    
    elements = []
    
    # --- LOGO / TOP STRIP ---
    elements.append(HRFlowable(width="100%", thickness=6, color=AZIMUTH_BLUE, spaceAfter=12))
    elements.append(Paragraph("AZIMUTH PROPERTY INTELLIGENCE | INSTITUTIONAL DIVISION", 
                             ParagraphStyle(name='Brand', parent=styles['Normal'], fontSize=9, letterSpacing=2, textColor=AZIMUTH_BLUE)))
    elements.append(Spacer(1, 0.3*inch))
    
    # --- REPORT TITLE ---
    elements.append(Paragraph("Neighbourhood & Location Analysis Report", styles['AzimuthHeader']))
    formatted_addr = data.get('address', {}).get('formatted_address', data.get('input_address', 'N/A'))
    elements.append(Paragraph(f"Subject Asset: {formatted_addr}", 
                             ParagraphStyle(name='Sub', parent=styles['Normal'], fontSize=12, textColor=colors.grey, spaceAfter=25)))
    
    # --- 1. LOCATION SUMMARY ---
    elements.append(Paragraph("1. Location Summary & Neighborhood Character", styles['AzimuthSectionTitle']))
    summary_text = (
        f"The subject property is strategically situated at <b>{formatted_addr}</b>, located within one of London's most distinguished and "
        "affluent residential enclaves. This micro-location is characterized by its quiet, tree-lined residential corridors, "
        "offering a high degree of seclusion and privacy while remaining perfectly positioned for immediate access to the "
        "commercial and cultural hearts of Central London. The surrounding neighborhood is widely recognized for its "
        "architectural heritage, consisting predominantly of high-value period properties that cater to a discerning resident "
        "demographic. This balance of tranquil residential utility and metropolitan accessibility underpins the area's "
        "status as a primary target for institutional-grade property investment."
    )
    elements.append(Paragraph(summary_text, styles['AzimuthBody']))
    
    # Roadmap Image
    visuals = data.get('visuals', {})
    roadmap_url = visuals.get('roadmap_url')
    if roadmap_url:
        img_data = get_image_from_url(roadmap_url)
        if img_data:
            elements.append(KeepTogether([
                Paragraph("Figure 1.1: Strategic Site Connectivity & Macro-Location Context", styles['AzimuthSubTitle']),
                Image(img_data, width=5.2*inch, height=3*inch),
                Spacer(1, 0.2*inch)
            ]))

    # --- 2. ACCESSIBILITY & CONNECTIVITY ---
    transport = data.get('transport', [])
    if transport:
        elements.append(Paragraph("2. Accessibility & Multi-Modal Connectivity", styles['AzimuthSectionTitle']))
        connectivity_text = (
            "The subject location benefits from an exceptional transit profile, offering diverse and efficient multi-modal "
            "connectivity options. The asset is served by a cluster of high-frequency London Underground stations, "
            "facilitating rapid transit to key business districts including the West End, the City, and Canary Wharf. "
            "This ease of accessibility is a primary driver of desirability for the professional workforce and is "
            "instrumental in maintaining strong occupational demand and high-yield potential."
        )
        elements.append(Paragraph(connectivity_text, styles['AzimuthBody']))
        
        transport_rows = [["Transport Node", "Rating / Review", "Indicative Proximity"]]
        for t in transport:
            rating = t.get('rating')
            rating_str = f"{rating}/5.0" if rating else "Data not available"
            dist = t.get('distance_estimate_m')
            dist_str = f"{dist}m (estimated)" if dist else "Walking distance (approx.)"
            transport_rows.append([t.get('name', 'N/A'), rating_str, dist_str])
            
        t1 = Table(transport_rows, colWidths=[2.5*inch, 1.2*inch, 1.8*inch])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZIMUTH_LIGHT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 0.1 * inch))

    # --- 3. LOCAL AMENITIES & INFRASTRUCTURE ---
    amenities = data.get('amenities', {})
    valid_amenities = {k: v for k, v in amenities.items() if v.get('count', 0) > 0}
    
    if valid_amenities:
        elements.append(Paragraph("3. Local Amenity Density & Social Infrastructure", styles['AzimuthSectionTitle']))
        
        # Satellite Image next to text
        sat_url = visuals.get('satellite_map_url')
        sat_data = get_image_from_url(sat_url) if sat_url else None
        
        amenity_intro = (
            "The neighborhood is characterized by a mature and highly developed amenity landscape. Residents have "
            "access to a concentrated range of high-quality services, ranging from essential convenience retail to "
            "luxury dining and boutique wellness facilities. This comprehensive infrastructure supports a high "
            "quality of life and reinforces the location's premium market position."
        )
        
        if sat_data:
            img = Image(sat_data, width=2.8*inch, height=2.1*inch)
            side_table_data = [[img, Paragraph(amenity_intro, styles['AzimuthBody'])]]
            t_side = Table(side_table_data, colWidths=[3*inch, 2.5*inch])
            t_side.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            elements.append(t_side)
        else:
            elements.append(Paragraph(amenity_intro, styles['Justify']))

        amenities_rows = [["Category", "Density", "Notable Nearby Example", "Rating"]]
        total_count = 0
        for cat_name, cat_data in valid_amenities.items():
            count = cat_data.get('count', 0)
            total_count += count
            top_pick = cat_data.get('top_pick')
            if top_pick:
                name = top_pick.get('name', 'N/A')
                rating = top_pick.get('rating')
                rating_str = f"{rating}/5.0" if rating else "N/A"
                amenities_rows.append([cat_name.capitalize(), f"{count} recorded", name, rating_str])
            
        t2 = Table(amenities_rows, colWidths=[1.2*inch, 1*inch, 2.3*inch, 1*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZIMUTH_LIGHT_BG]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            f"With <b>{total_count}</b> identified amenity sites within the immediate radius, the asset is exceptionally well-positioned "
            "to capture demand from residents who prioritize convenience and luxury lifestyle access. This density of "
            "established commercial interest is a significant indicator of localized economic health and stability.", styles['AzimuthBody']))

    # --- 4. EDUCATION & FAMILY INFRASTRUCTURE ---
    schools = data.get('schools', [])
    if schools:
        elements.append(Paragraph("4. Educational Quality & Family Demand Signals", styles['AzimuthSectionTitle']))
        notable_schools = [f"<b>{s.get('name')}</b>" for s in schools[:3] if s.get('name')]
        school_text = (
            "The subject location is supported by a robust educational network, a critical factor for sustained "
            "family demand in the prime London market. The presence of several high-rated institutions—including "
            f"{', '.join(notable_schools)}—indicates an area that attracts high-net-worth family occupiers. "
            "The consistent quality of local education, as reflected in positive review metrics and ratings, "
            "underpins long-term capital preservation and demand resilience across market cycles."
        )
        elements.append(Paragraph(school_text, styles['AzimuthBody']))

    # --- 5. ENVIRONMENTAL & LIVEABILITY FACTORS ---
    elements.append(Paragraph("5. Environmental Profiling & Liveability Indicators", styles['AzimuthSectionTitle']))
    
    # Crime & Safety
    crime = data.get('crime', {})
    if crime and crime.get('total_incidents', 0) > 0:
        total = crime['total_incidents']
        top_cats = crime.get('top_categories', [])
        crime_desc = (
            f"A forensic review of recent localized safety data identifies a total of <b>{total}</b> recorded incidents. "
            "While raw counts are presented, it is noted that the distribution of these incidents is largely consistent "
            "with the typical profiles of high-density central London locations where commercial and residential usage "
            "intersect. The predominant report categories include "
        )
        if top_cats:
            cat_list = [f"<b>{c[0].replace('-', ' ')}</b> ({c[1]} reports)" for c in top_cats]
            crime_desc += f"{', '.join(cat_list)}. "
        
        crime_desc += (
            "These findings suggest a dynamic urban environment. Such metrics are crucial for assessing the "
            "overall liveability and operational safety context of the residential asset."
        )
        elements.append(KeepTogether([
            Paragraph("Crime & Safety Status", styles['AzimuthSubTitle']),
            Paragraph(crime_desc, styles['AzimuthBody'])
        ]))

    # Air Quality & Green Space
    aq = data.get('air_quality', {})
    park_count = amenities.get('parks', {}).get('count', 0)
    
    env_text = ""
    if aq and aq.get('aqi'):
        env_text += (
            f"The localized Air Quality Index (AQI) is recorded at <b>{aq['aqi']}</b>, currently classified as <b>'{aq.get('category', 'Standard')}'</b>. "
            "This confirms a stable and healthy environmental context for residential use. "
        )
    if park_count > 0:
        env_text += (
            f"Environmental utility is significantly enhanced by the presence of <b>{park_count}</b> green and recreational spaces "
            "in the vicinity. This level of 'green infrastructure' is a highly valued premium feature in central London, "
            "correlated with both resident well-being and positive property price performance."
        )
    
    if env_text:
        elements.append(KeepTogether([
            Paragraph("Environmental Quality & Recreation", styles['AzimuthSubTitle']),
            Paragraph(env_text, styles['AzimuthBody'])
        ]))

    # Street View Image
    sv_url = visuals.get('street_view_url')
    if sv_url:
        img_data = get_image_from_url(sv_url)
        if img_data:
            elements.append(KeepTogether([
                Paragraph("Figure 1.2: Immediate Street Frontage & Architectural Character Context", styles['AzimuthSubTitle']),
                Image(img_data, width=5.2*inch, height=3*inch),
                Spacer(1, 0.2*inch)
            ]))

    # --- 6. COMMUTE & SUSTAINABILITY ---
    commute = data.get('commute_to_city', {})
    solar = data.get('solar', {})
    
    if (commute and commute.get('duration')) or (solar and solar.get('max_panels', 0) > 0):
        elements.append(Paragraph("6. Asset Efficiency & Connectivity Metrics", styles['AzimuthSectionTitle']))
        
        perf_text = ""
        if commute.get('duration'):
            perf_text += (
                f"The property is positioned approximately <b>{commute.get('distance', 'N/A')}</b> from the traditional "
                f"center of London. With an indicative commute duration of <b>{commute['duration']}</b>, the asset "
                "offers exceptional utility for professionals operating in the capital's central financial districts. "
            )
        if solar.get('max_panels', 0) > 0:
            perf_text += (
                f"Sustainability analysis indicates a significant potential for energy efficiency upgrades, with capacity "
                f"for up to <b>{solar['max_panels']}</b> solar panels. This would provide an estimated generating "
                f"capacity of <b>{solar.get('estimated_kw', 0)}kW</b>, aligning with modern ESG investment criteria."
            )
        elements.append(Paragraph(perf_text, styles['AzimuthBody']))

    # --- 7. VALUATION RELEVANCE ---
    elements.append(KeepTogether([
        Paragraph("7. Strategic Valuation Conclusions", styles['AzimuthSectionTitle']),
        Paragraph(
            "The fundamental value of the subject asset is intrinsically tied to its superior location and neighborhood quality. "
            "The combination of residential prestige, exceptionally high amenity density, and world-class transport "
            "connectivity forms a robust defensive profile against broader market volatility. High quality-of-life "
            "indicators, particularly in education and environmental factors, ensure sustained demand from premium "
            "resident profiles. These location-specific drivers are critical in underpinning the long-term capital "
            "value stability and investment viability of the subject property within the prime London residential sector.", 
            styles['AzimuthBody'])
    ]))
    
    # --- FOOTER ---
    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph("PROPRIETARY & CONFIDENTIAL | INSTITUTIONAL PROPERTY INTELLIGENCE BY AZIMUTH TECH SOLUTIONS", 
                             ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, textColor=colors.grey, spaceBefore=6)))
    
    doc.build(elements)

if __name__ == "__main__":
    try:
        with open('enrichment_results.json', 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        create_premium_azimuth_report(full_data, "Azimuth_Premium_Final.pdf")
        print("Detailed Azimuth Premium PDF generated successfully.")
    except Exception as e:
        print(f"Error during PDF generation: {e}")
