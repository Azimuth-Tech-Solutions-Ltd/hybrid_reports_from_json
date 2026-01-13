import os
import json
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle, Image, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors

# Azimuth Branding Colors
AZIMUTH_BLUE = colors.HexColor('#003366')
AZIMUTH_LIGHT_BG = colors.HexColor('#F4F7F9')

class AzimuthModularStyler:
    def __init__(self, output_path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _get_image_from_url(self, url: str, width=200, height=150):
        """Fetch image from URL and return ReportLab Image object"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img = Image(BytesIO(response.content))
            # Set dimensions (supports both pixel and inch units)
            if isinstance(width, (int, float)) and isinstance(height, (int, float)):
                img.drawWidth = width
                img.drawHeight = height
            return img
        except Exception as e:
            print(f"Warning: Could not load image from {url}: {e}")
            return None

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='AZ_Title',
            parent=self.styles['Heading1'],
            fontSize=26,
            textColor=AZIMUTH_BLUE,
            alignment=TA_CENTER,
            spaceAfter=40,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Section_Header',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=AZIMUTH_BLUE,
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold',
            borderPadding=(2, 0, 8, 0),
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Sub_Header',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=AZIMUTH_BLUE,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Body',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Formal_Header',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=AZIMUTH_BLUE,
            spaceBefore=14,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Meta',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_RIGHT,
            fontName='Helvetica-Oblique'
        ))
        self.styles.add(ParagraphStyle(
            name='AZ_Caption',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            spaceBefore=2,
            spaceAfter=8
        ))

    def generate_pdf(self, report_json):
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        story = []
        
        # 1. Cover / Header (skip for single-section PDFs)
        sections = report_json.get('sections', {})
        is_single_section = len(sections) == 1
        single_section_name = list(sections.keys())[0] if is_single_section else None
        skip_header = is_single_section and single_section_name in ['instructions', 'property_overview', 'neighbourhood_overview', 'market_commentary', 'valuation_methodology']
        
        if not skip_header:
            metadata = report_json.get('metadata', {})
            context = report_json.get('property_context', {})
            
            address = f"{context.get('paon', '')} {context.get('street', '')}, {context.get('postcode', '')}"
            story.append(Paragraph("AZIMUTH INSTITUTIONAL VALUATION", self.styles['AZ_Title']))
            story.append(Paragraph(f"Subject: {address}", self.styles['AZ_Sub_Header']))
            story.append(Paragraph(f"Report ID: {metadata.get('report_id')}", self.styles['AZ_Meta']))
            story.append(Paragraph(f"Generated: {metadata.get('generation_timestamp')}", self.styles['AZ_Meta']))
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="100%", thickness=2, color=AZIMUTH_BLUE, spaceAfter=20))
        
        # 2. Sections
        sections = report_json.get('sections', {})
        
        # Order we want them in the report
        order = ['instructions', 'property_overview', 'neighbourhood_overview', 'market_commentary', 'valuation_methodology', 'location_analysis', 'infrastructure', 'safety', 'valuation_quality']
        
        # If order doesn't include all sections, add the rest
        all_sections = set(sections.keys())
        ordered_sections = set(order)
        remaining = all_sections - ordered_sections
        if remaining:
            order.extend(sorted(remaining))
        
        for section_name in order:
            if section_name not in sections:
                continue
                
            section = sections[section_name]
            data = section.get('data', {})
            
            # Section Header (only if multiple sections)
            if len(sections) > 1:
                story.append(Paragraph(section_name.replace('_', ' ').upper(), self.styles['AZ_Section_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=10))
            
            # Render based on section structure
            if section_name == 'instructions':
                content = data.get('content', '')
                # Process line by line for more control
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    
                    # Major section headers (bold with extra space)
                    major_headers = ['Scope of Work', 'Nature of the Valuation', 'Reliance and Liability', 
                                    'Information Sources', 'Special Assumptions', 'General']
                    if line in major_headers:
                        story.append(Spacer(1, 12))
                        story.append(Paragraph(f"<b>{line}</b>", self.styles['AZ_Formal_Header']))
                        story.append(Spacer(1, 6))
                    # Section headers (numbered or all caps short lines)
                    elif (line[0].isdigit() and '.' in line[:3]) or (len(line) < 60 and line.isupper() and not line.endswith('.') and not ':' in line):
                        story.append(Spacer(1, 4))
                        story.append(Paragraph(f"<b>{line}</b>", self.styles['AZ_Formal_Header']))
                        story.append(Spacer(1, 4))
                    # Bold key terms at start of paragraphs (including Subject Property with address)
                    elif line.startswith('Subject Property:') or line.startswith('Report Date:') or line.startswith('Prepared for:') or line.startswith('Purpose of Valuation:'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            story.append(Paragraph(f"<b>{parts[0]}:</b> {parts[1].strip()}", self.styles['AZ_Body']))
                        else:
                            story.append(Paragraph(line, self.styles['AZ_Body']))
                    # Regular paragraph text
                    else:
                        story.append(Paragraph(line, self.styles['AZ_Body']))
                    i += 1
            
            elif section_name == 'property_overview':
                # Section title
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>Section 2 : The Property</b>", self.styles['AZ_Section_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=12))
                
                # Get property context for image matching (we'll load image at the end)
                property_context = report_json.get('property_context', {})
                postcode = property_context.get('postcode', '')
                paon = property_context.get('paon', '')
                street = property_context.get('street', '')
                
                # Render as 2-3 paragraphs (new format)
                paragraph_keys = ['paragraph_1', 'paragraph_2', 'paragraph_3']
                has_paragraphs = any(key in data for key in paragraph_keys)
                
                if has_paragraphs:
                    # New format: 2-3 paragraphs
                    for para_key in paragraph_keys:
                        if para_key in data:
                            para_text = data[para_key]
                            if isinstance(para_text, str) and para_text.strip():
                                story.append(Paragraph(para_text, self.styles['AZ_Body']))
                                story.append(Spacer(1, 10))
                    
                    # Add floor area if available
                    if 'floor_area' in data and isinstance(data['floor_area'], dict):
                        sqm = data['floor_area'].get('sqm', 0)
                        sqft = data['floor_area'].get('sqft', 0)
                        if sqm > 0:
                            story.append(Paragraph(f"<b>Gross Internal Area:</b> {sqm:.2f} square meters ({sqft:,.2f} square feet).", self.styles['AZ_Body']))
                            story.append(Spacer(1, 10))
                else:
                    # Fallback: old format with subsections (for backward compatibility)
                    subsection_order = [
                        'position_and_locality', 'heritage_and_construction', 'external_amenities_and_parking',
                        'internal_accommodation', 'floor_area', 'tenure_and_possession',
                        'condition_and_maintenance', 'planning_and_use', 'energy_and_sustainability'
                    ]
                    subsection_titles = {
                        'position_and_locality': 'Position and Locality',
                        'heritage_and_construction': 'Heritage and Construction',
                        'external_amenities_and_parking': 'External Amenities and Parking',
                        'internal_accommodation': 'Internal Accommodation',
                        'floor_area': 'Floor Areas',
                        'tenure_and_possession': 'Tenure and Possession',
                        'condition_and_maintenance': 'Condition and Maintenance',
                        'planning_and_use': 'Planning and Use',
                        'energy_and_sustainability': 'Energy and Sustainability'
                    }
                    
                    for subsection_key in subsection_order:
                        if subsection_key not in data:
                            continue
                        subsection_data = data[subsection_key]
                        subsection_title = subsection_titles.get(subsection_key, subsection_key.replace('_', ' ').title())
                        
                        story.append(Spacer(1, 8))
                        story.append(Paragraph(f"<b>{subsection_title}</b>", self.styles['AZ_Formal_Header']))
                        story.append(Spacer(1, 4))
                        
                        if subsection_key == 'floor_area':
                            if isinstance(subsection_data, dict):
                                sqm = subsection_data.get('sqm', 0)
                                sqft = subsection_data.get('sqft', 0)
                                story.append(Paragraph(f"The property has a Gross Internal Area (GIA) of approximately {sqm:.2f} square meters ({sqft:,.2f} square feet).", self.styles['AZ_Body']))
                        else:
                            if isinstance(subsection_data, str):
                                paragraphs = subsection_data.split('\n\n')
                                for para in paragraphs:
                                    para = para.strip()
                                    if para:
                                        story.append(Paragraph(para, self.styles['AZ_Body']))
                                        story.append(Spacer(1, 3))
                
                # Add property image at the END (smaller size)
                # Use enrichment_data from report JSON (unified format) instead of loading from file
                image_url = None
                enrichment_data = report_json.get('enrichment_data', {})
                if enrichment_data:
                    visuals = enrichment_data.get('visuals', {})
                    if visuals:
                        image_url = visuals.get('street_view_url') or visuals.get('satellite_map_url')
                
                # Fallback: try to load from file if not in report JSON (for backward compatibility)
                if not image_url:
                    try:
                        enrichment_path = 'enrichment_results.json'
                        if os.path.exists(enrichment_path):
                            with open(enrichment_path, 'r', encoding='utf-8') as f:
                                enrichment_file_data = json.load(f)
                            
                            # Find matching property by postcode or address components
                            for item in enrichment_file_data:
                                if isinstance(item, dict):
                                    addr = item.get('input_address', '').lower()
                                    formatted = item.get('address', {}).get('formatted_address', '').lower()
                                    # Match by postcode or address components
                                    if (postcode.lower() in addr or postcode.lower() in formatted or 
                                        (paon and paon.lower() in addr) or (street and street.lower() in addr)):
                                        visuals = item.get('visuals', {})
                                        image_url = visuals.get('street_view_url') or visuals.get('satellite_map_url')
                                        break
                    except Exception as e:
                        print(f"Warning: Could not load enrichment data: {e}")
                
                # Add property image at the end (smaller)
                if image_url:
                    img = self._get_image_from_url(image_url, width=300, height=200)
                    if img:
                        story.append(Spacer(1, 12))
                        story.append(img)
            
            elif section_name == 'neighbourhood_overview':
                # Section title
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>Section 3 : Neighbourhood & Location Overview</b>", self.styles['AZ_Section_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=12))
                
                # Load enrichment data for images
                property_context = report_json.get('property_context', {})
                postcode = property_context.get('postcode', '')
                paon = property_context.get('paon', '')
                street = property_context.get('street', '')
                enrichment_data = None
                visuals = {}
                
                try:
                    enrichment_path = 'enrichment_results.json'
                    if os.path.exists(enrichment_path):
                        with open(enrichment_path, 'r', encoding='utf-8') as f:
                            all_enrichment = json.load(f)
                        
                        for item in all_enrichment:
                            if isinstance(item, dict):
                                addr = item.get('input_address', '').lower()
                                formatted = item.get('address', {}).get('formatted_address', '').lower()
                                if (postcode.lower() in addr or postcode.lower() in formatted or 
                                    (paon and paon.lower() in addr) or (street and street.lower() in addr)):
                                    enrichment_data = item
                                    visuals = item.get('visuals', {})
                                    break
                except Exception as e:
                    print(f"Warning: Could not load enrichment data: {e}")
                
                # 1. Location Summary
                if 'location_summary' in data:
                    story.append(KeepTogether([
                        Paragraph("1. Location Summary", self.styles['AZ_Formal_Header']),
                        Paragraph(data['location_summary'], self.styles['AZ_Body'])
                    ]))
                    story.append(Spacer(1, 10))
                
                # 2. Transport & Connectivity (with roadmap image)
                if 'transport' in data:
                    roadmap_url = visuals.get('roadmap_url')
                    roadmap_img = None
                    if roadmap_url:
                        roadmap_img = self._get_image_from_url(roadmap_url, width=5.2*inch, height=2.8*inch)
                    
                    transport_elements = [
                        Paragraph("2. Transport & Connectivity", self.styles['AZ_Formal_Header']),
                        Paragraph(data['transport'], self.styles['AZ_Body'])
                    ]
                    if roadmap_img:
                        transport_elements.append(roadmap_img)
                        transport_elements.append(Paragraph("Fig 1.1: Connectivity Context", self.styles['AZ_Caption']))
                    
                    story.append(KeepTogether(transport_elements))
                    story.append(Spacer(1, 10))
                
                # 3. Amenities & Infrastructure (with satellite image side-by-side)
                if 'amenities' in data:
                    sat_url = visuals.get('satellite_map_url')
                    sat_img = None
                    if sat_url:
                        sat_img = self._get_image_from_url(sat_url, width=2.8*inch, height=2*inch)
                    
                    if sat_img:
                        amenities_table = Table([
                            [sat_img, Paragraph(data['amenities'], self.styles['AZ_Body'])]
                        ], colWidths=[3*inch, 2.5*inch])
                        amenities_table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ]))
                        story.append(KeepTogether([
                            Paragraph("3. Local Social Infrastructure", self.styles['AZ_Formal_Header']),
                            amenities_table
                        ]))
                    else:
                        story.append(KeepTogether([
                            Paragraph("3. Amenities & Infrastructure", self.styles['AZ_Formal_Header']),
                            Paragraph(data['amenities'], self.styles['AZ_Body'])
                        ]))
                    story.append(Spacer(1, 10))
                
                # 4. Education
                if 'education' in data:
                    story.append(KeepTogether([
                        Paragraph("4. Education", self.styles['AZ_Formal_Header']),
                        Paragraph(data['education'], self.styles['AZ_Body'])
                    ]))
                    story.append(Spacer(1, 10))
                
                # 5. Safety & Crime Context (with street view image)
                if 'safety' in data:
                    sv_url = visuals.get('street_view_url')
                    sv_img = None
                    if sv_url:
                        sv_img = self._get_image_from_url(sv_url, width=5.2*inch, height=2.8*inch)
                    
                    safety_elements = [
                        Paragraph("5. Crime & Safety", self.styles['AZ_Formal_Header']),
                        Paragraph(data['safety'], self.styles['AZ_Body'])
                    ]
                    if sv_img:
                        safety_elements.append(sv_img)
                        safety_elements.append(Paragraph("Fig 1.2: Street Frontage", self.styles['AZ_Caption']))
                    
                    story.append(KeepTogether(safety_elements))
                    story.append(Spacer(1, 10))
                
                # 6. Environmental Quality
                if 'environment' in data:
                    story.append(KeepTogether([
                        Paragraph("6. Environmental Liveability", self.styles['AZ_Formal_Header']),
                        Paragraph(data['environment'], self.styles['AZ_Body'])
                    ]))
                    story.append(Spacer(1, 10))
            
            elif section_name == 'market_commentary':
                # Section title
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>4. Market Commentary</b>", self.styles['AZ_Section_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=12))
                
                # 1. Economic Overview
                if 'economic_overview' in data:
                    story.append(Paragraph("<b>Economic Overview</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['economic_overview'], self.styles['AZ_Body']))
                
                # 2. Stamp Duty
                if 'stamp_duty_commentary' in data:
                    story.append(Paragraph("<b>Stamp Duty and Property Taxes</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['stamp_duty_commentary'], self.styles['AZ_Body']))
                
                if 'sdlt_table' in data:
                    t_data = data['sdlt_table']
                    if t_data and len(t_data) > 0:
                        t = Table(t_data, colWidths=[200, 150, 150])
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('BACKGROUND', (0, 1), (-1, -1), AZIMUTH_LIGHT_BG),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 12))
                
                # 3. PCL Market
                if 'pcl_market_overview' in data:
                    story.append(Paragraph("<b>Prime Central London Residential Market</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['pcl_market_overview'], self.styles['AZ_Body']))
                
                # 4. wider London
                if 'london_market_sales' in data:
                    story.append(Paragraph("<b>London Property Market Overview</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph("<b>Sales Market</b>", self.styles['AZ_Body']))
                    story.append(Paragraph(data['london_market_sales'], self.styles['AZ_Body']))
                
                if 'london_market_lettings' in data:
                    story.append(Paragraph("<b>Lettings Market</b>", self.styles['AZ_Body']))
                    story.append(Paragraph(data['london_market_lettings'], self.styles['AZ_Body']))

            elif section_name == 'valuation_methodology':
                # Section title
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>5. Valuation Methodology and Comparable Evidence</b>", self.styles['AZ_Section_Header']))
                story.append(HRFlowable(width="30%", thickness=1, color=AZIMUTH_BLUE, hAlign='LEFT', spaceAfter=12))
                
                # 1. Methodology
                if 'methodology' in data:
                    story.append(Paragraph("<b>Methodology</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['methodology'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))
                
                # 2. Subject Property Summary
                if 'subject_property_summary' in data:
                    story.append(Paragraph("<b>Subject Property Summary</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['subject_property_summary'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))
                
                # 3. Comparable Evidence
                if 'comparable_evidence_intro' in data:
                    story.append(Paragraph("<b>Comparable Evidence</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['comparable_evidence_intro'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 8))
                
                # Comparable Table (if available)
                if 'comparable_table' in data and isinstance(data['comparable_table'], list) and len(data['comparable_table']) > 1:
                    # Render as table - 10 columns: Address, Distance, Type, Tenure, Beds, Size (sqm), Price, £/sqft, Sale Date, Key Differences
                    # Adjust column widths to fit on page (A4 width is ~7.5 inches)
                    table_data = data['comparable_table']
                    num_cols = len(table_data[0]) if table_data else 10
                    
                    # Column widths for 10 columns - wider table to fit key differences
                    # Total width should be ~7.5 inches for A4, but we'll use full width
                    # Reduce smaller columns and increase Key Differences column significantly
                    if num_cols == 10:
                        col_widths = [1.5*inch, 0.4*inch, 0.3*inch, 0.4*inch, 0.3*inch, 0.4*inch, 0.6*inch, 0.5*inch, 0.6*inch, 2.5*inch]
                    else:
                        # Fallback for 8 columns (old format)
                        col_widths = [1.8*inch, 0.6*inch, 0.5*inch, 0.6*inch, 0.8*inch, 0.6*inch, 0.8*inch, 1.3*inch]
                    
                    comp_table = Table(table_data, colWidths=col_widths[:num_cols])
                    comp_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 7),
                        ('FONTSIZE', (0, 1), (-1, -1), 7),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), AZIMUTH_LIGHT_BG),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, AZIMUTH_LIGHT_BG]),
                        ('WORDWRAP', (0, 0), (-1, -1), True),
                    ]))
                    story.append(comp_table)
                    story.append(Spacer(1, 10))
                
                # Note: Individual comparable narratives (comparable_1, comparable_2, etc.) are not rendered
                # The table above provides all necessary comparable information
                
                # 4. Rationale and Justification
                if 'rationale_and_justification' in data:
                    story.append(Paragraph("<b>Rationale and Justification</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['rationale_and_justification'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))
                
                # 5. Conclusion (expanded)
                if 'conclusion' in data:
                    story.append(Paragraph("<b>Conclusion</b>", self.styles['AZ_Formal_Header']))
                    # Split conclusion into paragraphs if it's long
                    conclusion_text = data['conclusion']
                    paragraphs = conclusion_text.split('. ')
                    for para in paragraphs:
                        para = para.strip()
                        if para and not para.endswith('.'):
                            para += '.'
                        if para:
                            story.append(Paragraph(para, self.styles['AZ_Body']))
                            story.append(Spacer(1, 6))
                    story.append(Spacer(1, 10))
                
                # 6. Demand, Marketability and Saleability
                if 'demand_marketability' in data:
                    story.append(Paragraph("<b>Demand, Marketability and Saleability</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['demand_marketability'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))
                
                # 7. Section 6: Final Summary
                if 'section_6_summary' in data:
                    story.append(Paragraph("<b>6. Valuation Summary</b>", self.styles['AZ_Formal_Header']))
                    story.append(Paragraph(data['section_6_summary'], self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))
                
                # 8. Lender's Action Points
                if 'lenders_action_points' in data:
                    story.append(Paragraph("<b>Lender's Action Points</b>", self.styles['AZ_Formal_Header']))
                    # Check if it contains bullet points or is plain text
                    action_text = data['lenders_action_points']
                    if '•' in action_text or '-' in action_text:
                        # Split by bullet points
                        lines = action_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line:
                                story.append(Paragraph(line, self.styles['AZ_Body']))
                    else:
                        story.append(Paragraph(action_text, self.styles['AZ_Body']))
                    story.append(Spacer(1, 10))

            elif section_name == 'valuation_quality':
                # Render table for stats
                table_data = [["Metric", "Value"]]
                for key, val in data.items():
                    if isinstance(val, float):
                        val = f"{val:.4f}"
                    table_data.append([key.replace('_', ' ').title(), str(val)])
                
                t = Table(table_data, colWidths=[200, 150])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), AZIMUTH_BLUE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), AZIMUTH_LIGHT_BG),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                story.append(t)
                story.append(Spacer(1, 20))
            
            else:
                # Generic LLM Narrative rendering
                for key, val in data.items():
                    if isinstance(val, str):
                        # Subheader for the specific field if it's not the only one
                        if len(data) > 1:
                            story.append(Paragraph(key.replace('_', ' ').title(), self.styles['AZ_Sub_Header']))
                        story.append(Paragraph(val, self.styles['AZ_Body']))
                    elif isinstance(val, dict):
                        # Handle area {sqm, sqft}
                        area_str = ", ".join([f"{k.upper()}: {v}" for k, v in val.items()])
                        story.append(Paragraph(area_str, self.styles['AZ_Body']))
            
            # Assumptions & Limitations (Skip for instructions, property_overview, neighbourhood_overview, market_commentary, and valuation_methodology - they're formal sections)
            if section_name not in ['instructions', 'property_overview', 'neighbourhood_overview', 'market_commentary', 'valuation_methodology']:
                if section.get('assumptions'):
                    story.append(Paragraph("Assumptions:", self.styles['AZ_Sub_Header']))
                    for asm in section['assumptions']:
                        story.append(Paragraph(f"• {asm}", self.styles['AZ_Meta']))
                
                if section.get('limitations'):
                    story.append(Paragraph("Limitations:", self.styles['AZ_Sub_Header']))
                    for lim in section['limitations']:
                        story.append(Paragraph(f"• {lim}", self.styles['AZ_Meta']))
            
            story.append(Spacer(1, 20))
            # Page break after major sections if needed, or just spacers
            # story.append(PageBreak())

        doc.build(story)
        return self.output_path

def style_report(json_path, pdf_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        report_json = json.load(f)
    
    styler = AzimuthModularStyler(pdf_path)
    return styler.generate_pdf(report_json)

