"""
Module: analysis.py
Description: Computes KPIs, room-type and channel summaries, IQR outliers, NumPy metrics, and seasonality.
"""

import numpy as np
import pandas as pd


def compute_overall_kpis(df):
    """
    Computes overall hotel operations KPIs.
    """
    total_bookings = len(df)
    total_nights_demanded = int(df["Nights"].sum())
    total_canceled = int((df["Canceled"] == "Yes").sum())
    cancellation_rate_pct = (total_canceled / total_bookings) * 100
    realized_bookings = int((df["Canceled"] == "No").sum())
    realized_nights = int(df.loc[df["Canceled"] == "No", "Nights"].sum())
    total_realized_revenue = float(df["Revenue"].sum())
    total_potential_revenue = float(df["Potential_Revenue"].sum())
    total_lost_revenue = float(df.loc[df["Canceled"] == "Yes", "Potential_Revenue"].sum())
    
    kpis = {
        "Total_Bookings": total_bookings,
        "Total_Nights_Demanded": total_nights_demanded,
        "Realized_Nights": realized_nights,
        "Canceled_Bookings": total_canceled,
        "Cancellation_Rate_Pct": cancellation_rate_pct,
        "Realized_Bookings": realized_bookings,
        "Total_Realized_Revenue": total_realized_revenue,
        "Total_Potential_Revenue": total_potential_revenue,
        "Total_Lost_Revenue": total_lost_revenue
    }
    return kpis


def analyze_room_types(df, total_bookings, total_revenue, realized_nights):
    """
    Evaluates room types by rate, nights, realized revenue, and cancellation (Deliverable 1).
    """
    summary = df.groupby("Room_Type").agg(
        Total_Bookings=("Booking_ID", "count"),
        Avg_Room_Rate=("Room_Rate", "mean"),
        Median_Room_Rate=("Room_Rate", "median"),
        Total_Nights=("Nights", "sum"),
        Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
        Realized_Revenue=("Revenue", "sum"),
        Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).reset_index()
    
    summary["Booking_Share_Pct"] = (summary["Total_Bookings"] / total_bookings * 100).round(2)
    summary["Nights_Share_Pct"] = (summary["Realized_Nights"] / realized_nights * 100).round(2)
    summary["Revenue_Share_Pct"] = (summary["Realized_Revenue"] / total_revenue * 100).round(2)
    
    return summary


def rank_booking_channels(df, total_bookings, total_revenue):
    """
    Ranks booking channels by booking volume and realized revenue (Deliverable 2).
    """
    summary = df.groupby("Booking_Channel").agg(
        Total_Bookings=("Booking_ID", "count"),
        Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
        Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
        Realized_Revenue=("Revenue", "sum"),
        Canceled_Bookings=("Canceled", lambda s: (s == "Yes").sum()),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).reset_index()
    
    summary["Booking_Share_Pct"] = (summary["Total_Bookings"] / total_bookings * 100).round(2)
    summary["Revenue_Share_Pct"] = (summary["Realized_Revenue"] / total_revenue * 100).round(2)
    
    summary = summary.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
    summary["Revenue_Rank"] = summary.index + 1
    summary["Volume_Rank"] = summary["Total_Bookings"].rank(ascending=False, method="min").astype(int)
    
    return summary


def analyze_cancellations_by_lead_band(df):
    """
    Analyzes cancellation rates across lead-time categories and generates the Channel x Band matrix.
    """
    lead_summary = df.groupby("Lead_Time_Band", observed=False).agg(
        Total_Bookings=("Booking_ID", "count"),
        Realized_Revenue=("Revenue", "sum"),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).reset_index()
    
    channel_lead_pivot = pd.crosstab(
        df["Booking_Channel"],
        df["Lead_Time_Band"],
        values=df["Canceled"] == "Yes",
        aggfunc=lambda x: round(np.mean(x) * 100, 2)
    )
    
    multi_level_summary = df.groupby(["Room_Type", "Booking_Channel"]).agg(
        Total_Bookings=("Booking_ID", "count"),
        Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
        Realized_Revenue=("Revenue", "sum"),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).round(2)
    
    return lead_summary, channel_lead_pivot, multi_level_summary


def identify_peak_months(df):
    """
    Identifies top 3 peak revenue months and full monthly performance table (Deliverable 3).
    """
    monthly = df.groupby(["Arrival_Year_Month", "Arrival_Month_Name"]).agg(
        Total_Bookings=("Booking_ID", "count"),
        Realized_Bookings=("Canceled", lambda s: (s == "No").sum()),
        Realized_Nights=("Nights", lambda s: s[df.loc[s.index, "Canceled"] == "No"].sum()),
        Realized_Revenue=("Revenue", "sum"),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).reset_index().sort_values(by="Arrival_Year_Month")
    
    ranked = monthly.sort_values(by="Realized_Revenue", ascending=False).reset_index(drop=True)
    top_3 = ranked.head(3)
    return monthly, top_3


def compare_traveler_segments(df, total_revenue):
    """
    Compares stay duration and revenue contribution for Leisure vs. Business travelers.
    """
    summary = df.groupby("Traveler_Type").agg(
        Total_Bookings=("Booking_ID", "count"),
        Mean_Stay_Nights=("Nights", "mean"),
        Median_Stay_Nights=("Nights", "median"),
        Std_Stay_Nights=("Nights", "std"),
        Realized_Revenue=("Revenue", "sum"),
        Cancellation_Rate_Pct=("Canceled", lambda s: (s == "Yes").mean() * 100)
    ).reset_index()
    
    summary["Revenue_Share_Pct"] = (summary["Realized_Revenue"] / total_revenue * 100).round(2)
    return summary


def calculate_numpy_metrics(df):
    """
    Uses NumPy to calculate mean, median, standard deviation, and percentiles of daily room rates.
    """
    rates = df["Room_Rate"].to_numpy()
    stats = {
        "Mean": float(np.mean(rates)),
        "Median": float(np.median(rates)),
        "Std_Dev": float(np.std(rates, ddof=1)),
        "Min": float(np.min(rates)),
        "Max": float(np.max(rates)),
        "Percentile_25": float(np.percentile(rates, 25)),
        "Percentile_75": float(np.percentile(rates, 75))
    }
    return stats


def detect_revenue_outliers_iqr(df):
    """
    Identifies unusually high booking values using the IQR method on realized booking revenue.
    """
    realized_rev = df.loc[df["Canceled"] == "No", "Revenue"].to_numpy()
    q1 = float(np.percentile(realized_rev, 25))
    q3 = float(np.percentile(realized_rev, 75))
    iqr = q3 - q1
    lower_fence = max(0.0, q1 - 1.5 * iqr)
    upper_fence = q3 + 1.5 * iqr
    
    outliers = df[(df["Canceled"] == "No") & (df["Revenue"] > upper_fence)].sort_values(by="Revenue", ascending=False)
    
    results = {
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower_Fence": lower_fence,
        "Upper_Fence": upper_fence,
        "Outlier_Count": len(outliers),
        "Outlier_Percentage": (len(outliers) / len(realized_rev) * 100),
        "Outliers_DF": outliers
    }
    return results
