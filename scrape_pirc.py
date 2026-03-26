#!/usr/bin/env python3
"""
Scrape PIRC (Portland Immigrant Rights Coalition) weekly updates.
Extracts detention counts, date ranges, locations, and policy signals
from https://pircoregon.org/data-and-updates/weekly-updates/

Output: data/pirc_weekly.csv
"""

import re
import json
import csv
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
from bs4 import BeautifulSoup

INDEX_URL = "https://pircoregon.org/data-and-updates/weekly-updates"
HEADERS = {"User-Agent": "ProtestSafetyChecker/1.0 (research)"}
OUTPUT_CSV = "data/pirc_weekly.csv"
OUTPUT_JSON = "data/pirc_weekly.json"


def fetch_page(url):
    """Fetch a URL and return the text content."""
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except URLError as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return None


def get_weekly_urls():
    """Get all weekly update URLs from the PIRC index page."""
    html = fetch_page(INDEX_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/data-and-updates/weekly-updates/20" in href:
            full_url = href if href.startswith("http") else f"https://pircoregon.org{href}"
            if full_url not in urls:
                urls.append(full_url)
    return urls


def extract_date_from_url(url):
    """Extract date from URL like /2026-3-17 -> 2026-03-17"""
    match = re.search(r"/(\d{4})-(\d{1,2})-(\d{1,2})$", url)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return None


def extract_detention_count(text, week_date=None):
    """
    Parse detention count from PIRC's 'The Data' section.
    week_date: YYYY-MM-DD from the URL to infer correct year.
    """
    confirmed = 0
    unconfirmed = 0
    date_start = None
    date_end = None

    # "No confirmed detentions" pattern
    if re.search(r"no confirmed detentions", text, re.IGNORECASE):
        confirmed = 0
    else:
        # "X detention(s) with a name" or "X confirmed detention(s)"
        m = re.search(r"(\d+)\s+(?:confirmed\s+)?detention", text, re.IGNORECASE)
        if m:
            confirmed = int(m.group(1))

    # Additional unconfirmed reports
    m = re.search(r"additional\s+~?(\d+)\s+reports?", text, re.IGNORECASE)
    if m:
        unconfirmed = int(m.group(1))

    # Date range: "3/11-3/16" or "2/23-3/1"
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})", text)
    if m:
        # Infer year from the URL date (week_date)
        if week_date:
            year = int(week_date[:4])
        else:
            year = datetime.now().year
        try:
            date_start = f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
            date_end = f"{year}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        except ValueError:
            pass

    # Monthly total: "X detentions reported ... during <Month> <Year>"
    monthly_total = None
    m = re.search(r"(\d+)\s+detentions?\s+reported\s+.*?during\s+(\w+)\s+(\d{4})", text, re.IGNORECASE)
    if m:
        monthly_total = int(m.group(1))

    return {
        "confirmed_detentions": confirmed,
        "unconfirmed_reports": unconfirmed,
        "date_range_start": date_start,
        "date_range_end": date_end,
        "monthly_total": monthly_total,
    }


def extract_locations(text):
    """Extract mentioned Oregon counties/cities."""
    oregon_locations = [
        "Multnomah", "Clackamas", "Washington", "Lane", "Marion",
        "Jackson", "Deschutes", "Linn", "Douglas", "Josephine",
        "Portland", "Eugene", "Salem", "Bend", "Medford",
        "Macadam", "St Johns",
    ]
    found = []
    for loc in oregon_locations:
        if re.search(rf"\b{loc}\b", text, re.IGNORECASE):
            found.append(loc)
    return found


def extract_policy_signals(text):
    """Extract policy/legislation mentions."""
    signals = []
    keywords = [
        (r"SAVE act", "SAVE Act"),
        (r"LEAVA act", "LEAVA Act"),
        (r"EAD|work permit|employment authorization", "Work permit policy"),
        (r"proposed rule", "Proposed rule change"),
        (r"ordinance", "Local ordinance"),
        (r"Senate|House|Congress", "Congressional action"),
        (r"ICE field office|Macadam", "ICE field office activity"),
        (r"check.?in", "ICE check-in activity"),
    ]
    for pattern, label in keywords:
        if re.search(pattern, text, re.IGNORECASE):
            if label not in signals:
                signals.append(label)
    return signals


def parse_weekly_update(url):
    """Parse a single PIRC weekly update page."""
    html = fetch_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Get all text content
    # Try to find main content area
    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup
    text = main.get_text(separator="\n", strip=True)

    week_date = extract_date_from_url(url)
    detention_data = extract_detention_count(text, week_date=week_date)
    locations = extract_locations(text)
    policy_signals = extract_policy_signals(text)

    return {
        "week_of": week_date,
        "url": url,
        "confirmed_detentions": detention_data["confirmed_detentions"],
        "unconfirmed_reports": detention_data["unconfirmed_reports"],
        "date_range_start": detention_data["date_range_start"],
        "date_range_end": detention_data["date_range_end"],
        "monthly_total": detention_data["monthly_total"],
        "locations_mentioned": ", ".join(locations),
        "policy_signals": ", ".join(policy_signals),
        "raw_text_excerpt": text[:500],
    }


def generate_incident_rows(pirc_data):
    """
    Convert PIRC weekly summaries into incident rows compatible with
    protest_data_oversight.csv format (date, location, category, title, source_url).
    """
    rows = []
    for week in pirc_data:
        if not week:
            continue

        count = week["confirmed_detentions"]
        unconfirmed = week["unconfirmed_reports"]
        week_date = week["week_of"]
        url = week["url"]
        locations = week["locations_mentioned"] or "Oregon"

        if count > 0:
            # Use end of reporting period as date, or week_of
            incident_date = week.get("date_range_end") or week_date
            if incident_date:
                # Convert to MM/DD/YYYY format to match oversight CSV
                try:
                    dt = datetime.strptime(incident_date, "%Y-%m-%d")
                    incident_date_fmt = dt.strftime("%m/%d/%Y")
                except ValueError:
                    incident_date_fmt = incident_date
            else:
                incident_date_fmt = ""

            # Primary location: use first specific location or Oregon
            primary_loc = locations.split(",")[0].strip()
            if primary_loc in ["Multnomah", "Clackamas", "Washington", "Lane", "Marion"]:
                loc_str = f"{primary_loc} County, OR"
            elif primary_loc in ["Portland", "Eugene", "Salem", "Bend", "Medford"]:
                loc_str = f"{primary_loc}, OR"
            else:
                loc_str = f"{primary_loc}, OR" if primary_loc != "Oregon" else "Oregon"

            dr_start = week.get('date_range_start') or ''
            dr_end = week.get('date_range_end') or ''
            if dr_start and dr_end:
                title = f"PIRC hotline: {count} confirmed detention(s) reported {dr_start} to {dr_end}"
            else:
                title = f"PIRC hotline: {count} confirmed detention(s) reported week of {week_date}"
            if unconfirmed > 0:
                title += f" (+~{unconfirmed} unconfirmed)"

            rows.append({
                "date": incident_date_fmt,
                "location": loc_str,
                "category": "Concerning Arrest/Detention",
                "title": title,
                "source_url": url,
            })

        # Monthly summary if available
        if week.get("monthly_total") and week["monthly_total"] > 0:
            if week_date:
                try:
                    dt = datetime.strptime(week_date, "%Y-%m-%d")
                    monthly_date_fmt = dt.strftime("%m/%d/%Y")
                except ValueError:
                    monthly_date_fmt = ""
            else:
                monthly_date_fmt = ""
            rows.append({
                "date": monthly_date_fmt,
                "location": "Oregon",
                "category": "Concerning Arrest/Detention",
                "title": f"PIRC monthly summary: {week['monthly_total']} detentions reported",
                "source_url": url,
            })

    return rows


def main():
    print("🔍 Scraping PIRC weekly updates...")

    urls = get_weekly_urls()
    print(f"  Found {len(urls)} weekly update URLs")

    if not urls:
        print("  ⚠️  No URLs found. Check if the site structure changed.")
        sys.exit(1)

    all_data = []
    for i, url in enumerate(urls):
        print(f"  [{i+1}/{len(urls)}] {url}")
        result = parse_weekly_update(url)
        if result:
            all_data.append(result)
            det = result["confirmed_detentions"]
            unc = result["unconfirmed_reports"]
            print(f"    → {det} confirmed, {unc} unconfirmed, locations: {result['locations_mentioned'] or 'none'}")

    # Save raw PIRC data as JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\n✅ Saved {len(all_data)} weekly summaries → {OUTPUT_JSON}")

    # Save as CSV
    if all_data:
        fieldnames = list(all_data[0].keys())
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
        print(f"✅ Saved CSV → {OUTPUT_CSV}")

    # Generate incident rows for main dataset
    incident_rows = generate_incident_rows(all_data)
    if incident_rows:
        incident_csv = "data/pirc_incidents.csv"
        fieldnames = ["date", "location", "category", "title", "source_url"]
        with open(incident_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(incident_rows)
        print(f"✅ Generated {len(incident_rows)} incident rows → {incident_csv}")
    else:
        print("  ℹ️  No incident rows generated (no confirmed detentions found)")

    # Summary
    print(f"\n📊 PIRC Data Summary:")
    total_confirmed = sum(d["confirmed_detentions"] for d in all_data if d)
    total_unconfirmed = sum(d["unconfirmed_reports"] for d in all_data if d)
    print(f"  Total confirmed detentions: {total_confirmed}")
    print(f"  Total unconfirmed reports: {total_unconfirmed}")
    print(f"  Weeks covered: {len(all_data)}")
    if all_data:
        dates = [d["week_of"] for d in all_data if d.get("week_of")]
        if dates:
            print(f"  Date range: {min(dates)} to {max(dates)}")


if __name__ == "__main__":
    main()
