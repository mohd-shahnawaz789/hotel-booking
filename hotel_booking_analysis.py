"""
========================================================================================
Project 13: Hotel Booking & Occupancy Analysis (Hospitality / Tourism)
========================================================================================
Business Scenario:
Analyze room reservations, stay durations, booking channels, and cancellations
to help hotel management optimize room pricing, marketing channel mix, and front-desk staffing.

Dataset: 13_hotel_bookings.csv
Tools: pandas, numpy, matplotlib, seaborn
========================================================================================
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set visualization styles for professional aesthetics
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["figure.dpi"] = 100


# ======================================================================================
# SECTION 1: Load and Inspect Booking Records
# ======================================================================================
print("=" * 80)
print("SECTION 1: LOAD AND INSPECT THE BOOKING RECORDS")
print("=" * 80)

# Resolve dataset file path (current directory, scratch directory, or fallback)
csv_filename = "13_hotel_bookings.csv"
if not os.path.exists(csv_filename):
    fallback_path = os.path.join(os.path.dirname(__file__), csv_filename)
    if os.path.exists(fallback_path):
        csv_filename = fallback_path
    else:
        # Search common fallback
        alt_path = r"C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv"
        if os.path.exists(alt_path):
            csv_filename = alt_path

df_raw = pd.read_csv(csv_filename)

print(f"\n[INFO] Loaded dataset from: {csv_filename}")
print(f"Dataset Shape (Rows, Columns): {df_raw.shape}")

print("\n--- Actual Column Names ---")
print(df_raw.columns.tolist())

print("\n--- First 5 Records (head) ---")
print(df_raw.head())

print("\n--- DataFrame Information (info) ---")
df_raw.info()

print("\n--- Descriptive Statistics for Numerical Features (describe) ---")
print(df_raw.describe().T)

print("\n--- Descriptive Statistics for Categorical Features ---")
print(df_raw.describe(include=["object"]).T)


# ======================================================================================
# SECTION 2: Identify Missing Values and Duplicate Booking_ID Records
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 2: IDENTIFY MISSING VALUES AND DUPLICATE BOOKING_ID RECORDS")
print("=" * 80)

# Check missing values count and percentage
missing_summary = pd.DataFrame({
    "Missing_Count": df_raw.isnull().sum(),
    "Missing_Percentage": (df_raw.isnull().sum() / len(df_raw) * 100).round(2)
})
print("\n--- Missing Values Summary ---")
print(missing_summary[missing_summary["Missing_Count"] > 0])

# Check duplicate Booking_ID entries
dup_mask = df_raw["Booking_ID"].duplicated(keep=False)
num_duplicates = df_raw["Booking_ID"].duplicated().sum()
print(f"\nTotal Duplicate Booking_ID entries: {num_duplicates}")

if num_duplicates > 0:
    print("\nSample Duplicate Booking_ID Rows:")
    sample_dup_ids = df_raw.loc[dup_mask, "Booking_ID"].unique()[:5]
    print(df_raw[df_raw["Booking_ID"].isin(sample_dup_ids)].sort_values(by="Booking_ID").head(10))

# Deduplicate by Booking_ID, keeping the first occurrence
df = df_raw.drop_duplicates(subset=["Booking_ID"], keep="first").copy()
print(f"\nShape after dropping duplicate Booking_IDs: {df.shape} (Removed {len(df_raw) - len(df)} rows)")


# ======================================================================================
# SECTION 3: Handle Missing Lead_Time_Days and Room_Rate Values
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 3: HANDLE MISSING LEAD_TIME_DAYS AND ROOM_RATE (WITH JUSTIFICATION)")
print("=" * 80)

"""
Justification for Imputation Approach:
1. Room_Rate:
   - Room rates vary substantially across room tiers (e.g., Suite is ~2.7x more expensive
     than Standard). Using a global average would severely under-price Suites and over-price
     Standards.
   - We impute missing Room_Rate using the MEDIAN grouped by 'Room_Type'. Median is chosen
     over mean because hotel room rates can experience seasonal surge pricing or luxury outliers,
     making the median a much more robust measure of central tendency.

2. Lead_Time_Days:
   - Lead time is typically right-skewed (a few guests book months in advance, while most book
     within a few weeks).
   - We impute missing Lead_Time_Days using the MEDIAN grouped by 'Room_Type' (or overall median),
     preventing extreme advance bookings from distorting typical planning windows.

3. Booking_Channel:
   - For missing booking channels, we impute with 'Direct Website' (mode) or mark as 'Unknown'
     to ensure complete category integrity.
"""

print("\nMedian Room_Rate by Room_Type before imputation:")
room_rate_medians = df.groupby("Room_Type")["Room_Rate"].median()
print(room_rate_medians)

print("\nMedian Lead_Time_Days by Room_Type before imputation:")
lead_time_medians = df.groupby("Room_Type")["Lead_Time_Days"].median()
print(lead_time_medians)

# Apply group-wise median imputation
df["Room_Rate"] = df["Room_Rate"].fillna(df.groupby("Room_Type")["Room_Rate"].transform("median"))
df["Lead_Time_Days"] = df["Lead_Time_Days"].fillna(df.groupby("Room_Type")["Lead_Time_Days"].transform("median"))

# Fill any residual missing booking channels
df["Booking_Channel"] = df["Booking_Channel"].fillna("Unknown")

print(f"\nMissing values remaining in df:")
print(df[["Lead_Time_Days", "Room_Rate", "Booking_Channel"]].isnull().sum())


# ======================================================================================
# SECTION 4: Convert Checkin_Date to Datetime & Extract Arrival Month & Weekday
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 4: CONVERT CHECKIN_DATE TO DATETIME & EXTRACT ARRIVAL MONTH & WEEKDAY")
print("=" * 80)

df["Checkin_Date"] = pd.to_datetime(df["Checkin_Date"])

# Extract temporal dimensions
df["Arrival_Year"] = df["Checkin_Date"].dt.year
df["Arrival_Month_Num"] = df["Checkin_Date"].dt.month
df["Arrival_Month"] = df["Checkin_Date"].dt.strftime("%Y-%m")
df["Arrival_Month_Name"] = df["Checkin_Date"].dt.month_name()
df["Arrival_Weekday"] = df["Checkin_Date"].dt.day_name()
df["Is_Weekend"] = df["Checkin_Date"].dt.weekday.isin([4, 5, 6]).astype(int)  # Fri, Sat, Sun

print("\nSample records showing extracted arrival temporal fields:")
print(df[["Booking_ID", "Checkin_Date", "Arrival_Month", "Arrival_Month_Name", "Arrival_Weekday"]].head())


# ======================================================================================
# SECTION 5: Calculate Total Bookings, Total Room Nights, & Overall Cancellation %
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 5: OVERALL KEY PERFORMANCE INDICATORS (KPIS)")
print("=" * 80)

total_bookings = len(df)
total_nights_all = df["Nights"].sum()
total_canceled = (df["Canceled"] == "Yes").sum()
cancellation_percentage = (total_canceled / total_bookings) * 100

realized_bookings = (df["Canceled"] == "No").sum()
realized_nights = df.loc[df["Canceled"] == "No", "Nights"].sum()

print(f"Total Reservations Booked:       {total_bookings:,}")
print(f"Total Room Nights Demanded:      {total_nights_all:,} nights")
print(f"Total Bookings Canceled:         {total_canceled:,}")
print(f"Overall Cancellation Rate:       {cancellation_percentage:.2f}%")
print(f"Realized (Checked-in) Bookings:  {realized_bookings:,}")
print(f"Realized (Checked-in) Nights:    {realized_nights:,} nights")


# ======================================================================================
# SECTION 6: Row-wise Total Booking Revenue (Non-Canceled Bookings Only)
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 6: REALIZED BOOKING REVENUE CALCULATION")
print("=" * 80)

# Potential revenue if all bookings materialized
df["Potential_Revenue"] = df["Nights"] * df["Room_Rate"]

# Realized revenue applies ONLY to non-canceled bookings (Canceled == 'No'); canceled = 0
df["Revenue"] = np.where(df["Canceled"] == "No", df["Nights"] * df["Room_Rate"], 0.0)

total_realized_revenue = df["Revenue"].sum()
total_lost_revenue = df.loc[df["Canceled"] == "Yes", "Potential_Revenue"].sum()

print(f"Total Realized Revenue (Non-Canceled): INR {total_realized_revenue:,.2f}")
print(f"Total Potential Revenue (All Bookings): INR {df['Potential_Revenue'].sum():,.2f}")
print(f"Total Revenue Lost to Cancellations:   INR {total_lost_revenue:,.2f}")

print("\nSample records with row-wise revenue:")
print(df[["Booking_ID", "Room_Type", "Nights", "Room_Rate", "Canceled", "Revenue"]].head(8))


# ======================================================================================
# SECTION 7: Compare Average Room Rates & Occupancy Across Room Types
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 7: ROOM TYPE COMPARISON (RATES, NIGHTS, REVENUE & OCCUPANCY SHARE)")
print("=" * 80)

room_type_summary = df.groupby("Room_Type").agg(
    Total_Bookings=("Booking_ID", "count"),
    Avg_Room_Rate=("Room_Rate", "mean"),
    Median_Room_Rate=("Room_Rate", "median"),
    Total_Nights_Booked=("Nights", "sum"),
    Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
    Realized_Revenue=("Revenue", "sum"),
    Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

# Add shares
room_type_summary["Booking_Share_Pct"] = (room_type_summary["Total_Bookings"] / total_bookings * 100).round(2)
room_type_summary["Nights_Share_Pct"] = (room_type_summary["Realized_Nights"] / realized_nights * 100).round(2)
room_type_summary["Revenue_Share_Pct"] = (room_type_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

# Format for clean display
display_rt = room_type_summary.copy()
display_rt["Avg_Room_Rate"] = display_rt["Avg_Room_Rate"].map("INR {:,.2f}".format)
display_rt["Realized_Revenue"] = display_rt["Realized_Revenue"].map("INR {:,.2f}".format)
display_rt["Cancellation_Rate_Pct"] = display_rt["Cancellation_Rate_Pct"].map("{:.2f}%".format)
display_rt["Booking_Share_Pct"] = display_rt["Booking_Share_Pct"].map("{:.2f}%".format)
display_rt["Revenue_Share_Pct"] = display_rt["Revenue_Share_Pct"].map("{:.2f}%".format)

print("\nDeliverable 1: Room-Type Revenue Summary Table:")
print(display_rt.to_string(index=False))


# ======================================================================================
# SECTION 8: Rank Booking Channels by Booking Volume and Revenue
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 8: RANK BOOKING CHANNELS BY BOOKING VOLUME AND REVENUE")
print("=" * 80)

channel_summary = df.groupby("Booking_Channel").agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
    Total_Nights=("Nights", "sum"),
    Realized_Revenue=("Revenue", "sum"),
    Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

channel_summary["Booking_Share_Pct"] = (channel_summary["Total_Bookings"] / total_bookings * 100).round(2)
channel_summary["Revenue_Share_Pct"] = (channel_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

# Rank by Realized Revenue (descending)
channel_summary = channel_summary.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
channel_summary["Revenue_Rank"] = channel_summary.index + 1

# Rank by Total Bookings (descending)
channel_summary["Volume_Rank"] = channel_summary["Total_Bookings"].rank(ascending=False, method="min").astype(int)

print("\nDeliverable 2: Booking Channel Performance Ranking Table:")
display_chan = channel_summary.copy()
display_chan["Realized_Revenue"] = display_chan["Realized_Revenue"].map("INR {:,.2f}".format)
display_chan["Cancellation_Rate_Pct"] = display_chan["Cancellation_Rate_Pct"].map("{:.2f}%".format)
display_chan["Revenue_Share_Pct"] = display_chan["Revenue_Share_Pct"].map("{:.2f}%".format)
display_chan["Booking_Share_Pct"] = display_chan["Booking_Share_Pct"].map("{:.2f}%".format)
print(display_chan[["Revenue_Rank", "Volume_Rank", "Booking_Channel", "Total_Bookings", 
                    "Booking_Share_Pct", "Realized_Revenue", "Revenue_Share_Pct", 
                    "Cancellation_Rate_Pct"]].to_string(index=False))


# ======================================================================================
# SECTION 9: Analyze Cancellation Rates by Booking Channel and Lead-Time Bands
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 9: CANCELLATION RATES BY BOOKING CHANNEL AND LEAD-TIME BANDS")
print("=" * 80)

# Bin lead times into standard hospitality categories
lead_bins = [-1, 7, 30, df["Lead_Time_Days"].max() + 1]
lead_labels = ["Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)"]
df["Lead_Time_Category"] = pd.cut(df["Lead_Time_Days"], bins=lead_bins, labels=lead_labels)

# 1. Overall Cancellation by Lead-Time Category
lead_cancellation = df.groupby("Lead_Time_Category", observed=False).agg(
    Total_Bookings=("Booking_ID", "count"),
    Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

print("\n--- Cancellation Rate by Lead-Time Category ---")
print(lead_cancellation.to_string(index=False))

# 2. Multi-level Crosstab / Pivot Table: Booking_Channel x Lead_Time_Category
channel_lead_pivot = pd.crosstab(
    df["Booking_Channel"],
    df["Lead_Time_Category"],
    values=df["Canceled"] == "Yes",
    aggfunc=lambda x: round(np.mean(x) * 100, 2)
)

print("\n--- Cancellation Rate (%) Matrix: Booking Channel vs. Lead-Time Category ---")
print(channel_lead_pivot)

# Multi-level Groupby Hint: groupby(['Room_Type', 'Booking_Channel'])
print("\n--- Multi-Level Summary: groupby(['Room_Type', 'Booking_Channel']) ---")
multi_summary = df.groupby(["Room_Type", "Booking_Channel"]).agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Revenue=("Revenue", "sum"),
    Avg_Rate=("Room_Rate", "mean"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).round(2)
print(multi_summary)


# ======================================================================================
# SECTION 10: Identify Top 3 Peak Revenue Months
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 10: MONTHLY REVENUE ANALYSIS & TOP 3 PEAK REVENUE MONTHS")
print("=" * 80)

monthly_summary = df.groupby(["Arrival_Month", "Arrival_Month_Name"]).agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
    Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
    Realized_Revenue=("Revenue", "sum"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index().sort_values(by="Arrival_Month")

# Rank months by realized revenue
monthly_ranked = monthly_summary.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
top_3_months = monthly_ranked.head(3)

print("\nDeliverable 3: Top 3 Peak Revenue Months:")
for idx, row in top_3_months.iterrows():
    print(f"Rank {idx+1}: {row['Arrival_Month']} ({row['Arrival_Month_Name']}) "
          f"- Revenue: INR {row['Realized_Revenue']:,.2f} | "
          f"Nights: {row['Realized_Nights']:,} | Bookings: {row['Realized_Bookings']:,}")

print("\nFull 12-Month Performance Table:")
display_months = monthly_summary.copy()
display_months["Realized_Revenue"] = display_months["Realized_Revenue"].map("INR {:,.2f}".format)
display_months["Cancellation_Rate_Pct"] = display_months["Cancellation_Rate_Pct"].map("{:.2f}%".format)
print(display_months.to_string(index=False))


# ======================================================================================
# SECTION 11: Compare Average Stay Duration: Leisure vs. Business Travelers
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 11: STAY DURATION COMPARISON: LEISURE VS. BUSINESS TRAVELERS")
print("=" * 80)

traveler_summary = df.groupby("Traveler_Type").agg(
    Total_Bookings=("Booking_ID", "count"),
    Mean_Stay_Nights=("Nights", "mean"),
    Median_Stay_Nights=("Nights", "median"),
    Std_Stay_Nights=("Nights", "std"),
    Min_Stay=("Nights", "min"),
    Max_Stay=("Nights", "max"),
    Realized_Revenue=("Revenue", "sum"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

traveler_summary["Revenue_Share_Pct"] = (traveler_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

print("\n--- Traveler Segment Profile Table ---")
print(traveler_summary.round(2).to_string(index=False))

leisure_avg = traveler_summary.loc[traveler_summary["Traveler_Type"] == "Leisure", "Mean_Stay_Nights"].values[0]
business_avg = traveler_summary.loc[traveler_summary["Traveler_Type"] == "Business", "Mean_Stay_Nights"].values[0]
print(f"\nKey Finding: Leisure guests stay an average of {leisure_avg:.2f} nights, which is "
      f"{(leisure_avg / business_avg):.2f}x longer than Business guests ({business_avg:.2f} nights).")


# ======================================================================================
# SECTION 12: NumPy Statistical Measures for Daily Room Rates
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 12: NUMPY STATISTICAL MEASURES FOR DAILY ROOM RATES")
print("=" * 80)

# Extract room rates as a 1D NumPy array
room_rates_arr = df["Room_Rate"].to_numpy()

rate_mean = np.mean(room_rates_arr)
rate_median = np.median(room_rates_arr)
rate_std = np.std(room_rates_arr, ddof=1)  # Sample standard deviation
rate_min = np.min(room_rates_arr)
rate_max = np.max(room_rates_arr)
rate_25th = np.percentile(room_rates_arr, 25)
rate_75th = np.percentile(room_rates_arr, 75)

print(f"NumPy Computed Daily Room Rate Metrics:")
print(f"  • Mean Rate:       INR {rate_mean:,.2f}")
print(f"  • Median Rate:     INR {rate_median:,.2f}")
print(f"  • Std Deviation:   INR {rate_std:,.2f}")
print(f"  • Minimum Rate:    INR {rate_min:,.2f}")
print(f"  • Maximum Rate:    INR {rate_max:,.2f}")
print(f"  • 25th Percentile: INR {rate_25th:,.2f}")
print(f"  • 75th Percentile: INR {rate_75th:,.2f}")


# ======================================================================================
# SECTION 13: Identify Unusually High Booking Values Using the IQR Method
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 13: OUTLIER DETECTION IN REALIZED BOOKING REVENUE (IQR METHOD)")
print("=" * 80)

# Filter for non-canceled bookings only to analyze realized value outliers
realized_rev_arr = df.loc[df["Canceled"] == "No", "Revenue"].to_numpy()

# Calculate Q1 (25th percentile) and Q3 (75th percentile) using np.percentile()
q1 = np.percentile(realized_rev_arr, 25)
q3 = np.percentile(realized_rev_arr, 75)
iqr = q3 - q1

lower_fence = max(0.0, q1 - 1.5 * iqr)
upper_fence = q3 + 1.5 * iqr

print(f"IQR Calculation Parameters for Realized Revenue:")
print(f"  • Q1 (25th Percentile):   INR {q1:,.2f}")
print(f"  • Q3 (75th Percentile):   INR {q3:,.2f}")
print(f"  • IQR (Q3 - Q1):          INR {iqr:,.2f}")
print(f"  • Lower Fence (Q1 - 1.5*IQR): INR {lower_fence:,.2f}")
print(f"  • Upper Fence (Q3 + 1.5*IQR): INR {upper_fence:,.2f}")

# Filter outlier bookings
outlier_mask = (df["Canceled"] == "No") & (df["Revenue"] > upper_fence)
df_outliers = df[outlier_mask].sort_values(by="Revenue", ascending=False)

print(f"\nTotal High-Value Outlier Bookings Found: {len(df_outliers)} "
      f"({(len(df_outliers) / len(realized_rev_arr) * 100):.2f}% of realized bookings)")

print("\nTop 5 Highest-Value Outlier Bookings:")
print(df_outliers[["Booking_ID", "Room_Type", "Traveler_Type", "Booking_Channel", 
                   "Nights", "Room_Rate", "Revenue"]].head(5).to_string(index=False))


# ======================================================================================
# SECTION 14: Lead-Time Categories Using pd.cut()
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 14: LEAD-TIME CATEGORIZATION USING PD.CUT()")
print("=" * 80)

# Define lead time bands:
# Last-Minute: 0 to 7 days
# Short-Term:  8 to 30 days
# Advance:     31 days and above
bins = [-1, 7, 30, int(df["Lead_Time_Days"].max()) + 1]
labels = ["Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)"]

df["Lead_Time_Band"] = pd.cut(df["Lead_Time_Days"], bins=bins, labels=labels, right=True)

lead_summary = df.groupby("Lead_Time_Band", observed=False).agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Revenue=("Revenue", "sum"),
    Avg_Stay_Nights=("Nights", "mean"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

lead_summary["Booking_Share_Pct"] = (lead_summary["Total_Bookings"] / total_bookings * 100).round(2)
lead_summary["Revenue_Share_Pct"] = (lead_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

print("\nLead-Time Category Performance Table:")
display_lead = lead_summary.copy()
display_lead["Realized_Revenue"] = display_lead["Realized_Revenue"].map("INR {:,.2f}".format)
display_lead["Cancellation_Rate_Pct"] = display_lead["Cancellation_Rate_Pct"].map("{:.2f}%".format)
print(display_lead.to_string(index=False))


# ======================================================================================
# SECTION 15: Five Revenue and Operations Recommendations for Hotel Management
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 15: FIVE REVENUE & OPERATIONS RECOMMENDATIONS")
print("=" * 80)

recommendations = """
1. OVERHAUL OTA CANCELLATION POLICIES (Deposit & Stricter Window):
   Findings: OTA represents the largest booking channel (39.75% volume, 477 bookings) but has an
   alarming 32.70% cancellation rate, which surges to 37.07% for advance bookings (>30 days).
   Recommendation: Implement non-refundable or 1-night deposit policies for OTA advance bookings,
   and introduce rate-parity incentives on direct channels to shift guests away from high-commission,
   high-cancellation intermediaries.

2. SCALE DIRECT WEBSITE MARKETING & LOYALTY PERKS:
   Findings: Direct Website generates virtually identical realized revenue (INR 5.42M) to OTA (INR 5.44M)
   with HALF the cancellation rate (16.95% vs. 32.70%) and zero commission overhead. Deluxe rooms via
   Direct Website generated the single highest revenue of any segment (INR 2.46M).
   Recommendation: Allocate digital marketing budgets toward SEO and meta-search (Google Hotel Ads)
   with exclusive direct-booking benefits (free breakfast, early check-in, flexible cancellation)
   to capture high-margin Deluxe travelers.

3. OPTIMIZE FRONT-DESK STAFFING BY ARRIVAL PEAKS & WEEKDAY DEMAND:
   Findings: Check-in arrivals peak heavily on Wednesdays (194 bookings) and Saturdays (181 bookings),
   while Sundays (158) and Mondays (165) have the lowest turnover. Mid-week check-ins are dominated
   by 2-night Business stays, whereas weekend check-ins are longer 4-night Leisure stays.
   Recommendation: Roster two additional front-desk agents and luggage concierges during peak turnover
   windows (2 PM - 6 PM) on Wednesdays and Saturdays, while scheduling maintenance and deep-cleaning
   during low-turnover Monday mornings.

4. HARNESS EXTENDED-STAY PACKAGES FOR LEISURE TRAVELERS:
   Findings: Leisure guests stay an average of 4.02 nights (generating 74.9% of hotel revenue), compared
   to 2.18 nights for Business guests. Furthermore, IQR analysis revealed 49 high-value outlier bookings
   (generating up to INR 143k per reservation), primarily driven by long stays in Deluxe and Suites.
   Recommendation: Introduce "Stay 4, Pay 3" or "Weekly Workcation" packages during off-peak shoulder
   months (April and August) to bolster room nights and lift occupancy.

5. IMPLEMENT DYNAMIC SEASONAL PRICING FOR Q4 & SUMMER SURGES:
   Findings: Monthly revenue peaks in December (INR 1.80M), January (INR 1.74M), October (INR 1.70M),
   and July (highest nights sold: 333 nights), whereas April generates less than half of peak revenue
   (INR 908k).
   Recommendation: Implement tiered dynamic pricing, raising rates by 15-20% for Suites and Deluxe rooms
   during Q4 holiday months and July summer vacation, while offering corporate meeting bundles to stimulate
   volume during low-occupancy months (April/May).
"""
print(recommendations)


# ======================================================================================
# BONUS ANALYSES & VISUALIZATIONS (COMPREHENSIVE DASHBOARD)
# ======================================================================================
print("\n" + "=" * 80)
print("GENERATING COMPREHENSIVE BUSINESS VISUALIZATIONS DASHBOARD...")
print("=" * 80)

# Create a multi-panel figure for executive reporting
fig, axes = plt.subplots(3, 2, figsize=(18, 16))
plt.subplots_adjust(hspace=0.35, wspace=0.25)

# 1. Monthly Occupancy & Realized Revenue Trend
ax1 = axes[0, 0]
color1 = "#1f77b4"
color2 = "#2ca02c"
months = monthly_summary["Arrival_Month_Name"]

ax1.bar(months, monthly_summary["Realized_Revenue"] / 1e5, color=color1, alpha=0.7, label="Realized Revenue (Lakh INR)")
ax1.set_ylabel("Revenue (Lakh INR)", color=color1, fontsize=11, fontweight="bold")
ax1.tick_params(axis="x", rotation=45)
ax1.set_title("Monthly Realized Revenue & Room Nights Trend", fontsize=12, fontweight="bold")

# Twin axis for room nights
ax1_twin = ax1.twinx()
ax1_twin.plot(months, monthly_summary["Realized_Nights"], color=color2, marker="o", linewidth=2.5, label="Realized Nights")
ax1_twin.set_ylabel("Realized Room Nights", color=color2, fontsize=11, fontweight="bold")
ax1_twin.grid(False)

# 2. Cancellation Rate by Booking Channel
ax2 = axes[0, 1]
sns.barplot(data=channel_summary, x="Booking_Channel", y="Cancellation_Rate_Pct", ax=ax2, palette="Reds_d")
ax2.set_title("Cancellation Rate by Booking Channel (%)", fontsize=12, fontweight="bold")
ax2.set_ylabel("Cancellation Rate (%)", fontsize=11)
ax2.set_xlabel("Booking Channel", fontsize=11)
for p in ax2.patches:
    ax2.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")

# 3. Revenue Share by Room Type
ax3 = axes[1, 0]
room_colors = ["#4e79a7", "#f28e2b", "#e15759"]
axes[1, 0].pie(room_type_summary["Realized_Revenue"], labels=room_type_summary["Room_Type"],
               autopct="%1.1f%%", startangle=140, colors=room_colors, explode=(0.02, 0.02, 0.05),
               textprops={"fontsize": 11, "fontweight": "bold"})
ax3.set_title("Realized Revenue Share by Room Type", fontsize=12, fontweight="bold")

# 4. Cancellation Rate by Lead-Time Category & Channel (Heatmap)
ax4 = axes[1, 1]
sns.heatmap(channel_lead_pivot, annot=True, fmt=".1f", cmap="YlOrRd", cbar_kws={"label": "Cancellation Rate (%)"}, ax=ax4)
ax4.set_title("Cancellation Rate Heatmap: Channel vs. Lead-Time Band", fontsize=12, fontweight="bold")
ax4.set_ylabel("Booking Channel", fontsize=11)
ax4.set_xlabel("Lead-Time Band", fontsize=11)

# 5. Stay Duration Distribution: Leisure vs. Business (Boxplot with Jitter)
ax5 = axes[2, 0]
sns.boxplot(data=df, x="Traveler_Type", y="Nights", palette="Set2", ax=ax5, showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "red", "markeredgecolor": "black", "markersize": "7"})
ax5.set_title("Stay Duration (Nights) by Traveler Segment (Red Diamond = Mean)", fontsize=12, fontweight="bold")
ax5.set_ylabel("Length of Stay (Nights)", fontsize=11)
ax5.set_xlabel("Traveler Segment", fontsize=11)

# 6. Check-in Arrivals & Cancellation by Day of the Week (Staffing Optimization)
ax6 = axes[2, 1]
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_summary = df.groupby("Arrival_Weekday").agg(
    Bookings=("Booking_ID", "count"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reindex(weekday_order).reset_index()

sns.barplot(data=weekday_summary, x="Arrival_Weekday", y="Bookings", ax=ax6, palette="Blues_d")
ax6.set_title("Front-Desk Workload: Total Check-in Arrivals by Day of Week", fontsize=12, fontweight="bold")
ax6.set_ylabel("Total Arrivals", fontsize=11)
ax6.set_xlabel("Day of Arrival", fontsize=11)
ax6.tick_params(axis="x", rotation=30)
for p in ax6.patches:
    ax6.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")

plt.tight_layout()

# Save dashboard image to disk
chart_path = "hotel_booking_analysis_dashboard.png"
plt.savefig(chart_path, dpi=300)
print(f"\n[SUCCESS] Visualizations saved to: {os.path.abspath(chart_path)}")
plt.close()

print("\n" + "=" * 80)
print("PROJECT 13: ANALYSIS COMPLETED SUCCESSFULLY!")
print("=" * 80)
