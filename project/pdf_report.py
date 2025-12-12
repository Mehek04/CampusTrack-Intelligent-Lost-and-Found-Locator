from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, date
from io import BytesIO

def format_date_for_pdf(date_value):
    """Helper function to format any date/datetime object or string for PDF display"""
    if date_value is None:
        return 'N/A'
    
    # If it's already a string, return it as is
    if isinstance(date_value, str):
        return date_value
    
    # If it's a datetime object
    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d %H:%M:%S')
    
    # If it's a date object (different from datetime!)
    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')
    
    # For any other type, convert to string
    return str(date_value)

def format_short_date_for_pdf(date_value):
    """Helper function to format date for short display (YYYY-MM-DD only)"""
    if date_value is None:
        return 'N/A'
    
    # If it's already a string
    if isinstance(date_value, str):
        # If string is long, truncate it
        if len(date_value) > 10:
            return date_value[:10]
        return date_value
    
    # If it's a datetime object
    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')
    
    # If it's a date object
    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')
    
    # For any other type
    return str(date_value)[:10]

def generate_admin_report(users_db, found_items_db, lost_items_db, claims_db, admins_db):
    """Generate comprehensive PDF report for admin with proper page management"""
    
    buffer = BytesIO()
    
    # Calculate available page height (A4 is 29.7cm)
    PAGE_HEIGHT = 29.7*cm
    PAGE_WIDTH = 21*cm
    
    # Margins
    left_margin = 1.5*cm
    right_margin = 1.5*cm
    top_margin = 2*cm
    bottom_margin = 2*cm
    
    # Available content height
    CONTENT_HEIGHT = PAGE_HEIGHT - top_margin - bottom_margin
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        title="Campus Lost & Found System Report",
        author="Admin Panel",
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ==================== CUSTOM STYLES ====================
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1A365D'),
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#2D3748'),
        alignment=TA_LEFT,
        spaceBefore=30,  # Reduced from 40
        spaceAfter=15,   # Reduced from 25
        fontName='Helvetica-Bold'
    )
    
    subsection_style = ParagraphStyle(
        'SubSectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4A5568'),
        alignment=TA_LEFT,
        spaceBefore=12,  # Reduced from 20
        spaceAfter=8,    # Reduced from 15
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2D3748'),
        alignment=TA_LEFT,
        spaceAfter=6,    # Reduced from 8
        leading=13       # Reduced from 14
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2D3748'),
        alignment=TA_CENTER,
        leading=11       # Reduced from 12
    )
    
    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        alignment=TA_CENTER,
        leading=11       # Reduced from 12
    )
    
    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 50))
    story.append(Paragraph("CAMPUS LOST & FOUND SYSTEM", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Comprehensive Administrative Report", subsection_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          ParagraphStyle('Metadata', parent=normal_style, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph("<b>System Version:</b> 2.0", 
                          ParagraphStyle('Metadata', parent=normal_style, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Spacer(1, 40))
    
    # Quick stats
    total_users = len(users_db) if users_db else 0
    total_found = len(found_items_db) if found_items_db else 0
    total_lost = len(lost_items_db) if lost_items_db else 0
    total_claims = len(claims_db) if claims_db else 0
    total_admins = len(admins_db) if admins_db else 1
    
    quick_stats = [
        ['<b>Metric</b>', '<b>Count</b>'],
        ['Total Users', str(total_users)],
        ['Found Items', str(total_found)],
        ['Lost Items', str(total_lost)],
        ['Total Claims', str(total_claims)],
        ['Administrators', str(total_admins)]
    ]
    
    formatted_stats = []
    for row in quick_stats:
        formatted_row = []
        for cell in row:
            if isinstance(cell, str) and cell.startswith('<b>'):
                formatted_row.append(Paragraph(cell, table_header_style))
            else:
                formatted_row.append(Paragraph(str(cell), table_cell_style))
        formatted_stats.append(formatted_row)
    
    quick_table = Table(formatted_stats, colWidths=[3*cm, 2*cm])
    quick_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F9FF')]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2B6CB0')),
    ]))
    
    story.append(quick_table)
    story.append(Spacer(1, 60))
    story.append(Paragraph("Confidential - For Administrative Use Only", small_style))
    story.append(PageBreak())
    
    # ==================== TABLE OF CONTENTS ====================
    story.append(Paragraph("TABLE OF CONTENTS", section_style))
    story.append(Spacer(1, 15))
    
    # Create TOC with proper formatting
    toc_data = []
    toc_pages = [3, 4, 5, 6, 7, 8, 9]
    toc_items = [
        "1. SYSTEM SUMMARY",
        "2. USER DETAILS",
        "3. FOUND ITEMS", 
        "4. LOST ITEMS",
        "5. CLAIMS ANALYSIS",
        "6. ADMINISTRATORS",
        "7. STATISTICAL ANALYSIS"
    ]
    
    for i, item in enumerate(toc_items):
        toc_data.append([
            Paragraph(item, normal_style),
            Paragraph(f"Page {toc_pages[i]}", normal_style)
        ])
    
    toc_table = Table(toc_data, colWidths=[12*cm, 3*cm])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    
    story.append(toc_table)
    story.append(Spacer(1, 20))
    story.append(PageBreak())
    
    # ==================== 1. SYSTEM SUMMARY ====================
    # Use KeepTogether to prevent breaking
    summary_section = []
    summary_section.append(Paragraph("1. SYSTEM SUMMARY", section_style))
    summary_section.append(Spacer(1, 5))
    
    # Calculate statistics
    active_users = sum(1 for u in users_db.values() if isinstance(u, dict) and u.get('is_active', True)) if users_db else 0
    
    pending_claims = 0
    approved_claims = 0
    rejected_claims = 0
    if claims_db:
        for c in claims_db.values():
            if isinstance(c, dict):
                status = c.get('status', 'pending')
                if status == 'pending':
                    pending_claims += 1
                elif status == 'approved':
                    approved_claims += 1
                elif status == 'rejected':
                    rejected_claims += 1
    
    summary_data = [
        ['<b>Metric</b>', '<b>Count</b>', '<b>Details</b>'],
        ['Total Users', str(total_users), 'All registered users'],
        ['Active Users', str(active_users), 'Currently active accounts'],
        ['Inactive Users', str(total_users - active_users), 'Deactivated accounts'],
        ['Administrators', str(total_admins), 'Admin accounts'],
        ['Found Items', str(total_found), 'Items posted as found'],
        ['Lost Items', str(total_lost), 'Items reported lost'],
        ['Total Claims', str(total_claims), 'All claim requests'],
        ['Pending Claims', str(pending_claims), 'Awaiting approval'],
        ['Approved Claims', str(approved_claims), 'Successfully approved'],
        ['Rejected Claims', str(rejected_claims), 'Rejected claims']
    ]
    
    formatted_summary = []
    for row in summary_data:
        formatted_row = []
        for cell in row:
            if isinstance(cell, str) and cell.startswith('<b>'):
                formatted_row.append(Paragraph(cell, table_header_style))
            else:
                formatted_row.append(Paragraph(str(cell), table_cell_style))
        formatted_summary.append(formatted_row)
    
    summary_table = Table(formatted_summary, colWidths=[4*cm, 2*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2F855A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FFF4')]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2F855A')),
    ]))
    
    summary_section.append(summary_table)
    summary_section.append(Spacer(1, 20))
    
    # Keep the entire summary section together
    story.append(KeepTogether(summary_section))
    
    # ==================== 2. USER DETAILS ====================
    if users_db and len(users_db) > 0:
        user_section = []
        user_section.append(Paragraph("2. USER DETAILS", section_style))
        user_section.append(Paragraph(f"Total Users: {total_users}", subsection_style))
        user_section.append(Spacer(1, 8))
        
        user_headers = ['<b>Username</b>', '<b>Email</b>', '<b>Type</b>', '<b>Department</b>', '<b>Joined</b>', '<b>Status</b>']
        user_data = [user_headers]
        
        for username, user in users_db.items():
            if isinstance(user, dict):
                user_type = user.get('user_type', 'student').title()
                department = user.get('department', 'N/A')
                if department != 'N/A':
                    department = department.replace('_', ' ').title()
                
                status = 'Active' if user.get('is_active', True) else 'Inactive'
                
                # Use helper function for date formatting
                join_date = format_short_date_for_pdf(user.get('created_at', 'N/A'))
                
                user_data.append([
                    username,
                    user.get('email', 'N/A'),
                    user_type,
                    department,
                    join_date,
                    status
                ])
        
        if len(user_data) > 1:
            formatted_user_data = []
            for row in user_data:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, str) and cell.startswith('<b>'):
                        formatted_row.append(Paragraph(cell, table_header_style))
                    else:
                        formatted_row.append(Paragraph(str(cell), table_cell_style))
                formatted_user_data.append(formatted_row)
            
            # Reduce table height by adjusting row heights
            user_table = Table(formatted_user_data, colWidths=[2.2*cm, 4.8*cm, 1.8*cm, 2.8*cm, 2*cm, 1.8*cm])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EFF6FF')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#2B6CB0')),
            ]))
            user_section.append(user_table)
        else:
            user_section.append(Paragraph("No user data available", normal_style))
        
        user_section.append(Spacer(1, 15))
        story.append(KeepTogether(user_section))
    
    # ==================== 3. FOUND ITEMS ====================
    if found_items_db and len(found_items_db) > 0:
        found_section = []
        found_section.append(Paragraph("3. FOUND ITEMS", section_style))
        found_section.append(Paragraph(f"Total Found Items: {total_found}", subsection_style))
        found_section.append(Spacer(1, 8))
        
        found_headers = ['<b>ID</b>', '<b>Device</b>', '<b>Posted By</b>', '<b>Location</b>', '<b>Status</b>', '<b>Date</b>']
        found_data = [found_headers]
        
        for item_id, item in found_items_db.items():
            if isinstance(item, dict):
                # Use helper function for date formatting
                posted_date = format_short_date_for_pdf(item.get('posted_date', 'N/A'))
                
                found_data.append([
                    str(item_id),
                    item.get('device_name', 'N/A'),
                    item.get('posted_by', 'N/A'),
                    item.get('location', 'N/A'),
                    item.get('status', 'active').title(),
                    posted_date
                ])
        
        if len(found_data) > 1:
            formatted_found_data = []
            for row in found_data:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, str) and cell.startswith('<b>'):
                        formatted_row.append(Paragraph(cell, table_header_style))
                    else:
                        formatted_row.append(Paragraph(str(cell), table_cell_style))
                formatted_found_data.append(formatted_row)
            
            found_table = Table(formatted_found_data, colWidths=[1.2*cm, 3.2*cm, 2.2*cm, 2.8*cm, 2.2*cm, 2.2*cm])
            found_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D69E2E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFBEB')),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#FBD38D')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFFBEB')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D69E2E')),
            ]))
            found_section.append(found_table)
        else:
            found_section.append(Paragraph("No found items data available", normal_style))
        
        found_section.append(Spacer(1, 15))
        
        # Check if we should break page before this section
        # If previous section was large, add page break
        if len(story) > 3 and isinstance(story[-2], KeepTogether):
            # Check approximate height of previous content
            story.append(PageBreak())
        
        story.append(KeepTogether(found_section))
    
    # ==================== 4. LOST ITEMS ====================
    if lost_items_db and len(lost_items_db) > 0:
        lost_section = []
        lost_section.append(Paragraph("4. LOST ITEMS", section_style))
        lost_section.append(Paragraph(f"Total Lost Items: {total_lost}", subsection_style))
        lost_section.append(Spacer(1, 8))
        
        lost_headers = ['<b>ID</b>', '<b>Device</b>', '<b>Posted By</b>', '<b>Location</b>', '<b>Status</b>', '<b>Lost Date</b>']
        lost_data = [lost_headers]
        
        for item_id, item in lost_items_db.items():
            if isinstance(item, dict):
                # Use helper function for date formatting
                lost_date_value = item.get('lost_date') or item.get('posted_date', 'N/A')
                lost_date = format_short_date_for_pdf(lost_date_value)
                
                lost_data.append([
                    str(item_id),
                    item.get('device_name', 'N/A'),
                    item.get('posted_by', 'N/A'),
                    item.get('location', 'N/A'),
                    item.get('status', 'active').title(),
                    lost_date
                ])
        
        if len(lost_data) > 1:
            formatted_lost_data = []
            for row in lost_data:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, str) and cell.startswith('<b>'):
                        formatted_row.append(Paragraph(cell, table_header_style))
                    else:
                        formatted_row.append(Paragraph(str(cell), table_cell_style))
                formatted_lost_data.append(formatted_row)
            
            lost_table = Table(formatted_lost_data, colWidths=[1.2*cm, 3.2*cm, 2.2*cm, 2.8*cm, 2.2*cm, 2.2*cm])
            lost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C53030')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF5F5')),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#FEB2B2')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#C53030')),
            ]))
            lost_section.append(lost_table)
        else:
            lost_section.append(Paragraph("No lost items data available", normal_style))
        
        lost_section.append(Spacer(1, 15))
        story.append(KeepTogether(lost_section))
    
    # ==================== 5. CLAIMS ANALYSIS ====================
    if claims_db and len(claims_db) > 0:
        # Try to group small sections together
        claims_section = []
        claims_section.append(Paragraph("5. CLAIMS ANALYSIS", section_style))
        claims_section.append(Paragraph(f"Total Claims: {total_claims}", subsection_style))
        claims_section.append(Spacer(1, 8))
        
        claims_headers = ['<b>ID</b>', '<b>Claimant</b>', '<b>Owner</b>', '<b>Status</b>', '<b>Date</b>', '<b>Item</b>']
        claims_data = [claims_headers]
        
        for claim_id, claim in claims_db.items():
            if isinstance(claim, dict):
                item_name = "Unknown"
                found_item_id = claim.get('found_item_id')
                if found_item_id and found_items_db and found_item_id in found_items_db:
                    item = found_items_db.get(found_item_id, {})
                    if isinstance(item, dict):
                        item_name = item.get('device_name', 'Unknown')
                
                # Use helper function for date formatting
                claim_date = format_short_date_for_pdf(claim.get('claim_date', 'N/A'))
                
                claims_data.append([
                    str(claim_id),
                    claim.get('claimant_username', 'N/A'),
                    claim.get('owner_username', 'N/A'),
                    claim.get('status', 'pending').title(),
                    claim_date,
                    item_name
                ])
        
        if len(claims_data) > 1:
            formatted_claims_data = []
            for row in claims_data:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, str) and cell.startswith('<b>'):
                        formatted_row.append(Paragraph(cell, table_header_style))
                    else:
                        formatted_row.append(Paragraph(str(cell), table_cell_style))
                formatted_claims_data.append(formatted_row)
            
            claims_table = Table(formatted_claims_data, colWidths=[1.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 3.2*cm])
            claims_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#805AD5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAF5FF')),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D6BCFA')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAF5FF')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#805AD5')),
            ]))
            claims_section.append(claims_table)
        else:
            claims_section.append(Paragraph("No claims data available", normal_style))
        
        claims_section.append(Spacer(1, 15))
        story.append(KeepTogether(claims_section))
    
    # ==================== 6. ADMINISTRATORS ====================
    # Group admins with stats if possible
    admin_section = []
    admin_section.append(Paragraph("6. ADMINISTRATORS", section_style))
    admin_section.append(Spacer(1, 8))
    
    admin_headers = ['<b>Username</b>', '<b>Created By</b>', '<b>Created At</b>']
    admin_data = [admin_headers]
    
    for username, admin in admins_db.items():
        if isinstance(admin, dict):
            # Use helper function for date formatting
            created_at = format_date_for_pdf(admin.get('created_at', 'N/A'))
            
            admin_data.append([
                username,
                admin.get('created_by', 'system'),
                created_at
            ])
    
    if len(admin_data) > 1:
        formatted_admin_data = []
        for row in admin_data:
            formatted_row = []
            for cell in row:
                if isinstance(cell, str) and cell.startswith('<b>'):
                    formatted_row.append(Paragraph(cell, table_header_style))
                else:
                    formatted_row.append(Paragraph(str(cell), table_cell_style))
            formatted_admin_data.append(formatted_row)
        
        admin_table = Table(formatted_admin_data, colWidths=[3*cm, 3*cm, 4*cm])
        admin_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CBD5E0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EDF2F7')]),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#4A5568')),
        ]))
        admin_section.append(admin_table)
    else:
        admin_section.append(Paragraph("No admin data available", normal_style))
    
    admin_section.append(Spacer(1, 15))
    
    # ==================== 7. STATISTICAL ANALYSIS ====================
    admin_section.append(Paragraph("7. STATISTICAL ANALYSIS", section_style))
    admin_section.append(Spacer(1, 8))
    
    # Calculate statistics
    active_found = sum(1 for item in found_items_db.values() 
                      if isinstance(item, dict) and item.get('status', 'active') == 'active') if found_items_db else 0
    claimed_found = sum(1 for item in found_items_db.values() 
                       if isinstance(item, dict) and item.get('status', 'active') == 'claimed') if found_items_db else 0
    
    active_lost = sum(1 for item in lost_items_db.values() 
                     if isinstance(item, dict) and item.get('status', 'active') == 'active') if lost_items_db else 0
    found_lost = sum(1 for item in lost_items_db.values() 
                    if isinstance(item, dict) and item.get('status', 'active') == 'found') if lost_items_db else 0
    
    pending_claims_count = sum(1 for claim in claims_db.values() 
                              if isinstance(claim, dict) and claim.get('status', 'pending') == 'pending') if claims_db else 0
    resolved_claims_count = sum(1 for claim in claims_db.values() 
                               if isinstance(claim, dict) and claim.get('status', 'pending') in ['approved', 'rejected']) if claims_db else 0
    
    stats_data = [
        ['<b>Category</b>', '<b>Active</b>', '<b>Resolved</b>', '<b>Total</b>', '<b>Resolution Rate</b>'],
        ['Found Items', str(active_found), str(claimed_found), str(total_found), 
         f"{round((claimed_found/total_found*100), 1) if total_found > 0 else 0.0}%"],
        ['Lost Items', str(active_lost), str(found_lost), str(total_lost),
         f"{round((found_lost/total_lost*100), 1) if total_lost > 0 else 0.0}%"],
        ['Claims', str(pending_claims_count), str(resolved_claims_count), str(total_claims),
         f"{round((resolved_claims_count/total_claims*100), 1) if total_claims > 0 else 0.0}%"]
    ]
    
    formatted_stats_data = []
    for row in stats_data:
        formatted_row = []
        for cell in row:
            if isinstance(cell, str) and cell.startswith('<b>'):
                formatted_row.append(Paragraph(cell, table_header_style))
            else:
                formatted_row.append(Paragraph(str(cell), table_cell_style))
        formatted_stats_data.append(formatted_row)
    
    stats_table = Table(formatted_stats_data, colWidths=[3.2*cm, 2*cm, 2*cm, 2*cm, 3.2*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FEF3C7')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FCE7F3')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#D1FAE5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2D3748')),
    ]))
    
    admin_section.append(stats_table)
    admin_section.append(Spacer(1, 25))
    
    # Group admins and stats together
    story.append(KeepTogether(admin_section))
    
    # ==================== FOOTER ====================
    story.append(Spacer(1, 30))
    
    # Add horizontal line
    footer_line = Table([['']], colWidths=[doc.width])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(footer_line)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("COMPREHENSIVE ADMIN REPORT - CAMPUS LOST & FOUND SYSTEM", small_style))
    story.append(Paragraph(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", small_style))
    story.append(Paragraph("Confidential - For Administrative Use Only", small_style))
    story.append(Paragraph("--- END OF REPORT ---", small_style))
    
    # Build PDF
    try:
        doc.build(story)
    except Exception as e:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        error_story = []
        error_story.append(Paragraph("ERROR GENERATING REPORT", section_style))
        error_story.append(Paragraph(f"An error occurred: {str(e)}", normal_style))
        error_story.append(Paragraph("Please check the application logs for more details.", normal_style))
        doc.build(error_story)
    
    buffer.seek(0)
    return buffer