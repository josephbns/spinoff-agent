---
name: equity_incentives_scorer
description: Score Equity Incentives from FeatureSet(ownership). Return CriterionScore JSON only.
---
Input: FeatureSet(domain="ownership") with mgmt_ownership_pct and perf_equity_present.
Rules:
- mgmt_ownership_pct >= 3 and perf_equity_present -> 5
- >= 1 and perf_equity_present -> 4
- >= 1 -> 3
- else -> 2
Output JSON:
{
  "criterion": "Equity Incentives",
  "score": 0,
  "confidence": 0.0,
  "rationale": "",
  "evidence_ids": []
}
Return JSON only. No prose.
