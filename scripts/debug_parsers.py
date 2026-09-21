"""Quick debug script for parsers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actuarial_engine.core.excel.assumptions_v2_parser import parse_consolidated_assumptions_from_path

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "templates")

path = os.path.join(TEMPLATES, "ASUMSI 2020 - 2025 - Update.xlsx")
assumptions, errors = parse_consolidated_assumptions_from_path(path)

print("=== Loss Ratio by COB ===")
for lr in assumptions.loss_ratio_by_cob:
    print(f"  {lr.cob}: {lr.ratios}")

print("\n=== Expense Ratio ===")
print(f"  Total ratios: {assumptions.expense.total_ratios}")
print(f"  Gross premium: {assumptions.expense.gross_premium}")
print(f"  Total opex: {assumptions.expense.total_operating_expense}")
print(f"  Details ({len(assumptions.expense.details)}):")
for d in assumptions.expense.details:
    print(f"    {d.category}: {d.amounts}")
print(f"  Sub-ratios ({len(assumptions.expense.sub_ratios)}):")
for d in assumptions.expense.sub_ratios:
    print(f"    {d.category}: {d.amounts}")

print("\n=== PAD ===")
for p in assumptions.pad_tables:
    print(f"  CL {p.confidence_level}:")
    print(f"    Gross ({len(p.gross)}):", [e.cob for e in p.gross])
    print(f"    Reas ({len(p.reinsurance)}):", [e.cob for e in p.reinsurance])
    print(f"    Net ({len(p.net)}):", [e.cob for e in p.net])

print("\n=== ICHE ===")
for e in assumptions.iche:
    print(f"  {e.cob}: {e.ratios}")

print("\n=== Discount Rates ===")
for dr in assumptions.discount_rates:
    print(f"  {dr.year} ({dr.label[:50]}): {len(dr.terms)} terms")
    if 0 in dr.terms:
        sak = dr.terms[0].get("SAK")
        print(f"    Term 0 SAK: {sak}")

print("\n=== Inflation ===")
print(f"  Monthly: {len(assumptions.inflation_monthly)} entries")
if assumptions.inflation_monthly:
    print(f"  First: {assumptions.inflation_monthly[0].month} {assumptions.inflation_monthly[0].year} = {assumptions.inflation_monthly[0].rate}")
print(f"  Averages: {len(assumptions.inflation_averages)} entries")
for a in assumptions.inflation_averages:
    print(f"    {a.valuation_date}: {a.average_3yr}")

print("\n=== Lapse ===")
print(f"  Durations: {len(assumptions.lapse.ratios)}")
for dur, years in list(assumptions.lapse.ratios.items())[:3]:
    print(f"    Duration {dur}: {years}")

print("\n=== Summary ===")
for sy in assumptions.summary:
    print(f"  Year {sy.year}: {len(sy.rows)} COBs")
    for r in sy.rows[:3]:
        print(f"    {r.cob}: LR={r.loss_ratio:.4f} PAD={r.pad:.4f} Exp={r.expense:.4f} Total={r.total:.4f}")
