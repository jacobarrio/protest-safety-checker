# Protest Safety Checker

**A tool for protest organizers to assess historical risk levels in US cities.**

Give it a city name, get a risk assessment based on recent incidents of police violence, ICE operations, and constitutional violations.

## Why This Exists

The US is experiencing unprecedented civil unrest and state violence. Protest organizers need data to plan safer actions and protect participants.

This tool analyzes historical patterns to help organizers make informed decisions about when, where, and how to mobilize.

## What It Does

```bash
$ python3 risk_checker.py
Enter city name: Minneapolis

==================================================
PROTEST SAFETY ASSESSMENT: MINNEAPOLIS
==================================================

🚨 RISK LEVEL: 🔴 HIGH
📊 Risk Score: 39.0

📈 Statistics:
  • Last 30 days: 5 incidents
  • Last 6 months: 6 incidents
  • Avg severity: 9.0/10

📋 Recent Incidents:
  • 2026-01-23 | POLICE_VIOLENCE
    General strike - tear gas, pepper spray, flashbangs on protesters
  • 2026-01-23 | ICE_OPERATION
    6-year-old left wandering streets after father detained
  [...]
```

## Installation

**Requirements:**
- Python 3.8+
- pandas

**Setup:**
```bash
git clone https://github.com/jacobarrio/protest-safety-checker.git
cd protest-safety-checker
pip install pandas
```

## Usage

```bash
python3 risk_checker.py
```

Enter a city name when prompted. Currently supported cities:
- Minneapolis
- Portland
- New York City
- Atlanta
- Seattle
- Los Angeles

## How Risk Scores Work

**Risk Level:**
- 🔴 HIGH (30+) - Multiple recent violent incidents, elevated threat
- 🟡 MEDIUM (15-29) - Some recent incidents, proceed with caution
- 🟢 LOW (<15) - Few recent incidents, relatively safer

**Risk Score Calculation:**
```
score = (recent_incidents × 3) + (total_incidents × 1) + (avg_severity × 2)
```

Where:
- `recent_incidents` = incidents in last 30 days
- `total_incidents` = incidents in last 6 months
- `avg_severity` = average severity rating (1-10 scale)

## Data Sources

v0.1 uses manually verified incidents from:
- News reports (verified independently)
- Legal filings (court documents, ACLU reports)
- Eyewitness accounts (cross-referenced)

**Included incident types:**
- Police violence at protests (tear gas, rubber bullets, arrests)
- ICE operations affecting civilians
- Constitutional violations (4th/5th Amendment)
- State repression (journalist arrests, military-style occupation)

## Limitations

**v0.1 is a minimal viable product:**
- ✅ Works with verified data
- ✅ Provides basic risk assessment
- ❌ Limited to 11 cities with <50 incidents
- ❌ No real-time data (incidents manually added)
- ❌ No predictive modeling

**What this tool does NOT do:**
- Track current/ongoing protests
- Predict future violence
- Guarantee safety (risk is always present)
- Replace local organizing knowledge

## Roadmap

**v0.2 (next):**
- Expand to 50+ incidents across more cities
- Add automated data collection
- Include source links for verification

**v0.3+:**
- Real-time incident tracking
- Predictive risk modeling (ML)
- Web interface
- API for organizer tools

## For Organizers

**This tool is a starting point, not a guarantee.**

Use it to:
- Assess baseline risk in your city
- Plan safer protest tactics
- Allocate resources (medics, legal observers)
- Educate participants about local conditions

**Always:**
- Trust local knowledge over data
- Have legal support ready
- Plan de-escalation strategies
- Prioritize participant safety

## Contributing

Found incorrect data? Have incidents to add? Open an issue or PR.

**To add incidents:**
Edit `protest_data.csv` with verified incidents. Format:
```
city,state,date,type,description,source,severity
```

**Data verification standards:**
- Cross-reference at least 2 independent sources
- Include verifiable source URL
- Severity ratings (1-10) should reflect actual harm/threat

## License

MIT License - use this to protect people.

## Contact

Built by Jacob Lee ([@jacobarrio](https://github.com/jacobarrio))

**Resistance builder.** Tools for organizers, not profits.

---

*This is v0.1 - a working prototype. It will improve with community contributions.*
