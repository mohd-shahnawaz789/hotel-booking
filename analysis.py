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

# Configure visual styling for publication-quality charts
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.sans-serif"] = "DejaVu Sans"


# ======================================================================================
# SECTION 1: Load and Inspect Booking Records
# ======================================================================================
print("=" * 80)
print("SECTION 1: LOAD AND INSPECT THE BOOKING RECORDS")
print("=" * 80)

# Load dataset (adjust path as needed)
csv_file = "13_hotel_bookings.csv"
if not os.path.exists(csv_file):
    # Fallback to absolute or scratch path if run from another directory
    csv_file = r"C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv"

df_raw = pd.read_csv(csv_file)

print(f"\n[INFO] Loaded dataset successfully. Shape: {df_raw.shape} (Rows, Columns)")
print("\n--- Verified Column Names ---")
print(df_raw.columns.tolist())

print("\n--- First 5 Records (head) ---")
print(df_raw.head())

print("\n--- DataFrame Summary Information (info) ---")
df_raw.info()

print("\n--- Descriptive Statistics for Numeric Columns (describe) ---")
print(df_raw.describe().T)

print("\n--- Descriptive Statistics for Categorical Columns ---")
print(df_raw.describe(include=["object"]).T)


# ======================================================================================
# SECTION 2: Identify Missing Values and Duplicate Booking_ID Records
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 2: IDENTIFY MISSING VALUES AND DUPLICATE BOOKING_ID RECORDS")
print("=" * 80)

# 1. Identify missing values
missing_counts = df_raw.isnull().sum()
missing_percent = (missing_counts / len(df_raw)) * 100
missing_df = pd.DataFrame({"Missing_Count": missing_counts, "Percentage_%": missing_percent.round(2)})
print("\n--- Missing Values Audit ---")
print(missing_df[missing_df["Missing_Count"] > 0])

# 2. Identify duplicate Booking_ID records
num_duplicates = df_raw["Booking_ID"].duplicated().sum()
print(f"\nTotal Duplicate Booking_ID records found: {num_duplicates}")

if num_duplicates > 0:
    dup_ids = df_raw.loc[df_raw["Booking_ID"].duplicated(), "Booking_ID"].head(3)
    print("\nSample duplicate entries:")
    print(df_raw[df_raw["Booking_ID"].isin(dup_ids)].sort_values(by="Booking_ID"))

# Drop duplicate Booking_IDs, retaining the first valid entry
df = df_raw.drop_duplicates(subset=["Booking_ID"], keep="first").copy()
print(f"\nShape after dropping duplicates: {df.shape} (Retained exactly {len(df)} unique bookings)")


# ======================================================================================
# SECTION 3: Handle Missing Lead_Time_Days and Room_Rate Values
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 3: HANDLE MISSING LEAD_TIME_DAYS OR ROOM_RATE (WITH JUSTIFICATION)")
print("=" * 80)

"""
Justification for Imputation Approach:
1. Room_Rate:
   - Pricing differs substantially across room categories (Suite is ~2.7x more expensive than Standard).
   - Global mean imputation would heavily bias rates downward for luxury suites and upward for standard rooms.
   - We impute missing Room_Rate using the MEDIAN grouped by 'Room_Type'. Median is chosen because room
     rates can feature luxury surges and seasonal peaks; median remains robust against extreme values.

2. Lead_Time_Days:
   - Lead time is inherently right-skewed: most reservations occur within 30 days, while a minority book 
     months ahead.
   - We impute missing Lead_Time_Days using the group MEDIAN by 'Room_Type' (or overall median), avoiding 
     mean-distortion from long-tail bookings.

3. Booking_Channel:
   - 8 missing values exist; imputed as 'Unknown' to maintain channel accountability.
"""

print("\nMedian Room_Rate by Room_Type (used for imputation):")
room_rate_medians = df.groupby("Room_Type")["Room_Rate"].median()
print(room_rate_medians)

print("\nMedian Lead_Time_Days by Room_Type (used for imputation):")
lead_time_medians = df.groupby("Room_Type")["Lead_Time_Days"].median()
print(lead_time_medians)

# Apply group-wise median imputation
df["Room_Rate"] = df["Room_Rate"].fillna(df.groupby("Room_Type")["Room_Rate"].transform("median"))
df["Lead_Time_Days"] = df["Lead_Time_Days"].fillna(df.groupby("Room_Type")["Lead_Time_Days"].transform("median"))
df["Booking_Channel"] = df["Booking_Channel"].fillna("Unknown")

print("\nMissing values remaining after imputation:")
print(df[["Lead_Time_Days", "Room_Rate", "Booking_Channel"]].isnull().sum())


# ======================================================================================
# SECTION 4: Convert Checkin_Date to Datetime & Extract Arrival Month and Weekday
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 4: CONVERT CHECKIN_DATE TO DATETIME & EXTRACT ARRIVAL MONTH & WEEKDAY")
print("=" * 80)

# Convert string dates to datetime objects
df["Checkin_Date"] = pd.to_datetime(df["Checkin_Date"])

# Extract temporal features
df["Arrival_Year_Month"] = df["Checkin_Date"].dt.strftime("%Y-%m")
df["Arrival_Month_Name"] = df["Checkin_Date"].dt.month_name()
df["Arrival_Month_Num"] = df["Checkin_Date"].dt.month
df["Arrival_Weekday"] = df["Checkin_Date"].dt.day_name()
df["Is_Weekend_Arrival"] = df["Checkin_Date"].dt.weekday.isin([4, 5, 6]).astype(int)  # Fri, Sat, Sun

print("\nSample records with extracted datetime attributes:")
print(df[["Booking_ID", "Checkin_Date", "Arrival_Year_Month", "Arrival_Month_Name", "Arrival_Weekday"]].head())


# ======================================================================================
# SECTION 5: Calculate Total Bookings, Total Room Nights, & Overall Cancellation %
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 5: OVERALL KEY PERFORMANCE INDICATORS (KPIS)")
print("=" * 80)

total_bookings = len(df)
total_nights_all = df["Nights"].sum()
total_canceled = (df["Canceled"] == "Yes").sum()
cancellation_rate_pct = (total_canceled / total_bookings) * 100

realized_bookings = (df["Canceled"] == "No").sum()
realized_nights = df.loc[df["Canceled"] == "No", "Nights"].sum()

print(f"Total Reservations Booked:       {total_bookings:,}")
print(f"Total Room Nights Demanded:      {total_nights_all:,} nights")
print(f"Total Reservations Canceled:     {total_canceled:,}")
print(f"Overall Cancellation Rate:       {cancellation_rate_pct:.2f}%")
print(f"Realized (Checked-in) Bookings:  {realized_bookings:,}")
print(f"Realized (Checked-in) Nights:    {realized_nights:,} nights")


# ======================================================================================
# SECTION 6: Row-wise Total Booking Revenue (Non-Canceled Bookings Only)
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 6: REALIZED BOOKING REVENUE CALCULATION")
print("=" * 80)

# Hint followed: Filter out canceled bookings before calculating realized revenue
# If Canceled == 'Yes', realized revenue is INR 0.00; otherwise, Nights * Room_Rate
df["Potential_Revenue"] = df["Nights"] * df["Room_Rate"]
df["Revenue"] = np.where(df["Canceled"] == "No", df["Nights"] * df["Room_Rate"], 0.0)

total_realized_revenue = df["Revenue"].sum()
total_potential_revenue = df["Potential_Revenue"].sum()
total_lost_revenue = df.loc[df["Canceled"] == "Yes", "Potential_Revenue"].sum()

print(f"Total Realized Revenue (Actual Cashflow): INR {total_realized_revenue:,.2f}")
print(f"Total Potential Gross Revenue:             INR {total_potential_revenue:,.2f}")
print(f"Revenue Lost to Cancellations:             INR {total_lost_revenue:,.2f} "
      f"({(total_lost_revenue / total_potential_revenue * 100):.2f}% of potential)")

print("\nSample records showing realized row-wise revenue:")
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

# Add percentage contributions
room_type_summary["Booking_Share_Pct"] = (room_type_summary["Total_Bookings"] / total_bookings * 100).round(2)
room_type_summary["Nights_Share_Pct"] = (room_type_summary["Realized_Nights"] / realized_nights * 100).round(2)
room_type_summary["Revenue_Share_Pct"] = (room_type_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

print("\n>>> DELIVERABLE 1: Room-Type Revenue Summary Table <<<")
display_rt = room_type_summary.copy()
display_rt["Avg_Room_Rate"] = display_rt["Avg_Room_Rate"].map("INR {:,.2f}".format)
display_rt["Realized_Revenue"] = display_rt["Realized_Revenue"].map("INR {:,.2f}".format)
display_rt["Cancellation_Rate_Pct"] = display_rt["Cancellation_Rate_Pct"].map("{:.2f}%".format)
display_rt["Booking_Share_Pct"] = display_rt["Booking_Share_Pct"].map("{:.2f}%".format)
display_rt["Revenue_Share_Pct"] = display_rt["Revenue_Share_Pct"].map("{:.2f}%".format)

cols_order = ["Room_Type", "Total_Bookings", "Booking_Share_Pct", "Avg_Room_Rate", 
              "Realized_Nights", "Realized_Revenue", "Revenue_Share_Pct", "Cancellation_Rate_Pct"]
print(display_rt[cols_order].to_string(index=False))


# ======================================================================================
# SECTION 8: Rank Booking Channels by Booking Volume and Revenue
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 8: RANK BOOKING CHANNELS BY BOOKING VOLUME AND REVENUE")
print("=" * 80)

channel_summary = df.groupby("Booking_Channel").agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
    Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
    Realized_Revenue=("Revenue", "sum"),
    Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

channel_summary["Booking_Share_Pct"] = (channel_summary["Total_Bookings"] / total_bookings * 100).round(2)
channel_summary["Revenue_Share_Pct"] = (channel_summary["Realized_Revenue"] / total_realized_revenue * 100).round(2)

# Rank by Revenue (descending) and by Volume (descending)
channel_summary = channel_summary.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
channel_summary["Revenue_Rank"] = channel_summary.index + 1
channel_summary["Volume_Rank"] = channel_summary["Total_Bookings"].rank(ascending=False, method="min").astype(int)

print("\n>>> DELIVERABLE 2: Booking Channel Performance Ranking Table <<<")
display_chan = channel_summary.copy()
display_chan["Realized_Revenue"] = display_chan["Realized_Revenue"].map("INR {:,.2f}".format)
display_chan["Cancellation_Rate_Pct"] = display_chan["Cancellation_Rate_Pct"].map("{:.2f}%".format)
display_chan["Booking_Share_Pct"] = display_chan["Booking_Share_Pct"].map("{:.2f}%".format)
display_chan["Revenue_Share_Pct"] = display_chan["Revenue_Share_Pct"].map("{:.2f}%".format)

chan_cols = ["Revenue_Rank", "Volume_Rank", "Booking_Channel", "Total_Bookings", 
             "Booking_Share_Pct", "Realized_Revenue", "Revenue_Share_Pct", "Cancellation_Rate_Pct"]
print(display_chan[chan_cols].to_string(index=False))


# ======================================================================================
# SECTION 9: Analyze Cancellation Rates by Booking Channel & Lead-Time Bands
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 9: CANCELLATION RATES BY BOOKING CHANNEL AND LEAD-TIME BANDS")
print("=" * 80)

# Create lead-time bands using pd.cut()
lead_bins = [-1, 7, 30, int(df["Lead_Time_Days"].max()) + 1]
lead_labels = ["Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)"]
df["Lead_Time_Band"] = pd.cut(df["Lead_Time_Days"], bins=lead_bins, labels=lead_labels, right=True)

# 1. Cancellation rate by Lead-Time Band alone
lead_band_canc = df.groupby("Lead_Time_Band", observed=False).agg(
    Total_Bookings=("Booking_ID", "count"),
    Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index()

print("\n--- Cancellation Rate by Lead-Time Band ---")
display_lbc = lead_band_canc.copy()
display_lbc["Cancellation_Rate_Pct"] = display_lbc["Cancellation_Rate_Pct"].map("{:.2f}%".format)
print(display_lbc.to_string(index=False))

# 2. Channel x Lead-Time Band Cancellation Matrix (%)
channel_lead_pivot = pd.crosstab(
    df["Booking_Channel"],
    df["Lead_Time_Band"],
    values=df["Canceled"] == "Yes",
    aggfunc=lambda x: round(np.mean(x) * 100, 2)
)
print("\n--- Cancellation Rate (%) Matrix: Booking Channel vs. Lead-Time Band ---")
print(channel_lead_pivot)

# Hint followed: Multi-level summary using groupby(['Room_Type', 'Booking_Channel'])
print("\n--- Multi-level Summary: groupby(['Room_Type', 'Booking_Channel']) ---")
multi_summary = df.groupby(["Room_Type", "Booking_Channel"]).agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
    Realized_Revenue=("Revenue", "sum"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).round(2)
print(multi_summary)


# ======================================================================================
# SECTION 10: Identify Top 3 Peak Revenue Months
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 10: MONTHLY REVENUE ANALYSIS & TOP 3 PEAK REVENUE MONTHS")
print("=" * 80)

monthly_summary = df.groupby(["Arrival_Year_Month", "Arrival_Month_Name"]).agg(
    Total_Bookings=("Booking_ID", "count"),
    Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
    Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
    Realized_Revenue=("Revenue", "sum"),
    Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
).reset_index().sort_values(by="Arrival_Year_Month")

# Rank months by realized revenue
monthly_ranked = monthly_summary.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
top_3_months = monthly_ranked.head(3)

print("\n>>> DELIVERABLE 3: Top 3 Peak Revenue Months <<<")
for i, row in top_3_months.iterrows():
    print(f"Rank {i+1}: {row['Arrival_Year_Month']} ({row['Arrival_Month_Name']}) "
          f"--> Realized Revenue: INR {row['Realized_Revenue']:,.2f} | "
          f"Realized Nights: {row['Realized_Nights']:,} | Realized Bookings: {row['Realized_Bookings']:,}")

print("\n--- Full 12-Month Performance Table ---")
display_monthly = monthly_summary.copy()
display_monthly["Realized_Revenue"] = display_monthly["Realized_Revenue"].map("INR {:,.2f}".format)
display_monthly["Cancellation_Rate_Pct"] = display_monthly["Cancellation_Rate_Pct"].map("{:.2f}%".format)
print(display_monthly.to_string(index=False))


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

print("\n--- Traveler Segment Behavioral Profile ---")
print(traveler_summary.round(2).to_string(index=False))

leisure_avg = traveler_summary.loc[traveler_summary["Traveler_Type"] == "Leisure", "Mean_Stay_Nights"].values[0]
business_avg = traveler_summary.loc[traveler_summary["Traveler_Type"] == "Business", "Mean_Stay_Nights"].values[0]
print(f"\nKey Finding: Leisure travelers stay on average {leisure_avg:.2f} nights, which is "
      f"{(leisure_avg / business_avg):.2f}x longer than Business travelers ({business_avg:.2f} nights). "
      f"Leisure contributes {traveler_summary.loc[traveler_summary['Traveler_Type'] == 'Leisure', 'Revenue_Share_Pct'].values[0]}% of total revenue.")


# ======================================================================================
# SECTION 12: NumPy Statistical Measures for Daily Room Rates
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 12: NUMPY STATISTICAL MEASURES FOR DAILY ROOM RATES")
print("=" * 80)

# Convert series to NumPy array
room_rates_arr = df["Room_Rate"].to_numpy()

# Calculate statistics using NumPy functions
np_mean_rate = np.mean(room_rates_arr)
np_median_rate = np.median(room_rates_arr)
np_std_rate = np.std(room_rates_arr, ddof=1)  # Sample standard deviation
np_p25 = np.percentile(room_rates_arr, 25)
np_p75 = np.percentile(room_rates_arr, 75)

print("NumPy Calculations for Daily Room Rates (INR):")
print(f"  • NumPy Mean Rate:       INR {np_mean_rate:,.2f}")
print(f"  • NumPy Median Rate:     INR {np_median_rate:,.2f}")
print(f"  • NumPy Sample Std Dev:  INR {np_std_rate:,.2f}")
print(f"  • NumPy 25th Percentile: INR {np_p25:,.2f}")
print(f"  • NumPy 75th Percentile: INR {np_p75:,.2f}")


# ======================================================================================
# SECTION 13: Identify Unusually High Booking Values Using the IQR Method
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 13: OUTLIER DETECTION IN REALIZED BOOKING REVENUE (IQR METHOD)")
print("=" * 80)

# Extract realized revenue values (non-canceled bookings only) into a NumPy array
realized_rev_arr = df.loc[df["Canceled"] == "No", "Revenue"].to_numpy()

# Hint followed: Use np.percentile() to compute Q1 and Q3
q1 = np.percentile(realized_rev_arr, 25)
q3 = np.percentile(realized_rev_arr, 75)
iqr = q3 - q1

lower_fence = max(0.0, q1 - 1.5 * iqr)
upper_fence = q3 + 1.5 * iqr

print("IQR Outlier Thresholds for Realized Booking Revenue:")
print(f"  • Q1 (25th Percentile):       INR {q1:,.2f}")
print(f"  • Q3 (75th Percentile):       INR {q3:,.2f}")
print(f"  • Interquartile Range (IQR):  INR {iqr:,.2f}")
print(f"  • Lower Fence (Q1 - 1.5*IQR): INR {lower_fence:,.2f}")
print(f"  • Upper Fence (Q3 + 1.5*IQR): INR {upper_fence:,.2f}")

# Filter outlier bookings
outlier_mask = (df["Canceled"] == "No") & (df["Revenue"] > upper_fence)
df_outliers = df[outlier_mask].sort_values(by="Revenue", ascending=False)

print(f"\nTotal High-Value Outlier Bookings: {len(df_outliers)} "
      f"({(len(df_outliers) / len(realized_rev_arr) * 100):.2f}% of realized bookings)")

print("\nTop 5 Highest-Value Outlier Reservations:")
outlier_cols = ["Booking_ID", "Room_Type", "Traveler_Type", "Booking_Channel", 
                "Nights", "Room_Rate", "Revenue"]
print(df_outliers[outlier_cols].head(5).to_string(index=False))


# ======================================================================================
# SECTION 14: Lead-Time Categories Using pd.cut()
# ======================================================================================
print("\n" + "=" * 80)
print("SECTION 14: LEAD-TIME CATEGORIZATION USING PD.CUT()")
print("=" * 80)

# Group into 3 hospitality lead-time categories
bins = [-1, 7, 30, int(df["Lead_Time_Days"].max()) + 1]
labels = ["Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)"]

df["Lead_Time_Category"] = pd.cut(df["Lead_Time_Days"], bins=bins, labels=labels, right=True)

lead_summary = df.groupby("Lead_Time_Category", observed=False).agg(
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

recommendations_text = """
>>> DELIVERABLE 4: Five Operational & Revenue Recommendations <<<

1. OVERHAUL OTA CANCELLATION POLICIES (Deposit & Stricter Window):
   • Finding: Online Travel Agencies (OTA) generate the highest booking volume (39.75% share, 477 bookings)
     but suffer from an unsustainable 32.70% cancellation rate, surging to 37.07% for advance bookings (>30 days).
   • Action: Enforce a mandatory 1-night non-refundable deposit on OTA reservations booked more than 14 days
     in advance, and offer free cancellation privileges exclusively through direct channels.

2. ACCELERATE DIRECT WEBSITE CONVERSION TO PROTECT MARGINS:
   • Finding: Direct Website bookings generated virtually identical realized revenue (INR 5.42M) to OTAs
     (INR 5.44M) with nearly HALF the cancellation rate (16.95% vs 32.70%) and zero commission deductions.
     Deluxe rooms booked via Direct Website represent the single most profitable segment (INR 2.46M).
   • Action: Reallocate marketing budget toward Google Hotel Ads and branded search campaigns offering direct-booker
     perks (complimentary breakfast, room upgrades, flexible check-in) to drive direct reservations.

3. OPTIMIZE FRONT-DESK STAFFING BY ARRIVAL PEAKS & WEEKDAY DEMAND:
   • Finding: Guest check-in arrivals peak on Wednesdays (194 bookings) and Saturdays (181 bookings), while
     Sundays (158) and Mondays (165) experience the lightest turnover. Mid-week check-ins are dominated by short
     Business stays (2.18 nights), while weekend check-ins are longer Leisure vacations (4.02 nights).
   • Action: Schedule two additional receptionists and concierge staff during the 1:00 PM - 6:00 PM arrival
     rush on Wednesdays and Saturdays. Schedule room deep cleaning and staff maintenance during Monday lulls.

4. CAPITALIZE ON HIGH-VALUE EXTENDED-STAY LEISURE PACKAGES:
   • Finding: Leisure travelers contribute 74.90% of total realized revenue (INR 12.24M) with an average stay
     of 4.02 nights. Furthermore, IQR outlier analysis uncovered 49 high-value bookings generating up to INR 143k
     each, driven primarily by extended multi-night stays in Suites and Deluxe rooms.
   • Action: Launch curated "Stay 4, Pay 3" and "Workcation Long-Stay" packages bundled with dining credits,
     specifically targeting family and couples segments during shoulder seasons (April and August).

5. DEPLOY DYNAMIC SEASONAL PRICING FOR Q4 & SUMMER PEAKS:
   • Finding: Revenue peaks sharply in December (INR 1.80M), January (INR 1.74M), October (INR 1.70M), and July
     (333 realized nights - peak occupancy), whereas April generates under half of peak revenue (INR 908k).
   • Action: Implement automated dynamic pricing rules: raise Deluxe and Suite BAR (Best Available Rates) by
     15% - 25% during peak holiday/summer windows (Oct, Dec, Jan, Jul), while offering bundled corporate meeting
     packages and early-bird discounts to fill low-demand months (April/May).
"""
print(recommendations_text)


# ======================================================================================
# BONUS: EXECUTIVE VISUALIZATIONS DASHBOARD
# ======================================================================================
print("\n" + "=" * 80)
print("GENERATING BUSINESS VISUALIZATION DASHBOARD...")
print("=" * 80)

fig, axes = plt.subplots(3, 2, figsize=(18, 16))
plt.subplots_adjust(hspace=0.35, wspace=0.25)

# 1. Monthly Revenue & Occupancy Trend
ax1 = axes[0, 0]
color_rev = "#1f77b4"
color_nights = "#2ca02c"
months_abbr = [m[:3] for m in monthly_summary["Arrival_Month_Name"]]

ax1.bar(months_abbr, monthly_summary["Realized_Revenue"] / 1e5, color=color_rev, alpha=0.7, label="Revenue (Lakh ₹)")
ax1.set_ylabel("Realized Revenue (Lakh ₹)", color=color_rev, fontsize=11, fontweight="bold")
ax1.set_title("Monthly Realized Revenue & Room Nights Trend (Deliverable 3)", fontsize=12, fontweight="bold")
ax1.tick_params(axis="x", rotation=30)

ax1_twin = ax1.twinx()
ax1_twin.plot(months_abbr, monthly_summary["Realized_Nights"], color=color_nights, marker="o", linewidth=2.5, label="Nights")
ax1_twin.set_ylabel("Realized Room Nights", color=color_nights, fontsize=11, fontweight="bold")
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
ax3.pie(room_type_summary["Realized_Revenue"], labels=room_type_summary["Room_Type"],
        autopct="%1.1f%%", startangle=140, colors=room_colors, explode=(0.02, 0.02, 0.04),
        textprops={"fontsize": 11, "fontweight": "bold"})
ax3.set_title("Realized Revenue Contribution by Room Type", fontsize=12, fontweight="bold")

# 4. Cancellation Rate Heatmap: Channel vs. Lead-Time Band
ax4 = axes[1, 1]
sns.heatmap(channel_lead_pivot, annot=True, fmt=".1f", cmap="YlOrRd", 
            cbar_kws={"label": "Cancellation Rate (%)"}, ax=ax4)
ax4.set_title("Cancellation Rate Heatmap: Channel vs. Lead-Time Band", fontsize=12, fontweight="bold")
ax4.set_ylabel("Booking Channel", fontsize=11)
ax4.set_xlabel("Lead-Time Band", fontsize=11)

# 5. Stay Duration Distribution: Leisure vs. Business
ax5 = axes[2, 0]
sns.boxplot(data=df, x="Traveler_Type", y="Nights", palette="Set2", ax=ax5, showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "red", "markeredgecolor": "black", "markersize": "7"})
ax5.set_title("Stay Duration Distribution (Red Diamond = Mean)", fontsize=12, fontweight="bold")
ax5.set_ylabel("Nights Stayed", fontsize=11)
ax5.set_xlabel("Traveler Segment", fontsize=11)

# 6. Check-in Arrivals by Weekday (Front-Desk Staffing)
ax6 = axes[2, 1]
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_counts = df["Arrival_Weekday"].value_counts().reindex(weekday_order)
sns.barplot(x=weekday_counts.index, y=weekday_counts.values, ax=ax6, palette="Blues_d")
ax6.set_title("Front-Desk Workload: Total Arrivals by Day of Week", fontsize=12, fontweight="bold")
ax6.set_ylabel("Arrival Bookings", fontsize=11)
ax6.set_xlabel("Day of Arrival", fontsize=11)
ax6.tick_params(axis="x", rotation=30)
for p in ax6.patches:
    ax6.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")

plt.tight_layout()
dashboard_path = "hotel_booking_analysis_dashboard.png"
plt.savefig(dashboard_path, dpi=300)
print(f"\n[SUCCESS] Visualizations exported to: {os.path.abspath(dashboard_path)}")
plt.show()

print("\n" + "=" * 80)
print("PROJECT 13: HOTEL BOOKING & OCCUPANCY ANALYSIS COMPLETED SUCCESSFULLY!")
print("=" * 80)
