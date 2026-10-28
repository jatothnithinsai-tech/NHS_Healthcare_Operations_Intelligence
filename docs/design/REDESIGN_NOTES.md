# Dashboard redesign decisions

27 October 2026. Presentation-only changes; analytical definitions stay intact.

| Page | Stakeholder | Primary question | Organisation and caveats |
|---|---|---|---|
| Executive Healthcare Performance | Performance director | How do the three latest published operational measures compare? | Separate domain KPIs, monthly RTT/A&E trends and provider context; never add pathways, attendances and waits. |
| RTT Waiting List Intelligence | Elective-care manager | Which specialties and providers account for long waits? | Pathways, over-52-week counts, month change, specialty comparison and nested-threshold trends. |
| A&E and Diagnostics Intelligence | Urgent-care and diagnostics leads | Where should attendance and diagnostic pressure be investigated? | Separate attendance/activity/waiting measures; DTA 12+ hours remains decision-to-admit waiting. |
| Data Quality & Operational Monitoring | Reporting operations lead | Are the source versions, dates and pipeline runs fit for review? | Coverage, unverified publication dates, revision counts, source timing and actual execution history. |

## Visual standard
- Light neutral canvas, aligned panels, restrained borders, readable Segoe UI/Aptos typography and labels that state the metric population.
- Transit: royal blue, observed-good-service teal, disruption coral and a purple coverage card.
- NHS: healthcare blue, teal, coral and selective purple; independent portfolio branding.
- Hospitality: warm green, blue and gold. Native objects, formulas and data sources are retained.
- Units and denominators remain visible; colour is supported by text labels. No generated mockup or rewritten KPI pixels are used.

## Verification limits
Page loading, metadata validation and source fingerprints are distinct from a full usability test. Consult redesign_validation.json for the exact executed checks. Existing historical test evidence is retained separately.
