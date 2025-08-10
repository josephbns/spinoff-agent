import asyncio
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
import csv

# ---------- Data contracts ----------
class CaseFile(BaseModel):
    company: str
    ticker: str
    announcement_date: str | None = None

class FeatureSet(BaseModel):
    domain: str
    features: Dict[str, float | int | bool | str]
    provenance: List[Dict[str, str]] = Field(default_factory=list)

class CriterionScore(BaseModel):
    criterion: str
    score: float         # 0–5
    confidence: float    # 0–1
    rationale: str
    evidence_ids: List[str] = Field(default_factory=list)

# ---------- Acquisition & normalization (demo placeholders) ----------
async def fetch_and_normalize(subject: str) -> CaseFile:
    await asyncio.sleep(0.1)
    return CaseFile(company=subject, ticker="TBD", announcement_date="2025-07-15")

# ---------- Domain hubs (run in parallel) ----------
async def capital_structure_hub(cf: CaseFile) -> FeatureSet:
    await asyncio.sleep(0.1)
    return FeatureSet(
        domain="capital_structure",
        features={
            "net_leverage_turns": 3.2,
            "fcf_to_net_debt_pct": 22,
            "special_dividend_flag": True,
        },
        provenance=[{"feature": "net_leverage_turns", "url": "https://example.com/press"}],
    )

async def ownership_hub(cf: CaseFile) -> FeatureSet:
    await asyncio.sleep(0.1)
    return FeatureSet(
        domain="ownership",
        features={
            "mgmt_ownership_pct": 2.1,
            "perf_equity_present": 1,  # 1 = yes, 0 = no
        },
    )

async def microstructure_hub(cf: CaseFile) -> FeatureSet:
    await asyncio.sleep(0.1)
    return FeatureSet(
        domain="microstructure",
        features={
            "free_float_pct": 65,
            "russell_eligible": 0,          # 0 = not eligible at spin (demo)
            "avg_daily_dollar_volume": 12000000,
        },
    )

async def ops_hub(cf: CaseFile) -> FeatureSet:
    await asyncio.sleep(0.1)
    return FeatureSet(
        domain="ops",
        features={
            "ebitda_margin_pct": 14,
            "customer_conc_top5_pct": 38,
        },
    )

# ---------- Deterministic scoring rules ----------
def score_debt_loading(cap: FeatureSet) -> CriterionScore:
    nl = float(cap.features.get("net_leverage_turns", 0))
    fcf_nd = float(cap.features.get("fcf_to_net_debt_pct", 0))

    if nl <= 1.5:
        base = 1
    elif nl <= 3.0:
        base = 3
    else:
        base = 4 if fcf_nd >= 20 else 3
        if fcf_nd >= 30:
            base = 5

    rationale = f"Net leverage {nl:.1f}x; FCF/NetDebt approx {fcf_nd:.0f}% -> deleveraging plausible."
    return CriterionScore(criterion="Debt Loading", score=base, confidence=0.75, rationale=rationale)

def score_index_exclusion(micro: FeatureSet) -> CriterionScore:
    russ = int(micro.features.get("russell_eligible", 1))
    adv = float(micro.features.get("avg_daily_dollar_volume", 0))

    if russ == 0 and adv < 15000000:
        s = 5
        r = "Likely excluded from major indices at spin; thin ADV increases forced selling risk."
    elif russ == 0:
        s = 4
        r = "Likely excluded; liquidity somewhat offsets."
    else:
        s = 2
        r = "Index eligible; less forced selling."
    return CriterionScore(criterion="Index Exclusion", score=s, confidence=0.70, rationale=r)

def score_equity_incentives(own: FeatureSet) -> CriterionScore:
    pct = float(own.features.get("mgmt_ownership_pct", 0))
    perf = int(own.features.get("perf_equity_present", 0))

    if pct >= 3 and perf:
        s = 5
    elif pct >= 1 and perf:
        s = 4
    elif pct >= 1:
        s = 3
    else:
        s = 2

    r = f"Mgmt owns approx {pct:.1f}% {'with' if perf else 'without'} performance equity."
    return CriterionScore(criterion="Equity Incentives", score=s, confidence=0.80, rationale=r)

# ---------- Composer (weights + confidence handling) ----------
WEIGHTS = {
    "Debt Loading": 1.3,
    "Index Exclusion": 1.2,
    "Equity Incentives": 1.5,
}

def compose(scores: List[CriterionScore]) -> Tuple[float, List[CriterionScore]]:
    num, den = 0.0, 0.0
    for sc in scores:
        w = WEIGHTS.get(sc.criterion, 1.0) * (0.5 + 0.5 * sc.confidence)
        num += w * sc.score
        den += w
    return ((num / den) if den else 0.0, scores)

# ---------- Orchestration ----------
async def run(subject: str):
    print("\n=== Spinoff Grid (demo) for:", subject, "===")
    casefile = await fetch_and_normalize(subject)

    # Hubs in parallel
    cap, own, micro, ops = await asyncio.gather(
        capital_structure_hub(casefile),
        ownership_hub(casefile),
        microstructure_hub(casefile),
        ops_hub(casefile),
    )

    # Criteria in parallel (CPU-bound tiny funcs -> run in thread pool)
    scores = await asyncio.gather(
        asyncio.to_thread(score_debt_loading, cap),
        asyncio.to_thread(score_index_exclusion, micro),
        asyncio.to_thread(score_equity_incentives, own),
    )

    composite, _ = compose(list(scores))
    print(f"Composite score: {composite:.2f}")
    for sc in scores:
        print(f"- {sc.criterion}: {sc.score}/5  (conf {sc.confidence:.2f})  - {sc.rationale}")

    # Write a simple CSV for Excel
    with open("grid.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Company", "Criterion", "Score", "Confidence", "Rationale"])
        for sc in scores:
            w.writerow([casefile.company, sc.criterion, sc.score, sc.confidence, sc.rationale])
    print("Saved: grid.csv")

if __name__ == "__main__":
    asyncio.run(run("Example SpinCo"))
