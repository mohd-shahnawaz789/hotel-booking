# Software Requirements Specification (SRS)
## Project 13: Hotel Booking & Occupancy Analysis
**Industry Domain:** Hospitality & Tourism Revenue Management  
**Version:** 1.0.0  
**Status:** Approved  
**Author:** Data Science & Analytics Team  
**Date:** November 2026  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional, analytical, and technical requirements for the **Hotel Booking & Occupancy Analysis System**. The primary objective is to analyze historical reservation records, guest stay patterns, distribution channels, and cancellation behaviors to help hotel management optimize room pricing, maximize revenue per available room (RevPAR), reduce cancellation leakages, and streamline front-desk staffing.

### 1.2 Business Scenario
Hotels face significant revenue volatility and operational challenges due to:
- High cancellation rates from third-party distribution intermediaries (OTAs).
- Mismatched staffing levels during unpredictable peak check-in days.
- Inefficient pricing structures across room categories (Standard, Deluxe, Suite).
- Uncaptured high-value extended leisure stays.

This project delivers an automated analytics pipeline that transforms raw booking records into actionable operational intelligence.

### 1.3 Scope of the System
The system ingests reservation data (`13_hotel_bookings.csv`), cleanses and validates records, computes core hospitality KPIs, isolates realized cashflows from cancellations, evaluates distribution channels, performs statistical outlier detection, and generates an executive visualization dashboard and operational recommendations.

---

## 2. System Architecture & Folder Structure

The project is structured according to modular data science engineering standards:

```text
hotel_booking_analysis/
│
├── data/
│   ├── raw/
│   │   └── 13_hotel_bookings.csv          # Original untouched reservation records
│   └── processed/
│       └── hotel_bookings_cleaned.csv     # Deduplicated, imputed, and feature-engineered dataset
│
├── srs/
│   └── SRS.md                             # Software Requirements Specification (this document)
│
├── src/
│   ├── __init__.py                        # Package initializer
│   ├── data_loader.py                     # Module 1: Ingestion, schema audit & inspection
│   ├── cleaner.py                         # Module 2: Deduplication & median imputation
│   ├── analysis.py                        # Module 3: KPIs, revenue, channel & outlier metrics
│   ├── visualizer.py                      # Module 4: Executive dashboard & chart generation
│   └── main.py                            # Pipeline Orchestrator (Single-command execution)
│
├── notebook/
│   └── Project_13_Hotel_Booking_Analysis.ipynb # Interactive Jupyter Notebook for presentation
│
├── outputs/
│   └── hotel_booking_analysis_dashboard.png    # High-resolution executive dashboard visual
│
├── requirements.txt                       # Project dependencies
└── README.md                              # Comprehensive user guide and findings summary
```

---

## 3. Data Dictionary & Schema Specification

| Attribute Name | Raw Data Type | Target Type | Nullable | Description / Business Meaning |
| :--- | :--- | :--- | :---: | :--- |
| `Booking_ID` | `object` (string) | `string` | No | Unique alphanumeric reservation identifier (e.g., `BK1697`). Must be unique. |
| `Checkin_Date` | `object` (string) | `datetime64[ns]` | No | Scheduled arrival date formatted as `YYYY-MM-DD`. |
| `Nights` | `int64` | `int64` | No | Total length of stay in nights (positive integer). |
| `Room_Type` | `object` | `category` | No | Room tier: `Standard`, `Deluxe`, `Suite`. |
| `Booking_Channel`| `object` | `category` | Yes (8 nulls) | Source of booking: `OTA`, `Direct Website`, `Travel Agent`, `Corporate`, `Walk-in`. |
| `Traveler_Type` | `object` | `category` | No | Purpose of travel: `Business` or `Leisure`. |
| `Lead_Time_Days`| `float64` / `int64`| `float64` | Yes (40 nulls)| Days between booking creation and scheduled check-in. |
| `Room_Rate` | `float64` | `float64` | Yes (35 nulls)| Nightly room tariff in local currency (INR ₹). |
| `Canceled` | `object` | `object` (`Yes`/`No`)| No | Reservation outcome: `'Yes'` (canceled), `'No'` (realized/checked-in). |

---

## 4. Functional Requirements

### 4.1 Module 1: Data Ingestion & Audit (`data_loader.py`)
- **FR-1.1:** System shall load `13_hotel_bookings.csv` and report initial row count, column count, and data types.
- **FR-1.2:** System shall verify null counts per column and identify duplicate `Booking_ID` keys.
- **FR-1.3:** System shall output summary descriptive statistics for both numeric and categorical attributes.

### 4.2 Module 2: Data Cleansing & Imputation (`cleaner.py`)
- **FR-2.1 Deduplication:** System shall remove duplicate `Booking_ID` occurrences, retaining the first occurrence. Exactly 25 duplicate rows must be purged, reducing total records from 1,225 to 1,200.
- **FR-2.2 Room Rate Imputation:** Missing `Room_Rate` values (35 records) shall be imputed using the **median of the corresponding `Room_Type`** (Standard = ₹3,608.00; Deluxe = ₹5,642.00; Suite = ₹9,732.00). Mean imputation is prohibited due to high skewness.
- **FR-2.3 Lead Time Imputation:** Missing `Lead_Time_Days` values (40 records) shall be imputed using the **median of the corresponding `Room_Type`** (29 days for Standard/Deluxe; 31 days for Suite).
- **FR-2.4 Booking Channel Imputation:** Missing `Booking_Channel` values (8 records) shall be categorized as `'Unknown'`.

### 4.3 Module 3: Feature Engineering (`cleaner.py` / `analysis.py`)
- **FR-3.1 Temporal Extraction:** Parse `Checkin_Date` to extract `Arrival_Year_Month` (`YYYY-MM`), `Arrival_Month_Name`, `Arrival_Weekday`, and weekend indicators.
- **FR-3.2 Lead-Time Categorization:** Using `pd.cut()`, partition lead times into three standard hospitality operational bands:
  - `Last-Minute`: 0 to 7 days
  - `Short-Term`: 8 to 30 days
  - `Advance`: 31+ days
- **FR-3.3 Realized Revenue Calculation:** Row-wise realized revenue must be computed strictly for non-canceled bookings:
  $$\text{Realized Revenue} = \begin{cases} \text{Nights} \times \text{Room\_Rate}, & \text{if Canceled} = \text{'No'} \\ 0.00, & \text{if Canceled} = \text{'Yes'} \end{cases}$$

### 4.4 Module 4: Analytical Calculations & Business Metrics (`analysis.py`)
- **FR-4.1 Overall KPIs:** Compute total bookings (1,200), total nights demanded (3,921), realized room nights (3,023), and overall cancellation percentage (21.83%).
- **FR-4.2 Room Type Evaluation:** Aggregate room-type booking volume, room rates, realized revenue, and cancellation rates.
- **FR-4.3 Channel Performance & Ranking:** Rank channels by booking volume and realized revenue, cross-referencing cancellation rates.
- **FR-4.4 Multi-Level Groupby:** Group by `['Room_Type', 'Booking_Channel']` to detect segment profitability.
- **FR-4.5 Seasonality & Peak Months:** Aggregate realized revenue by month and identify the top 3 peak revenue months.
- **FR-4.6 Segment Stay Duration:** Contrast mean and median stay duration between Leisure and Business travelers.
- **FR-4.7 NumPy Statistical Measures:** Compute sample mean, median, and standard deviation of daily room rates using NumPy.
- **FR-4.8 Outlier Detection (IQR Method):** Compute Q1, Q3, and IQR on realized booking revenues. Flag reservations exceeding $\text{Upper Fence} = Q_3 + 1.5 \times \text{IQR}$.

### 4.5 Module 5: Visualization & Reporting (`visualizer.py`)
- **FR-5.1 Executive Dashboard:** Render a multi-panel grid featuring:
  1. Monthly Realized Revenue & Room Nights Trend (Dual-axis bar/line chart).
  2. Cancellation Rate by Booking Channel (Bar chart).
  3. Realized Revenue Contribution by Room Type (Donut/Pie chart).
  4. Cancellation Rate Heatmap (Booking Channel vs. Lead-Time Band).
  5. Stay Duration Boxplot (Leisure vs. Business).
  6. Check-in Arrivals by Weekday (Front-desk workload bar chart).
- **FR-5.2 File Export:** Save dashboard visual to `outputs/hotel_booking_analysis_dashboard.png` at $\ge 300\text{ DPI}$.

---

## 5. Non-Functional Requirements (NFRs)

- **NFR-1 Code Quality & Modularity:** Clean separation of concerns across loader, cleaner, analyzer, and visualizer modules.
- **NFR-2 Portability:** Relative path resolution ensuring compatibility across Windows, Linux, and macOS without hardcoded user directories.
- **NFR-3 Execution Performance:** Complete pipeline execution within 5 seconds for datasets up to 100,000 rows.
- **NFR-4 Error Handling:** Graceful fallback if dataset is missing or column names mismatch.

---

## 6. Deliverables & Acceptance Criteria

1. **Room-Type Revenue Summary Table:** Must confirm Deluxe rooms as the #1 revenue contributor (₹69.35L; 42.44% share).
2. **Channel Cancellation Table:** Must confirm OTA cancellation rate at 32.70% vs. Direct Website at 16.95%.
3. **Monthly Trend Chart:** Must identify December, January, and October as top revenue months.
4. **Five Operational Recommendations:** Revenue management, OTA policies, front-desk staffing, extended stays, and seasonal pricing.
