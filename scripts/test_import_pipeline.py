"""
Integration Test – Parse semua file dari data/templates/ dan validasi hasilnya.
"""
import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actuarial_engine.core.excel.ojk_parser import parse_ojk_codes_from_path
from actuarial_engine.core.excel.assumptions_v2_parser import parse_consolidated_assumptions_from_path
from actuarial_engine.core.excel.inforce_parser import parse_inforce_from_path

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "templates")


def test_ojk_codes():
    print("=" * 60)
    print("TEST: OJK Codes Parser")
    print("=" * 60)
    path = os.path.join(TEMPLATES, "SANDI LINI USAHA BERDASARKAN OJK APOLLO - KIRIM.xlsx")
    table, errors = parse_ojk_codes_from_path(path)

    print(f"  Codes parsed: {len(table.codes)}")
    print(f"  Errors: {errors}")
    for c in table.codes[:5]:
        print(f"    {c}")

    # Validations
    assert len(table.codes) == 21, f"Expected 21 codes, got {len(table.codes)}"
    assert table.get_name(501) == "Harta Benda", f"501 should be 'Harta Benda'"
    assert table.get_name(512) == "Kesehatan", f"512 should be 'Kesehatan'"
    assert table.get_name(521) == "Asuransi barang elektronik"
    print("  [PASS] All validations passed!")
    return True


def test_assumptions():
    print("\n" + "=" * 60)
    print("TEST: Consolidated Assumptions Parser")
    print("=" * 60)
    path = os.path.join(TEMPLATES, "ASUMSI 2020 - 2025 - Update.xlsx")
    assumptions, errors = parse_consolidated_assumptions_from_path(path)

    print(f"  Errors: {errors}")
    print(f"  Available years: {assumptions.available_years}")
    print(f"  Loss Ratio by Product: {len(assumptions.loss_ratio_by_product)} entries")
    print(f"  Loss Ratio by COB: {len(assumptions.loss_ratio_by_cob)} entries")
    print(f"  PAD tables: {len(assumptions.pad_tables)}")
    print(f"  ICHE entries: {len(assumptions.iche)}")
    print(f"  Discount rate years: {len(assumptions.discount_rates)}")
    print(f"  Inflation monthly: {len(assumptions.inflation_monthly)} entries")
    print(f"  Inflation averages: {len(assumptions.inflation_averages)} entries")
    print(f"  Lapse durations: {len(assumptions.lapse.ratios)}")
    print(f"  Expense years: {len(assumptions.expense.total_ratios)}")
    print(f"  Summary years: {len(assumptions.summary)}")

    # Sample data
    if assumptions.loss_ratio_by_product:
        lr = assumptions.loss_ratio_by_product[0]
        print(f"\n  Sample Loss Ratio Product: {lr.cob}/{lr.business_code} {lr.business_name}")
        print(f"    Ratios: {lr.ratios}")

    if assumptions.loss_ratio_by_cob:
        lr = assumptions.loss_ratio_by_cob[0]
        print(f"\n  Sample Loss Ratio COB: {lr.cob}")
        print(f"    Ratios: {lr.ratios}")

    # Validate specific values from our analysis
    lr_property = assumptions.get_loss_ratio("Property", 2023)
    if lr_property is not None:
        print(f"\n  Property Loss Ratio 2023: {lr_property:.6f}")
        assert abs(lr_property - 0.7622924660862627) < 0.001, "Property LR 2023 mismatch"

    exp_2023 = assumptions.get_expense_ratio(2023)
    if exp_2023 is not None:
        print(f"  Expense Ratio 2023: {exp_2023:.6f}")
        # R15 from the Excel: Rasio Biaya 2023 = 0.14267631484560075
        assert abs(exp_2023 - 0.14267631484560075) < 0.01, f"Expense ratio 2023 mismatch: {exp_2023}"

    # Discount rates
    sak_2025_t0 = assumptions.get_discount_rate_sak(2025, 0)
    if sak_2025_t0 is not None:
        print(f"  Discount SAK 2025 Term 0: {sak_2025_t0:.8f}")
        assert abs(sak_2025_t0 - 0.04744445) < 0.001, "Discount SAK 2025 t0 mismatch"

    print("  [PASS] All validations passed!")
    return True


def test_inforce_2023():
    print("\n" + "=" * 60)
    print("TEST: Inforce Parser (2023)")
    print("=" * 60)
    path = os.path.join(TEMPLATES, "01. INFORCE 31 DESEMBER 2023 - KIRIM.xlsx")
    if not os.path.exists(path):
        print("  SKIP: File not found")
        return True

    print("  Parsing (this may take 1-2 minutes for 200K rows)...")
    start = time.time()
    parsed = parse_inforce_from_path(path)
    elapsed = time.time() - start

    print(f"  Parse time: {elapsed:.1f}s")
    print(f"  Year: {parsed.year}")
    print(f"  Records: {len(parsed.records)}")
    print(f"  Stoploss: {len(parsed.stoploss)}")
    print(f"  Errors: {parsed.errors}")

    if parsed.records:
        r = parsed.records[0]
        print(f"\n  First record: {r.policyno}")
        print(f"    COB: {r.cob}, Product: {r.product}")
        print(f"    GWP: {r.gwp:,.2f}, NGWP: {r.ngwp:,.2f}")
        print(f"    TSI: {r.tsi:,.2f}")
        print(f"    Begin: {r.begindt}, End: {r.enddt}")
        print(f"    Methode: {r.smethode}")

    if parsed.summary:
        print(f"\n  Pivot summary:")
        print(f"    Products: {list(parsed.summary.by_product.keys())}")
        print(f"    Total policies: {parsed.summary.total_policies}")
        print(f"    Total GWP: {parsed.summary.total_gwp:,.2f}")

    # Validations
    assert parsed.year == 2023, f"Expected year 2023, got {parsed.year}"
    assert len(parsed.records) > 10000, f"Expected >10K records, got {len(parsed.records)}"
    assert len(parsed.stoploss) > 0, "Expected stoploss records"

    # First record validation
    if parsed.records:
        r = parsed.records[0]
        assert r.cob == "510", f"First record COB should be 510, got {r.cob}"
        assert r.product == "Tanggung Gugat", f"First record product mismatch"
        assert r.smethode == "PAA", f"First record method should be PAA"
        assert r.gwp == 200000, f"First record GWP should be 200000"

    print("  [PASS] All validations passed!")
    return True


if __name__ == "__main__":
    results = {}

    results["OJK Codes"] = test_ojk_codes()
    results["Assumptions"] = test_assumptions()
    results["Inforce 2023"] = test_inforce_2023()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {name}")
    print()

    all_pass = all(results.values())
    sys.exit(0 if all_pass else 1)
