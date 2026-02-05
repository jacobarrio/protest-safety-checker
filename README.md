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

Enter a city name when prompted. **418 verified incidents** across **180+ cities** in 39 states (as of Feb 2026).

Top cities by incident count:
- Chicago (38+ incidents)
- Minneapolis (37+ incidents)  
- Portland (21+ incidents)
- Los Angeles (23+ incidents)
- New York City (13+ incidents)
- Many more...

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

**Primary source:** [House Oversight Committee Democrats Immigration Enforcement Dashboard](https://oversightdemocrats.house.gov/immigration-dashboard)  
All incidents verified by reputable news outlets or referenced in litigation.

Additional sources:
- Court documents and legal filings
- Verified news reports (cross-referenced)
- ACLU reports

**Included incident types:**
- Police violence at protests (tear gas, rubber bullets, arrests)
- ICE operations affecting civilians
- Constitutional violations (4th/5th Amendment)
- State repression (journalist arrests, military-style occupation)

## Limitations

**v0.1 status:**
- ✅ Works with verified official data (House Oversight Committee)
- ✅ 418 verified incidents across 180+ cities
- ✅ Provides basic risk assessment
- ⏳ Data current through Feb 2026 (updated periodically)
- ❌ No real-time tracking (incidents added after verification)
- ❌ No predictive modeling

**What this tool does NOT do:**
- Track current/ongoing protests
- Predict future violence
- Guarantee safety (risk is always present)
- Replace local organizing knowledge

## Roadmap

**v0.2 (in progress):**
- ✅ Automated scraping of House Oversight Dashboard
- ✅ Expanded to 400+ incidents
- ⏳ Add more data sources (ACLU tracker, local reports)
- ⏳ Improve city matching (handle variations)

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
