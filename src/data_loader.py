"""
Module: data_loader.py
Description: Ingests hotel reservation data, validates schema, audits nulls and duplicates.
"""

import os
import pandas as pd


def get_dataset_path(filename="13_hotel_bookings.csv"):
    """
    Dynamically resolves the path to the CSV file across common directory structures.
    """
    candidate_paths = [
        filename,
        os.path.join("data", "raw", filename),
        os.path.join("data", filename),
        os.path.join("..", "data", "raw", filename),
        os.path.join("..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", "raw", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", filename),
        r"C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\data\raw\13_hotel_bookings.csv",
        r"C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    raise FileNotFoundError(f"Dataset '{filename}' could not be located in any standard search path.")


def load_and_inspect_data(filepath=None):
    """
    Loads dataset and prints structural inspection: head, shape, info, and describe.
    """
    if filepath is None:
        filepath = get_dataset_path()
        
    print(f"\n[DATA LOADER] Ingesting dataset from: {filepath}")
    df_raw = pd.read_csv(filepath)
    
    print(f"[DATA LOADER] Raw Record Count: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns")
    print(f"[DATA LOADER] Column Schema: {df_raw.columns.tolist()}")
    
    return df_raw


def audit_quality(df):
    """
    Audits missing values and identifies duplicate Booking_IDs.
    """
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    missing_summary = pd.DataFrame({"Missing_Count": null_counts, "Percentage_%": null_pct})
    missing_fields = missing_summary[missing_summary["Missing_Count"] > 0]
    
    dup_count = df["Booking_ID"].duplicated().sum()
    
    print("\n--- Data Quality Audit ---")
    print(f"Duplicate Booking_ID Records: {dup_count}")
    if not missing_fields.empty:
        print("Missing Values Summary:")
        print(missing_fields)
    else:
        print("No missing values detected.")
        
    return missing_summary, dup_count


if __name__ == "__main__":
    df = load_and_inspect_data()
    audit_quality(df)
