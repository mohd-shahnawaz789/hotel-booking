import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = Document()

# Page Margins
sections = doc.sections
for section in sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Colors
PRIMARY = RGBColor(27, 54, 93)      # Deep Navy
SECONDARY = RGBColor(70, 130, 180)  # Steel Blue
TEXT_COLOR = RGBColor(51, 51, 51)   # Charcoal

def style_heading(p, text, level):
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.bold = True
    if level == 1:
        run.font.size = Pt(18)
        run.font.color.rgb = PRIMARY
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.size = Pt(14)
        run.font.color.rgb = SECONDARY
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.size = Pt(12)
        run.font.color.rgb = PRIMARY
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)

def add_body_p(text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.bold = True
        r_pre.font.size = Pt(11)
        r_pre.font.color.rgb = TEXT_COLOR
    r_body = p.add_run(text)
    r_body.font.name = "Calibri"
    r_body.font.size = Pt(11)
    r_body.font.color.rgb = TEXT_COLOR
    return p

# ----------------- TITLE BLOCK -----------------
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
t_run = title_p.add_run("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)\n")
t_run.font.name = "Calibri"
t_run.font.size = Pt(22)
t_run.bold = True
t_run.font.color.rgb = PRIMARY

sub_run = title_p.add_run("Project 13: Hotel Booking & Occupancy Analysis\n")
sub_run.font.name = "Calibri"
sub_run.font.size = Pt(16)
sub_run.bold = True
sub_run.font.color.rgb = SECONDARY

meta_run = title_p.add_run("Industry Domain: Hospitality & Tourism Revenue Analytics\nVersion 1.0.0 | Date: November 2026\n")
meta_run.font.name = "Calibri"
meta_run.font.size = Pt(10.5)
meta_run.italic = True

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ----------------- 1. INTRODUCTION -----------------
style_heading(doc.add_paragraph(), "1. Introduction", 1)
add_body_p("This document specifies the software requirements for the Hotel Booking & Occupancy Analysis System. The system ingests raw reservation records, identifies data quality anomalies, computes key hospitality performance indicators (KPIs), isolates realized cashflows from cancellations, evaluates channel profitability, and delivers operational recommendations.", "1.1 Purpose: ")
add_body_p("Hotels face revenue loss due to excessive online travel agency (OTA) cancellations, misaligned front-desk staffing on high-arrival days, and suboptimal pricing across room categories. This solution establishes an automated end-to-end analytics pipeline that transforms historical booking data into executive business intelligence.", "1.2 Business Scenario: ")

# ----------------- 2. ARCHITECTURE -----------------
style_heading(doc.add_paragraph(), "2. Project Architecture & Modular Structure", 1)
add_body_p("The project is structured according to professional data science standards with distinct modules for data management, documentation, analysis, and visualization:")

structure_text = """• data/raw/13_hotel_bookings.csv: Untouched historical booking dataset (1,225 rows).
• data/processed/hotel_bookings_cleaned.csv: Deduplicated and imputed dataset (1,200 rows).
• docs/SRS.md & docs/SRS_Hotel_Booking_Analysis.docx: Formal Software Requirements Specification.
• src/data_loader.py: Data ingestion, schema validation, and missing/duplicate audit.
• src/cleaner.py: Grouped median imputation, datetime extraction, and lead-time binning.
• src/analysis.py: Room-type summaries, channel rankings, peak months, NumPy stats, and IQR outliers.
• src/visualizer.py: 6-panel executive visualization dashboard generator (300 DPI).
• src/main.py: End-to-end pipeline orchestrator executable with a single command.
• notebook/Project_13_Hotel_Booking_Analysis.ipynb: Interactive presentation notebook."""
for line in structure_text.split("\n"):
    p_b = doc.add_paragraph(style='List Bullet')
    p_b.paragraph_format.space_after = Pt(2)
    p_b.paragraph_format.line_spacing = 1.15
    parts = line.split(": ")
    r1 = p_b.add_run(parts[0] + ": ")
    r1.font.name = "Calibri"
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p_b.add_run(parts[1])
    r2.font.name = "Calibri"
    r2.font.size = Pt(10.5)

# ----------------- 3. DATA DICTIONARY -----------------
style_heading(doc.add_paragraph(), "3. Data Dictionary & Schema Specification", 1)

table_data = [
    ("Column Name", "Type", "Nulls", "Description"),
    ("Booking_ID", "string", "0 (25 dups)", "Unique alphanumeric booking identifier (e.g. BK1697)"),
    ("Checkin_Date", "datetime", "0", "Scheduled check-in date (YYYY-MM-DD)"),
    ("Nights", "integer", "0", "Total duration of stay in nights"),
    ("Room_Type", "category", "0", "Category of room: Standard, Deluxe, Suite"),
    ("Booking_Channel", "category", "8", "Channel source: OTA, Direct Website, Travel Agent, Corporate, Walk-in"),
    ("Traveler_Type", "category", "0", "Segment: Business or Leisure"),
    ("Lead_Time_Days", "float", "40", "Days between reservation creation and arrival date"),
    ("Room_Rate", "float", "35", "Nightly room rate in INR (₹)"),
    ("Canceled", "category", "0", "Reservation status: 'Yes' (canceled) or 'No' (checked-in)")
]

tbl = doc.add_table(rows=len(table_data), cols=4)
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl.style = "Table Grid"

for row_idx, row in enumerate(table_data):
    for col_idx, cell_value in enumerate(row):
        cell = tbl.cell(row_idx, col_idx)
        cell.text = cell_value
        p_c = cell.paragraphs[0]
        p_c.paragraph_format.space_before = Pt(3)
        p_c.paragraph_format.space_after = Pt(3)
        run_c = p_c.runs[0]
        run_c.font.name = "Calibri"
        if row_idx == 0:
            run_c.bold = True
            run_c.font.size = Pt(10)
            shading = parse_xml(r'<w:shd {} w:fill="1B365D"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shading)
            run_c.font.color.rgb = RGBColor(255, 255, 255)
        else:
            run_c.font.size = Pt(9.5)

doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ----------------- 4. FUNCTIONAL REQUIREMENTS -----------------
style_heading(doc.add_paragraph(), "4. Functional Requirements", 1)

fr_items = [
    ("FR-1: Data Ingestion & Audit", "The system shall ingest 13_hotel_bookings.csv, verify schema integrity, report missing value counts, and identify duplicate Booking_IDs."),
    ("FR-2: Deduplication", "The system shall drop 25 duplicate Booking_ID records, preserving the first occurrence and reducing dataset size from 1,225 to 1,200 unique records."),
    ("FR-3: Justified Median Imputation", "Missing Room_Rate values (35 records) shall be imputed using the median of the corresponding Room_Type (Standard: ₹3,608; Deluxe: ₹5,642; Suite: ₹9,732). Missing Lead_Time_Days (40 records) shall be imputed using Room_Type medians. Missing Booking_Channel (8 records) shall be categorized as 'Unknown'."),
    ("FR-4: Feature Engineering", "The system shall convert Checkin_Date to datetime, extract Arrival_Year_Month, Arrival_Month_Name, and Arrival_Weekday. It shall categorize lead time into Last-Minute (0-7d), Short-Term (8-30d), and Advance (31+d)."),
    ("FR-5: Realized Revenue Logic", "Realized revenue shall apply strictly to non-canceled bookings: Revenue = Nights * Room_Rate if Canceled == 'No', else 0.00."),
    ("FR-6: Room Type Evaluation", "The system shall aggregate booking volume, realized nights, realized revenue, and cancellation rates across Standard, Deluxe, and Suite room tiers."),
    ("FR-7: Channel Ranking", "The system shall rank booking channels by realized revenue and volume, cross-referencing cancellation rates to identify margin risks."),
    ("FR-8: Seasonality & Peak Months", "The system shall calculate monthly realized revenue and identify the top 3 peak revenue months."),
    ("FR-9: Traveler Type Comparison", "The system shall contrast stay duration and revenue contribution between Leisure and Business traveler segments."),
    ("FR-10: NumPy Statistical Metrics", "The system shall compute mean, median, sample standard deviation, and percentiles of daily room rates using NumPy."),
    ("FR-11: IQR Outlier Detection", "The system shall calculate Q1, Q3, and IQR on realized booking revenues to identify high-value outlier reservations (Upper Fence = Q3 + 1.5 * IQR)."),
    ("FR-12: Visual Reporting", "The system shall render a 6-panel executive dashboard visual and save it to outputs/hotel_booking_analysis_dashboard.png at 300 DPI.")
]

for fr_title, fr_desc in fr_items:
    add_body_p(fr_desc, bold_prefix=fr_title + ": ")

# ----------------- 5. KEY DELIVERABLES & FINDINGS -----------------
style_heading(doc.add_paragraph(), "5. Core Deliverables & Key Findings", 1)

add_body_p("Deluxe rooms represent 37.67% of reservations (452 bookings) but generate ₹69,35,469.00 (42.44% of total revenue), making them the primary revenue driver. Standard rooms provide volume (48.67% share; 584 bookings; ₹54.56L), while Suites achieve the highest rate (Avg ₹10,326.10/night; ₹39.50L).", "Deliverable 1 (Room-Type Performance): ")

add_body_p("Online Travel Agencies (OTA) capture the highest volume (477 bookings; 39.75% share; ₹54.40L) but suffer from a severe 32.70% cancellation rate (surging to 37.07% for advance bookings). Direct Website generates virtually identical revenue (₹54.20L) with nearly HALF the cancellation rate (16.95%) and zero commission deductions.", "Deliverable 2 (Channel Performance): ")

add_body_p("Realized revenue peaks in December 2025 (₹17.97 Lakh; 266 nights), January 2025 (₹17.41 Lakh; 269 nights), and October 2025 (₹17.02 Lakh; 298 nights). July achieves the highest physical occupancy with 333 realized room nights.", "Deliverable 3 (Peak Revenue Months): ")

# ----------------- 6. RECOMMENDATIONS -----------------
style_heading(doc.add_paragraph(), "6. Operational & Revenue Recommendations", 1)

recs = [
    ("1. Overhaul OTA Cancellation Policies", "Enforce a mandatory 1-night non-refundable deposit for OTA bookings made >14 days in advance to mitigate the 37.07% advance cancellation rate."),
    ("2. Accelerate Direct Booking Conversion", "Incentivize direct website bookings through exclusive perks (complimentary breakfast, room upgrades, flexible cancellation) to capture high-margin Deluxe travelers and eliminate 15-25% OTA commissions."),
    ("3. Optimize Front-Desk Staffing", "Schedule additional front-desk receptionists during peak arrival windows (1:00 PM - 6:00 PM) on Wednesdays (194 arrivals) and Saturdays (181 arrivals)."),
    ("4. Target Extended Leisure Stays", "Capitalize on Leisure travelers' longer stays (4.02 nights avg vs 2.18 for Business) by launching 'Stay 4, Pay 3' vacation packages during shoulder months (April and August)."),
    ("5. Implement Dynamic Seasonal Pricing", "Surge Deluxe and Suite room rates by 15-20% during peak holiday and summer periods (Q4 and July), while offering meeting retreat packages to stimulate demand in April.")
]

for rec_title, rec_text in recs:
    add_body_p(rec_text, bold_prefix=rec_title + ": ")

# Save document
output_path = r"C:\Users\mohds\OneDrive\Desktop\hotel_booking_analysis\docs\SRS_Hotel_Booking_Analysis.docx"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
doc.save(output_path)
print(f"Successfully generated DOCX at: {output_path}")
