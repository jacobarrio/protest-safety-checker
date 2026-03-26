#!/usr/bin/env python3
"""
Merge PIRC incident data into the main protest_data_oversight.csv.
Handles deduplication and maintains consistent format.
"""

import pandas as pd
import os
from datetime import datetime


def merge_pirc_data():
    main_csv = "protest_data_oversight.csv"
    pirc_csv = "data/pirc_incidents.csv"

    if not os.path.exists(pirc_csv):
        print("⚠️  No PIRC incidents file found. Run scrape_pirc.py first.")
        return

    print("📦 Merging PIRC data into main dataset...")

    main_df = pd.read_csv(main_csv)
    pirc_df = pd.read_csv(pirc_csv)

    print(f"  Main dataset: {len(main_df)} rows")
    print(f"  PIRC incidents: {len(pirc_df)} rows")

    # Tag source for tracking
    if "source" not in main_df.columns:
        main_df["source"] = "oversight_dashboard"
    pirc_df["source"] = "pirc_hotline"

    # Merge
    merged = pd.concat([main_df, pirc_df], ignore_index=True)

    # Deduplicate on key columns (excluding source)
    key_cols = ["date", "location", "title"]
    before_dedup = len(merged)
    merged = merged.drop_duplicates(subset=key_cols, keep="first")
    dupes_removed = before_dedup - len(merged)

    # Sort by date descending
    merged["date_parsed"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.sort_values("date_parsed", ascending=False).drop(columns=["date_parsed"])

    # Save (without source column in main CSV for backward compat)
    output_df = merged.drop(columns=["source"], errors="ignore")
    output_df.to_csv(main_csv, index=False)

    # Save source-tagged version separately
    merged.to_csv("data/merged_with_sources.csv", index=False)

    print(f"\n✅ Merged dataset: {len(merged)} rows")
    print(f"  Duplicates removed: {dupes_removed}")
    print(f"  Saved → {main_csv}")
    print(f"  Source-tagged version → data/merged_with_sources.csv")

    # Show freshness after merge
    dates = pd.to_datetime(output_df["date"], errors="coerce").dropna()
    if not dates.empty:
        latest = dates.max()
        days_old = (pd.Timestamp.now() - latest).days
        print(f"\n📊 Latest incident date: {latest.strftime('%Y-%m-%d')}")
        print(f"  Days since latest: {days_old}")
        if days_old <= 14:
            print("  Status: ✅ FRESH")
        elif days_old <= 30:
            print("  Status: ⚠️  AGING")
        else:
            print("  Status: ❌ STALE")


if __name__ == "__main__":
    merge_pirc_data()
