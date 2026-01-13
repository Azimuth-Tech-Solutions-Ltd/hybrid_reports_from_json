from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame
from reportlab.lib.units import inch

def create_report_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    header_style = styles["Heading1"]
    subheader_style = styles["Heading2"]
    body_style = styles["BodyText"]
    
    elements = []
    
    # 1. Section Header
    elements.append(Paragraph("Neighbourhood & Location Overview", header_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 2. Location Summary
    elements.append(Paragraph("Location Summary", subheader_style))
    elements.append(Paragraph(
        "The subject property is located at 4E Airlie Gardens, London, W8 7AJ. "
        "Situated in the Campden Hill neighbourhood within the Royal Borough of Kensington and Chelsea, "
        "the area is an established prime residential district. The urban character is predominantly central "
        "and residential, characterized by high-value period architecture and close proximity to major green "
        "spaces and upscale commercial corridors.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 3. Accessibility & Connectivity
    elements.append(Paragraph("Accessibility & Connectivity", subheader_style))
    elements.append(Paragraph(
        "The location is exceptionally well-connected to the London Underground network, "
        "providing efficient access to the West End and the City. All primary transport nodes "
        "are within walking distance, offering high-frequency services across multiple lines.", body_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    transport_data = [
        ["Transport Node", "Type", "Indicative Accessibility"],
        ["Notting Hill Gate", "Subway Station", "Walking distance (approx.)"],
        ["Holland Park", "Subway Station", "Walking distance (approx.)"],
        ["High Street Kensington", "Subway Station", "Walking distance (approx.)"]
    ]
    t1 = Table(transport_data, colWidths=[2*inch, 1.5*inch, 2*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.2 * inch))
    
    # 4. Local Amenities
    elements.append(Paragraph("Local Amenities", subheader_style))
    amenities_data = [
        ["Category", "Nearby Count", "Notable Example", "Rating"],
        ["Supermarkets", "19", "Damascene Rose Deli", "4.6"],
        ["Restaurants", "20", "Maggie Jones's Restaurant", "4.6"],
        ["Gyms", "20", "Onebody Clinic", "5.0"],
        ["Parks", "20", "Renaud’s Rocks", "5.0"]
    ]
    t2 = Table(amenities_data, colWidths=[1.5*inch, 1.2*inch, 2*inch, 0.8*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Interpretation: The exceptionally high count of amenities in every category (80 total) reflects the mature "
        "and prestigious nature of the location. High ratings across all sectors indicate a consistent level of quality "
        "in local services, contributing to a high level of residential liveability and convenience.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 5. Education
    elements.append(Paragraph("Education", subheader_style))
    elements.append(Paragraph(
        "The property is situated within an area of high educational quality, with several well-regarded institutions "
        "nearby. Notable examples include the Ladbroke Square Montessori School and Artpeggios, both of which maintain "
        "exceptional review signals (Rating: 5.0). The presence of diverse educational facilities supports family occupancy.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 6. Environmental & Liveability Factors
    elements.append(Paragraph("Environmental & Liveability Factors", subheader_style))
    elements.append(Paragraph("Crime & Safety", styles["Heading3"]))
    elements.append(Paragraph(
        "The locality recorded 1,494 incidents during the reported period. The primary categories contributing to this "
        "total include anti-social behaviour (307 incidents), violent crime (282 incidents), and shoplifting (188 incidents). "
        "These figures are reported descriptively and should be considered in context.", body_style))
    
    elements.append(Paragraph("Air Quality", styles["Heading3"]))
    elements.append(Paragraph(
        "Air quality at the location is categorized as 'Good air quality' with an index of 78. This indicates a level of "
        "liveability consistent with central residential districts.", body_style))
    
    elements.append(Paragraph("Green & Recreational Spaces", styles["Heading3"]))
    elements.append(Paragraph(
        "The area is remarkably well-served by green spaces, with 20 recreational areas identified in the vicinity. "
        "This includes major open spaces and smaller local parks, such as Renaud’s Rocks.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 7. Commute to Central London
    elements.append(Paragraph("Commute to Central London", subheader_style))
    elements.append(Paragraph(
        "The property is located approximately 5.7 km from central London. The estimated commute duration is 24 minutes, "
        "reflecting the area's central position and efficient connectivity.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 8. Sustainability & Energy Context
    elements.append(Paragraph("Sustainability & Energy Context", subheader_style))
    elements.append(Paragraph(
        "Indicative analysis shows a solar potential for the property of approximately 22 maximum array panels, "
        "with an estimated capacity of 8.8 kW.", body_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # 9. Map & Visual References
    elements.append(Paragraph("Map & Visual References", subheader_style))
    placeholder_data = [
        [Paragraph("[Street View Image - Placeholder]", body_style)],
        [Paragraph("[Satellite Map - Placeholder]", body_style)],
        [Paragraph("[Local Amenities Map - Placeholder]", body_style)]
    ]
    t3 = Table(placeholder_data, colWidths=[5.5*inch], rowHeights=[1*inch, 1*inch, 1*inch])
    t3.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 0.2 * inch))
    
    # 10. Valuation Relevance
    elements.append(Paragraph("Valuation Relevance", subheader_style))
    elements.append(Paragraph(
        "The quality of the neighbourhood is a critical driver of property value in Kensington. High amenity density, "
        "exceptional transport connectivity, and access to premium green spaces create a robust demand profile. "
        "The area's established reputation for quality and safety further stabilizes capital value.", body_style))
    
    doc.build(elements)

if __name__ == "__main__":
    create_report_pdf("Neighbourhood_Report_4e_Airlie_Gardens.pdf")
    print("PDF generated successfully.")

