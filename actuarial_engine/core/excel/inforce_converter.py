"""
Inforce Converter – Konversi InforceRecord ke PolicyRecord.

Mengizinkan data dari file INFORCE bulanan untuk diproses
oleh engine kalkulasi PAA/GMM yang menggunakan PolicyRecord.

Opsi A: Data RI (reinsurance) diabaikan untuk sementara.
"""
from __future__ import annotations

import logging
from typing import Any

from actuarial_engine.core.excel.parser import PolicyRecord
from actuarial_engine.models.inforce import InforceRecord, ParsedInforce

logger = logging.getLogger(__name__)


def inforce_record_to_policy(rec: InforceRecord) -> PolicyRecord:
    """
    Konversi satu InforceRecord ke PolicyRecord.

    Field mapping:
      - Field yang sama: sguser, id, batchnr, cob, product, sob,
        policyno, begindt, enddt, valdate, stspolis, tsi, gwp,
        discount, outgo, ngwp, smethode
      - Field RI (ripremi, ricom, ripreminett): diabaikan (Opsi A)
    """
    return PolicyRecord(
        sguser=rec.sguser,
        id=rec.id,
        batchnr=rec.batchnr,
        cob=rec.cob,
        product=rec.product,
        sob=rec.sob,
        policyno=rec.policyno,
        begindt=rec.begindt,
        enddt=rec.enddt,
        valdate=rec.valdate,
        stspolis=rec.stspolis,
        tsi=rec.tsi,
        gwp=rec.gwp,
        discount=rec.discount,
        outgo=rec.outgo,
        ngwp=rec.ngwp,
        smethode=rec.smethode or "PAA",
    )


def inforce_to_policies(
    parsed: ParsedInforce,
    active_only: bool = True,
) -> list[PolicyRecord]:
    """
    Konversi seluruh ParsedInforce ke list PolicyRecord.

    Args:
        parsed: Hasil parsing file inforce.
        active_only: Jika True, hanya polis aktif yang di-convert.

    Returns:
        List PolicyRecord siap diproses oleh BatchService.
    """
    policies: list[PolicyRecord] = []
    skipped = 0

    for rec in parsed.records:
        if active_only and not rec.is_active:
            skipped += 1
            continue
        pol = inforce_record_to_policy(rec)
        policies.append(pol)

    logger.info(
        f"Converted {len(policies)} inforce records to PolicyRecord "
        f"(skipped {skipped} inactive, year={parsed.year}, month={parsed.month})"
    )
    return policies


def multi_inforce_to_policies(
    inforce_data: dict[str, ParsedInforce],
    active_only: bool = True,
) -> tuple[list[PolicyRecord], dict[str, Any]]:
    """
    Konversi multiple ParsedInforce (dari session) ke satu list PolicyRecord.

    Menggabungkan semua bulan/tahun, de-duplicate berdasarkan policyno
    (mengambil record terbaru berdasarkan valdate).

    Args:
        inforce_data: Dict key -> ParsedInforce dari session.
        active_only: Jika True, hanya polis aktif.

    Returns:
        Tuple of (policies, stats).
    """
    # Collect all records with their period info
    all_records: dict[str, tuple[PolicyRecord, int, int]] = {}
    total_raw = 0
    periods_processed = []

    for key, parsed in sorted(inforce_data.items()):
        policies = inforce_to_policies(parsed, active_only=active_only)
        total_raw += len(policies)
        periods_processed.append(key)

        for pol in policies:
            existing = all_records.get(pol.policyno)
            if existing is None:
                all_records[pol.policyno] = (pol, parsed.year, parsed.month)
            else:
                # Ambil yang terbaru berdasarkan valdate
                _, ex_year, ex_month = existing
                cur_period = (parsed.year, parsed.month)
                ex_period = (ex_year, ex_month)
                if cur_period > ex_period:
                    all_records[pol.policyno] = (pol, parsed.year, parsed.month)

    policies = [rec for rec, _, _ in all_records.values()]

    stats = {
        "total_raw_records": total_raw,
        "unique_policies": len(policies),
        "duplicates_resolved": total_raw - len(policies),
        "periods_processed": periods_processed,
    }

    logger.info(
        f"Multi-inforce conversion: {total_raw} raw → {len(policies)} unique policies "
        f"from {len(periods_processed)} periods"
    )

    return policies, stats
