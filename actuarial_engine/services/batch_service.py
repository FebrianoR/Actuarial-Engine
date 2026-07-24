"""
Batch Service – Proses seluruh portofolio polis secara batch.

Alur:
1. Terima list PolicyRecord (hasil parse Excel)
2. Pisahkan berdasarkan smethode: PAA, GMM/BBA, VFA
3. Jalankan kalkulasi masing-masing
4. Return list hasil + statistik
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from actuarial_engine.core.excel.parser import (
    PolicyRecord, AssumptionRow, YieldCurveRow, LapseRow
)
from actuarial_engine.core.cashflows.projector import CashFlowProjector
from actuarial_engine.core.discount.yield_curve import DiscountCurve, flat_curve
from actuarial_engine.core.risk_adjustment.calculator import RiskAdjustmentCalculator
from actuarial_engine.core.csm.tracker import CSMTracker
from actuarial_engine.core.bba.calculator import BBACalculator
from actuarial_engine.core.paa.calculator import PAACalculator
from actuarial_engine.audit.trace import AuditTrace
from actuarial_engine.services.audit_service import AuditService


# In-memory store untuk batch results
_batch_store: dict[str, list[dict[str, Any]]] = {}


def _build_discount_curve(yield_rows: list[YieldCurveRow], syear: int) -> DiscountCurve:
    """Bangun DiscountCurve dari yield curve data. Filter by syear."""
    rows = [r for r in yield_rows if r.syear == syear] or yield_rows
    if not rows:
        return flat_curve(0.065)

    # Konversi ke tenor (tahun): ambil rata-rata rate per tahun
    from collections import defaultdict
    year_rates: dict[int, list[float]] = defaultdict(list)
    for r in rows:
        if r.sdate:
            tenor = max(1, (r.sdate.year - rows[0].sdate.year) + 1) if rows[0].sdate else 1
        else:
            tenor = max(1, r.syear + 1)
        year_rates[tenor].append(r.srate / 100)  # konversi dari % ke desimal

    rate_dict = {t: sum(v) / len(v) for t, v in year_rates.items() if v}
    if not rate_dict:
        return flat_curve(0.065)
    return DiscountCurve(rate_dict)


def _get_assumption(assumptions: list[AssumptionRow], cob: str, syear: int) -> AssumptionRow | None:
    """Cari asumsi yang paling sesuai untuk cob dan syear."""
    # Exact match
    for a in assumptions:
        if a.cob == cob and a.syear == syear:
            return a
    # Fallback ke cob saja
    for a in assumptions:
        if a.cob == cob:
            return a
    # Fallback ke first available
    return assumptions[0] if assumptions else None


def _get_lapse_rates(lapse_rows: list[LapseRow], cob: str, coverage_years: int) -> list[float]:
    """Ambil lapse rate tahunan untuk cob tertentu."""
    rows = [r for r in lapse_rows if r.cob == cob] or lapse_rows
    if not rows:
        return [0.05] * coverage_years

    # Aggregate bulan ke tahun (rata-rata 12 bulan per tahun)
    annual: list[float] = []
    for year in range(1, coverage_years + 1):
        month_rows = [r for r in rows if r.syear == year]
        if month_rows:
            annual.append(sum(r.srate for r in month_rows) / len(month_rows))
        elif annual:
            annual.append(annual[-1])
        else:
            annual.append(0.05)

    return annual[:coverage_years]


def _calc_coverage_years(pol: PolicyRecord) -> int:
    """Hitung jumlah tahun coverage dari tanggal begin/end."""
    if pol.begindt and pol.enddt:
        delta = pol.enddt - pol.begindt
        return max(1, round(delta.days / 365))
    return 1


def calculate_policy_paa(
    pol: PolicyRecord,
    assumptions: list[AssumptionRow],
    audit_svc: AuditService,
) -> dict[str, Any]:
    """Kalkulasi PAA untuk satu polis."""
    assum = _get_assumption(assumptions, pol.cob, pol.begindt.year if pol.begindt else 2024)

    coverage_years = _calc_coverage_years(pol)
    val_date = pol.valdate or date.today()
    end_date = pol.enddt or date.today()
    begin_date = pol.begindt or date(val_date.year, 1, 1)

    claim_ratio = assum.expclaim if assum else 0.15
    opex_ratio = assum.expopex if assum else 0.025
    ra_ratio = assum.expriskadj if assum else 0.15

    # Estimasi claims incurred & outstanding
    written_prem = pol.gwp
    claims_incurred = written_prem * claim_ratio
    outstanding_claims = claims_incurred * 0.3  # 30% masih outstanding

    try:
        calc = PAACalculator(
            written_premium=written_prem,
            coverage_start=begin_date,
            coverage_end=end_date,
            reporting_date=val_date,
            claims_incurred=claims_incurred,
            outstanding_claims=outstanding_claims,
            ibnr_ratio=ra_ratio,
            acquisition_cost_ratio=opex_ratio,
            amortize_dac=True,
            discount_rate=0.0,
        )
        result = calc.calculate()

        trace = AuditTrace("PAA", "upload_batch")
        trace.steps = result.intermediate_steps

        # ── Simpan ke AuditService ──
        input_snap = {
            "policyno": pol.policyno, "cob": pol.cob,
            "gwp": written_prem, "claim_ratio": claim_ratio,
            "begin_date": str(begin_date), "end_date": str(end_date),
            "val_date": str(val_date),
        }
        output_snap = {
            "lrc_net": result.lrc_net, "lic": result.lic,
            "total_liability": result.total_liability,
            "earned_premium": result.earned_premium,
            "loss_ratio": result.loss_ratio,
        }
        audit_svc.save(trace, pol.policyno, input_snap, output_snap)

        return {
            "policyno": pol.policyno,
            "contract_id": pol.policyno,
            "cob": pol.cob,
            "method": "PAA",
            "tsi": pol.tsi,
            "gwp": pol.gwp,
            "pvfcf": 0.0,
            "risk_adjustment": 0.0,
            "csm": 0.0,
            "lrc_net": result.lrc_net,
            "lic": result.lic,
            "total_liability": result.total_liability,
            "insurance_contract_liability": result.total_liability,
            "earned_premium": result.earned_premium,
            "loss_ratio": result.loss_ratio,
            "is_onerous": result.lic > result.lrc_net,
            "trace_id": trace.trace_id,
            "status": "ok",
        }
    except Exception as e:
        return {"policyno": pol.policyno, "contract_id": pol.policyno,
                "cob": pol.cob, "method": "PAA", "status": "error", "error": str(e)}


def calculate_policy_gmm(
    pol: PolicyRecord,
    assumptions: list[AssumptionRow],
    yield_curve: list[YieldCurveRow],
    lapse_rows: list[LapseRow],
    audit_svc: AuditService,
) -> dict[str, Any]:
    """Kalkulasi BBA/GMM untuk satu polis."""
    assum = _get_assumption(assumptions, pol.cob, pol.begindt.year if pol.begindt else 2024)
    coverage_years = _calc_coverage_years(pol)
    val_year = pol.valdate.year if pol.valdate else 2024

    claim_ratio = assum.expclaim if assum else 0.20
    opex_ratio = assum.expopex if assum else 0.05
    ra_coc = 0.06
    ra_capital = assum.expriskadj if assum else 0.10

    # ── Derive qx dari claim ratio ──────────────────────────────────────
    # claim_ratio = E[klaim/premi], sehingga:
    #   E[klaim] = claim_ratio × GWP
    #   E[klaim] = qx × TSI  →  qx = claim_ratio × GWP / TSI
    tsi = pol.tsi or pol.gwp * 10
    base_qx = (claim_ratio * pol.gwp) / tsi if tsi > 0 else 0.005
    # qx meningkat sedikit tiap tahun seiring usia (aging factor 2%/yr)
    mortality_rates = [min(base_qx * (1 + 0.02 * i), 0.05) for i in range(coverage_years)]
    lapse_rates = _get_lapse_rates(lapse_rows, pol.cob, coverage_years)

    disc_curve = _build_discount_curve(yield_curve, val_year)
    disc_rates_int = {t: disc_curve.spot_rate(t) for t in range(1, min(coverage_years, 30) + 1)}

    ra_calc = RiskAdjustmentCalculator(
        coc_rate=ra_coc,
        required_capital_ratio=ra_capital,
        discount_rates=disc_rates_int,
    )
    csm_tracker = CSMTracker()

    try:
        projector = CashFlowProjector(
            gross_premium=pol.gwp,
            sum_assured=tsi,
            coverage_years=coverage_years,
            mortality_rates=mortality_rates,
            lapse_rates=lapse_rates,
            expense_ratio=opex_ratio,
        )
        projection = projector.project()

        trace = AuditTrace("BBA", "upload_batch")
        calculator = BBACalculator(
            cash_flow_projector=projection,
            discount_curve=disc_curve,
            ra_calculator=ra_calc,
            csm_tracker=csm_tracker,
        )
        result = calculator.calculate(audit_trace=trace)

        # ── Hitung breakdown komponen untuk Sistem Pembukuan GMM ──
        import numpy as np
        pv_inflows = disc_curve.discount(projection.inflows)
        pv_outflows = disc_curve.discount(projection.outflows)

        total_pv_inflows = float(np.sum(pv_inflows))
        total_pv_outflows = float(np.sum(pv_outflows))

        # Breakdown outflows: klaim vs biaya
        # Dari projector: outflow = death_claims + expenses
        # death_claims = active * qx * SA, expenses = active * (expense_ratio * prem + maintenance)
        # Kita re-derive komponen klaim dan biaya per tahun
        active = 1.0
        claim_flows = []
        expense_flows = []
        for t in range(coverage_years):
            qx_t = mortality_rates[t] if t < len(mortality_rates) else mortality_rates[-1]
            lx_t = lapse_rates[t] if t < len(lapse_rates) else lapse_rates[-1]
            death_claim = active * qx_t * tsi
            expense = active * opex_ratio * pol.gwp
            claim_flows.append(death_claim)
            expense_flows.append(expense)
            active = active * (1 - qx_t) * (1 - lx_t)

        pv_claims = float(np.sum(disc_curve.discount(claim_flows)))
        pv_expenses = float(np.sum(disc_curve.discount(expense_flows)))

        # FCF & CSM
        fcf = result.fulfilment_cash_flows  # PVFCF + RA
        is_onerous = fcf > 0
        loss_component = fcf if is_onerous else 0.0
        csm_val = result.csm

        # Accretion = rata-rata discount rate × komponen (simplified Year 1)
        avg_rate = disc_curve.spot_rate(1) if coverage_years >= 1 else 0.065
        accretion_claims = pv_claims * avg_rate
        accretion_expense = pv_expenses * avg_rate
        accretion_ra = result.risk_adjustment * avg_rate
        accretion_csm = csm_val * avg_rate
        accretion_lc = loss_component * avg_rate

        total_accretion = accretion_claims + accretion_expense + accretion_ra + accretion_csm + accretion_lc

        # Insurance Revenue breakdown (release = alokasi proporsional per period)
        # Simplified: revenue tahun 1 = total / coverage_years
        rev_claim = pv_claims / coverage_years if coverage_years > 0 else 0
        rev_expense = pv_expenses / coverage_years if coverage_years > 0 else 0
        rev_ra = result.risk_adjustment / coverage_years if coverage_years > 0 else 0
        rev_csm = csm_val / coverage_years if coverage_years > 0 else 0
        total_revenue = rev_claim + rev_expense + rev_ra + rev_csm

        # Total liabilities
        total_liab = pv_claims + pv_expenses + result.risk_adjustment + csm_val + loss_component
        equity = pol.gwp - total_liab

        # ── Simpan ke AuditService ──
        input_snap = {
            "policyno": pol.policyno, "cob": pol.cob,
            "gwp": pol.gwp, "tsi": pol.tsi,
            "coverage_years": coverage_years,
            "claim_ratio": claim_ratio,
            "opex_ratio": opex_ratio,
        }
        output_snap = {
            "pvfcf": result.pvfcf,
            "risk_adjustment": result.risk_adjustment,
            "csm": result.csm,
            "insurance_contract_liability": result.insurance_contract_liability,
            "is_onerous": is_onerous,
        }
        audit_svc.save(trace, pol.policyno, input_snap, output_snap)

        # ── ICL Reporting per PSAK 117 ──
        reported_icl = fcf if is_onerous else 0.0
        reported_lrc = result.csm
        reported_total_liab = reported_icl + result.risk_adjustment if is_onerous else result.risk_adjustment

        return {
            "policyno": pol.policyno,
            "contract_id": pol.policyno,
            "cob": pol.cob,
            "method": "GMM",
            "tsi": pol.tsi,
            "gwp": pol.gwp,
            "pvfcf": result.pvfcf,
            "risk_adjustment": result.risk_adjustment,
            "csm": result.csm,
            "lrc_net": reported_lrc,
            "lic": 0.0,
            "total_liability": reported_total_liab,
            "insurance_contract_liability": reported_total_liab,
            "is_onerous": is_onerous,
            "trace_id": trace.trace_id,
            "status": "ok",
            # ── Granular data untuk Sistem Pembukuan GMM ──
            "gmm_detail": {
                # Balance Sheet - Asset
                "bank_piutang": pol.gwp,
                # Balance Sheet - Liability (LRC)
                "expected_claims": pv_claims,
                "expected_acq_cost": 0.0,
                "expected_expense": pv_expenses,
                "risk_adjustment_liability": result.risk_adjustment,
                "csm_liability": csm_val,
                "loss_component": loss_component,
                "dac": 0.0,
                "total_liability": total_liab,
                # Balance Sheet - Equity
                "equity": equity,
                # RI Asset (default 0 — no reinsurance in initial)
                "ri_claim_asset": 0.0,
                "ri_acq_cost_asset": 0.0,
                "ri_expense_asset": 0.0,
                "ri_npr": 0.0,
                "ri_ra_asset": 0.0,
                "ri_csm_asset": 0.0,
                "ri_lc_asset": 0.0,
                "ri_acq_cost_dimuka": 0.0,
                "total_ri_asset": 0.0,
                "total_asset": pol.gwp,
                # P&L - Insurance Revenue
                "rev_expected_claim": rev_claim,
                "rev_acq_cost": 0.0,
                "rev_expected_expense": rev_expense,
                "rev_risk_adjustment": rev_ra,
                "rev_csm": rev_csm,
                "total_insurance_revenue": total_revenue,
                # P&L - Insurance Service Expense
                "initial_recognition_lc": 0.0,
                "changes_future_services_lc": 0.0,
                "incurred_claims": 0.0,
                "insurance_expense": 0.0,
                "acquisition_costs_expense": 0.0,
                "total_insurance_expense": 0.0,
                # P&L - Insurance Service Result
                "insurance_service_result": total_revenue,
                # P&L - Insurance Finance Expense (Accretion)
                "accretion_claims": accretion_claims,
                "accretion_expense": accretion_expense,
                "accretion_ra": accretion_ra,
                "accretion_csm": accretion_csm,
                "accretion_lc": accretion_lc,
                "accretion_acq_cost": 0.0,
                "total_accretion": total_accretion,
                # P&L - Change in discount rate
                "chg_disc_claim": 0.0,
                "chg_disc_expense": 0.0,
                "chg_disc_ra": 0.0,
                "chg_disc_csm": 0.0,
                "chg_disc_lc": 0.0,
                "chg_disc_acq_cost": 0.0,
                "total_chg_disc": 0.0,
                "total_finance_expense": total_accretion,
                # P&L - Bottom line
                "surplus_gross": equity,
                # RI P&L (all zero for initial)
                "ri_rev_claim": 0.0,
                "ri_rev_acq_cost": 0.0,
                "ri_rev_expense": 0.0,
                "ri_rev_npr": 0.0,
                "ri_rev_ra": 0.0,
                "ri_rev_csm": 0.0,
                "total_ri_revenue": 0.0,
                "ri_exp_lc_initial": 0.0,
                "ri_exp_lc_changes": 0.0,
                "ri_exp_incurred_claims": 0.0,
                "ri_exp_expense": 0.0,
                "ri_exp_acq_cost": 0.0,
                "total_ri_expense": 0.0,
                "ri_accretion_claim": 0.0,
                "ri_accretion_expense": 0.0,
                "ri_accretion_npr": 0.0,
                "ri_accretion_ra": 0.0,
                "ri_accretion_csm": 0.0,
                "ri_accretion_lc": 0.0,
                "ri_accretion_acq_cost": 0.0,
                "total_ri_accretion": 0.0,
                "ri_chg_disc_claim": 0.0,
                "ri_chg_disc_expense": 0.0,
                "ri_chg_disc_npr": 0.0,
                "ri_chg_disc_ra": 0.0,
                "ri_chg_disc_csm": 0.0,
                "ri_chg_disc_lc": 0.0,
                "ri_chg_disc_acq_cost": 0.0,
                "total_ri_chg_disc": 0.0,
                "total_ri_finance_expense": 0.0,
                "surplus_ri": 0.0,
                "profit_loss": equity,
            },
        }
    except Exception as e:
        return {"policyno": pol.policyno, "contract_id": pol.policyno,
                "cob": pol.cob, "method": "GMM", "status": "error", "error": str(e)}


class BatchService:
    """Service untuk batch calculation seluruh portofolio."""

    def __init__(self, audit_service: AuditService | None = None) -> None:
        self._audit = audit_service or AuditService()

    def run(
        self,
        policies: list[PolicyRecord],
        assumptions: list[AssumptionRow],
        yield_curve: list[YieldCurveRow],
        lapse_rows: list[LapseRow],
    ) -> dict[str, Any]:
        """
        Jalankan batch calculation untuk semua polis.
        Returns: batch_id + results + statistics
        """
        batch_id = str(uuid.uuid4())
        results: list[dict[str, Any]] = []

        for pol in policies:
            if pol.smethode == "PAA":
                res = calculate_policy_paa(pol, assumptions, self._audit)
            else:
                res = calculate_policy_gmm(pol, assumptions, yield_curve, lapse_rows, self._audit)
            results.append(res)

        # Statistik
        ok_results = [r for r in results if r.get("status") == "ok"]
        stats = {
            "total": len(results),
            "success": len(ok_results),
            "error": len(results) - len(ok_results),
            "paa_count": sum(1 for r in ok_results if r.get("method") == "PAA"),
            "gmm_count": sum(1 for r in ok_results if r.get("method") == "GMM"),
            "total_icl": sum(r.get("insurance_contract_liability", 0) for r in ok_results),
            "total_lrc": sum(r.get("lrc_net", 0) for r in ok_results),
            "total_lic": sum(r.get("lic", 0) for r in ok_results),
        }

        _batch_store[batch_id] = results

        return {
            "batch_id": batch_id,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": stats,
            "results": results,
        }


def get_batch(batch_id: str) -> list[dict[str, Any]] | None:
    """Ambil hasil batch dari store."""
    return _batch_store.get(batch_id)
