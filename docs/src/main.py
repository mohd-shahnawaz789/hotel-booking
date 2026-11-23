"""
Module: main.py
Description: End-to-end execution pipeline for Project 13: Hotel Booking & Occupancy Analysis.
"""

import sys
import os

# Ensure current module directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from data_loader import load_and_inspect_data, audit_quality
from cleaner import clean_and_prepare_data
from analysis import (
    compute_overall_kpis,
    analyze_room_types,
    rank_booking_channels,
    analyze_cancellations_by_lead_band,
    identify_peak_months,
    compare_traveler_segments,
    calculate_numpy_metrics,
    detect_revenue_outliers_iqr
)
from visualizer import generate_executive_dashboard


def run_pipeline():
    print("=" * 80)
    print("STARTING PROJECT 13: HOTEL BOOKING & OCCUPANCY ANALYSIS PIPELINE")
    print("=" * 80)

    # 1. Ingestion & Quality Audit
    df_raw = load_and_inspect_data()
    audit_quality(df_raw)

    # 2. Cleansing, Imputation & Feature Engineering
    df = clean_and_prepare_data(df_raw, save_processed=True)

    # 3. Overall KPIs
    kpis = compute_overall_kpis(df)
    print("\n" + "=" * 80)
    print("EXECUTIVE HOSPITALITY KPIS")
    print("=" * 80)
    print(f"Total Reservations Booked:       {kpis['Total_Bookings']:,}")
    print(f"Total Room Nights Demanded:      {kpis['Total_Nights_Demanded']:,}")
    print(f"Realized (Checked-in) Nights:    {kpis['Realized_Nights']:,}")
    print(f"Canceled Reservations:           {kpis['Canceled_Bookings']:,}")
    print(f"Overall Cancellation Rate:       {kpis['Cancellation_Rate_Pct']:.2f}%")
    print(f"Total Realized Revenue:          INR {kpis['Total_Realized_Revenue']:,.2f}")
    print(f"Revenue Lost to Cancellations:   INR {kpis['Total_Lost_Revenue']:,.2f}")

    # 4. Deliverable 1: Room-Type Revenue Summary
    rt_summary = analyze_room_types(df, kpis["Total_Bookings"], kpis["Total_Realized_Revenue"], kpis["Realized_Nights"])
    print("\n" + "=" * 80)
    print("DELIVERABLE 1: ROOM-TYPE REVENUE SUMMARY TABLE")
    print("=" * 80)
    disp_rt = rt_summary.copy()
    disp_rt["Avg_Room_Rate"] = disp_rt["Avg_Room_Rate"].map("INR {:,.2f}".format)
    disp_rt["Realized_Revenue"] = disp_rt["Realized_Revenue"].map("INR {:,.2f}".format)
    disp_rt["Cancellation_Rate_Pct"] = disp_rt["Cancellation_Rate_Pct"].map("{:.2f}%".format)
    disp_rt["Booking_Share_Pct"] = disp_rt["Booking_Share_Pct"].map("{:.2f}%".format)
    disp_rt["Revenue_Share_Pct"] = disp_rt["Revenue_Share_Pct"].map("{:.2f}%".format)
    cols = ["Room_Type", "Total_Bookings", "Booking_Share_Pct", "Avg_Room_Rate", 
            "Realized_Nights", "Realized_Revenue", "Revenue_Share_Pct", "Cancellation_Rate_Pct"]
    print(disp_rt[cols].to_string(index=False))

    # 5. Deliverable 2: Booking Channel Performance Ranking
    chan_summary = rank_booking_channels(df, kpis["Total_Bookings"], kpis["Total_Realized_Revenue"])
    print("\n" + "=" * 80)
    print("DELIVERABLE 2: BOOKING CHANNEL PERFORMANCE RANKING TABLE")
    print("=" * 80)
    disp_chan = chan_summary.copy()
    disp_chan["Realized_Revenue"] = disp_chan["Realized_Revenue"].map("INR {:,.2f}".format)
    disp_chan["Cancellation_Rate_Pct"] = disp_chan["Cancellation_Rate_Pct"].map("{:.2f}%".format)
    disp_chan["Booking_Share_Pct"] = disp_chan["Booking_Share_Pct"].map("{:.2f}%".format)
    disp_chan["Revenue_Share_Pct"] = disp_chan["Revenue_Share_Pct"].map("{:.2f}%".format)
    c_cols = ["Revenue_Rank", "Volume_Rank", "Booking_Channel", "Total_Bookings", 
              "Booking_Share_Pct", "Realized_Revenue", "Revenue_Share_Pct", "Cancellation_Rate_Pct"]
    print(disp_chan[c_cols].to_string(index=False))

    # 6. Cancellation by Lead-Time Bands & Multi-level Summary
    lead_summary, channel_lead_pivot, multi_summary = analyze_cancellations_by_lead_band(df)
    print("\n" + "=" * 80)
    print("CANCELLATION RATE (%) MATRIX: BOOKING CHANNEL VS. LEAD-TIME BAND")
    print("=" * 80)
    print(channel_lead_pivot)

    # 7. Deliverable 3: Top 3 Peak Months
    monthly_summary, top_3_months = identify_peak_months(df)
    print("\n" + "=" * 80)
    print("DELIVERABLE 3: TOP 3 PEAK REVENUE MONTHS")
    print("=" * 80)
    for idx, r in top_3_months.iterrows():
        print(f"Rank {idx+1}: {r['Arrival_Year_Month']} ({r['Arrival_Month_Name']}) "
              f"--> Realized Revenue: INR {r['Realized_Revenue']:,.2f} | Realized Nights: {r['Realized_Nights']:,}")

    # 8. Traveler Type Comparison
    traveler_summary = compare_traveler_segments(df, kpis["Total_Realized_Revenue"])
    print("\n" + "=" * 80)
    print("TRAVELER SEGMENT COMPARISON: LEISURE VS. BUSINESS")
    print("=" * 80)
    print(traveler_summary.round(2).to_string(index=False))

    # 9. NumPy Statistical Measures
    np_stats = calculate_numpy_metrics(df)
    print("\n" + "=" * 80)
    print("NUMPY STATISTICAL MEASURES FOR DAILY ROOM RATES (INR)")
    print("=" * 80)
    for k, v in np_stats.items():
        print(f"  • {k:15}: INR {v:,.2f}")

    # 10. Outlier Detection via IQR
    outliers = detect_revenue_outliers_iqr(df)
    print("\n" + "=" * 80)
    print("REVENUE OUTLIER DETECTION (IQR METHOD)")
    print("=" * 80)
    print(f"Q1: INR {outliers['Q1']:,.2f} | Q3: INR {outliers['Q3']:,.2f} | IQR: INR {outliers['IQR']:,.2f}")
    print(f"Upper Fence: INR {outliers['Upper_Fence']:,.2f} | Outliers Count: {outliers['Outlier_Count']}")

    # 11. Visualizations
    generate_executive_dashboard(df, rt_summary, chan_summary, monthly_summary, channel_lead_pivot)

    # 12. Deliverable 4: 5 Recommendations
    print("\n" + "=" * 80)
    print("DELIVERABLE 4: FIVE OPERATIONAL & REVENUE RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. Overhaul OTA Cancellation Policy: Mandate 1-night deposit for advance bookings (>14 days).
2. Accelerate Direct Website Booking Conversion: Offer free breakfast & room upgrades for direct bookers.
3. Align Front-Desk Staffing: Increase staffing on Wednesdays (194 arrivals) and Saturdays (181 arrivals).
4. Market Extended Stay Vacation Deals: Leverage Leisure guests' 4.02-night average stay with 'Stay 4, Pay 3' offers.
5. Deploy Dynamic Seasonal Pricing: Surge rates by 15-20% during Q4 and July; offer meeting bundles in April.
""")
    print("=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
