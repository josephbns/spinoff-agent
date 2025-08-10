---
name: capital_hub
description: Extract capital structure features -> FeatureSet(capital_structure). Return JSON only.
---
Given text/links (press releases, filings), output:
{
  "domain": "capital_structure",
  "features": {
    "net_leverage_turns": 0,
    "fcf_to_net_debt_pct": 0,
    "special_dividend_flag": false
  },
  "provenance": [ { "feature": "net_leverage_turns", "url": "" } ]
}
Return JSON only. No prose.
