"""
Module: cleaner.py
Description: Cleans raw booking records, performs justified median imputation, and generates engineered features.
"""

import os
import numpy as np
import pandas as pd


def clean_and_prepare_data(df_raw, save_processed=True):
    """
    Cleans raw booking records:
    1. Removes duplicate Booking_IDs.
    2. Imputes missing Room_Rate by Room_Type median.
    3. Imputes missing Lead_Time_Days by Room_Type median.
    4. Imputes missing Booking_Channel with 'Unknown'.
    5. Converts Checkin_Date to datetime and extracts arrival period & weekday.
    6. Creates lead-time operational categories.
    7. Computes row-wise realized revenue (Nights * Room_Rate) for non-canceled bookings only.
    """
    print("\n[CLEANER] Starting data cleansing and feature engineering...")
    
    # 1. Deduplicate
    initial_len = len(df_raw)
    df = df_raw.drop_duplicates(subset=["Booking_ID"], keep="first").copy()
    dropped_dups = initial_len - len(df)
    print(f"[CLEANER] Purged {dropped_dups} duplicate Booking_ID records. Retained {len(df):,} unique rows.")
    
    # 2. Impute Room_Rate using group-wise median
    print("[CLEANER] Imputing missing Room_Rate values using Room_Type median...")
    df["Room_Rate"] = df["Room_Rate"].fillna(df.groupby("Room_Type")["Room_Rate"].transform("median"))
    
    # 3. Impute Lead_Time_Days using group-wise median
    print("[CLEANER] Imputing missing Lead_Time_Days using Room_Type median...")
    df["Lead_Time_Days"] = df["Lead_Time_Days"].fillna(df.groupby("Room_Type")["Lead_Time_Days"].transform("median"))
    
    # 4. Impute Booking_Channel
    df["Booking_Channel"] = df["Booking_Channel"].fillna("Unknown")
    
    # 5. Datetime features
    print("[CLEANER] Extracting temporal check-in features...")
    df["Checkin_Date"] = pd.to_datetime(df["Checkin_Date"])
    df["Arrival_Year_Month"] = df["Checkin_Date"].dt.strftime("%Y-%m")
    df["Arrival_Month_Name"] = df["Checkin_Date"].dt.month_name()
    df["Arrival_Month_Num"] = df["Checkin_Date"].dt.month
    df["Arrival_Weekday"] = df["Checkin_Date"].dt.day_name()
    df["Is_Weekend_Arrival"] = df["Checkin_Date"].dt.weekday.isin([4, 5, 6]).astype(int)  # Fri, Sat, Sun
    
    # 6. Lead-time bands
    lead_bins = [-1, 7, 30, int(df["Lead_Time_Days"].max()) + 1]
    lead_labels = ["Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)"]
    df["Lead_Time_Band"] = pd.cut(df["Lead_Time_Days"], bins=lead_bins, labels=lead_labels, right=True)
    
    # 7. Realized revenue (non-canceled only; 0 for canceled)
    df["Potential_Revenue"] = df["Nights"] * df["Room_Rate"]
    df["Revenue"] = np.where(df["Canceled"] == "No", df["Nights"] * df["Room_Rate"], 0.0)
    
    print(f"[CLEANER] Data cleaning completed. Final cleansed dataset shape: {df.shape}")
    
    # Save processed dataset
    if save_processed:
        candidate_dirs = [
            os.path.join("data", "processed"),
            os.path.join("..", "data", "processed"),
            os.path.join(os.path.dirname(__file__), "..", "data", "processed"),
            r"C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\data\processed"
        ]
        target_dir = candidate_dirs[0]
        for cd in candidate_dirs:
            if os.path.exists(cd) or os.path.exists(os.path.dirname(cd)):
                target_dir = cd
                break
        os.makedirs(target_dir, exist_ok=True)
        out_path = os.path.join(target_dir, "hotel_bookings_cleaned.csv")
        df.to_csv(out_path, index=False)
        print(f"[CLEANER] Cleaned dataset saved to: {os.path.abspath(out_path)}")
        
    return df


if __name__ == "__main__":
    from data_loader import load_and_inspect_data
    df_raw = load_and_inspect_data()
    df_clean = clean_and_prepare_data(df_raw)
