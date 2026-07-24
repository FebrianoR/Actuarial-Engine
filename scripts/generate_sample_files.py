"""
Generate sample Excel files PSAK 117 – versi baru (v2).
Data lebih realistis: 20 polis, yield curve per tenor, lapse TMI-3.
Saved ke: data/samples/
"""
import os
from datetime import date, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_DIR = r"d:\Web\Actuarial Engine\data\samples"
os.makedirs(OUT_DIR, exist_ok=True)

HEADER_COLOR = "1B3A6B"
ALT_COLOR    = "EBF3FB"
GREEN_DARK   = "1A5276"
WHITE        = "FFFFFF"

def hdr(cell, color=HEADER_COLOR):
    cell.font = Font(bold=True, color=WHITE, size=10)
    cell.fill = PatternFill("solid", fgColor=color)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def bdr(cell):
    s = Side(style="thin", color="CCCCCC")
    cell.border = Border(left=s, right=s, top=s, bottom=s)

def alt(cell, ri):
    if ri % 2 == 0:
        cell.fill = PatternFill("solid", fgColor=ALT_COLOR)

def write_row(ws, ri, values, fmt_map=None):
    for ci, val in enumerate(values, 1):
        c = ws.cell(row=ri, column=ci, value=val)
        bdr(c)
        alt(c, ri)
        if fmt_map and ci in fmt_map:
            c.number_format = fmt_map[ci]
    return ri + 1


# ────────────────────────────────────────────────────────────────────────────
# 00 – Data Polis (20 polis: 10 PAA + 10 GMM, berbagai COB)
# ────────────────────────────────────────────────────────────────────────────
def create_00_portfolio():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "datapolis"

    cols = [
        "sguser","id","batchnr","cob","product","sob","mkt","uw",
        "policyno","begindt","enddt","begindtlt","valdate",
        "stspolis","aktif","tsi","gwp","discount","outgo","ngwp",
        "ripremi","ricom","ripreminett","grace","smethode",
        "insured_age","insured_sex","duration_years"
    ]
    widths = [8,5,8,6,10,4,5,5,15,11,11,11,11,8,5,16,12,8,8,12,8,8,12,5,8,10,5,12]
    for ci, (h, w) in enumerate(zip(cols, widths), 1):
        c = ws.cell(row=1, column=ci, value=h)
        hdr(c)
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.row_dimensions[1].height = 24

    val = date(2024, 12, 31)

    # ── PAA Policies (10 polis, COB CSA – asuransi jangka pendek) ──────────
    paa = [
        # (policyno, begindt, enddt, TSI, GWP, age, sex)
        ("11052504741", date(2024,1,1),  date(2025,1,1),  50_000_000,    500_000, 32,"L"),
        ("11052504742", date(2024,2,15), date(2025,2,14), 75_000_000,    750_000, 45,"P"),
        ("11052504743", date(2024,3,1),  date(2025,2,28), 100_000_000, 1_000_000, 28,"L"),
        ("11052504744", date(2024,4,1),  date(2025,3,31), 150_000_000, 1_500_000, 51,"P"),
        ("11052504745", date(2024,5,9),  date(2025,5,8),  200_000_000, 2_000_000, 39,"L"),
        ("11052504746", date(2024,6,1),  date(2025,5,31), 500_000_000, 5_000_000, 55,"P"),
        ("11052504747", date(2024,7,15), date(2025,7,14),  25_000_000,   250_000, 27,"L"),
        ("11052504748", date(2024,8,1),  date(2025,7,31),  80_000_000,   800_000, 42,"P"),
        ("11052504749", date(2024,9,1),  date(2025,8,31), 120_000_000, 1_200_000, 36,"L"),
        ("11052504750", date(2024,10,1), date(2025,9,30), 300_000_000, 3_000_000, 48,"P"),
    ]
    ri = 2
    for i, (pno, bdt, edt, tsi, gwp, age, sex) in enumerate(paa, 1):
        row = ("ARI", str(i), "B2024", "CSA", "CSA.PROPERTY", "D", "AM", "UW",
               pno, bdt, edt, bdt, val,
               "A", 1, tsi, gwp, 0, 0, gwp, 0, 0, 0, 0, "PAA",
               age, sex, 1)
        ri = write_row(ws, ri, row, {10:"DD-MM-YYYY", 11:"DD-MM-YYYY", 13:"DD-MM-YYYY"})

    # ── GMM Policies (10 polis, COB V=jiwa, A=kecelakaan, B=kesehatan) ──────
    gmm = [
        # (policyno, cob, product, begindt, enddt, TSI, GWP, age, sex, dur)
        ("22010100001","V","JIWA20T",  date(2022,1,1), date(2042,1,1), 200_000_000, 10_000_000, 30,"L",20),
        ("22010100002","V","JIWA20T",  date(2021,6,15),date(2041,6,15),150_000_000,  7_500_000, 35,"P",20),
        ("22010100003","V","JIWA10T",  date(2023,3,1), date(2033,3,1), 100_000_000,  5_000_000, 40,"L",10),
        ("22010100004","V","JIWA10T",  date(2020,8,1), date(2030,8,1), 500_000_000, 25_000_000, 25,"P",10),
        ("22020100001","V","JIWA15T",  date(2019,5,1), date(2034,5,1), 300_000_000, 15_000_000, 45,"L",15),
        ("33010200001","A","KEC5T",    date(2023,1,1), date(2028,1,1),  50_000_000,  2_000_000, 32,"L", 5),
        ("33010200002","A","KEC5T",    date(2022,7,1), date(2027,7,1),  75_000_000,  3_000_000, 28,"P", 5),
        ("44010300001","B","KES3T",    date(2023,6,1), date(2026,6,1),  30_000_000,  3_600_000, 38,"L", 3),
        ("44010300002","B","KES3T",    date(2022,1,1), date(2025,1,1),  25_000_000,  3_000_000, 50,"P", 3),
        ("44010300003","B","KES5T",    date(2022,4,1), date(2027,4,1),  40_000_000,  4_800_000, 35,"L", 5),
    ]
    for i, (pno, cob, prod, bdt, edt, tsi, gwp, age, sex, dur) in enumerate(gmm, 11):
        row = ("ARI", str(i), "B2024", cob, prod, "D", "AM", "UW",
               pno, bdt, edt, bdt, val,
               "A", 1, tsi, gwp, 0, 0, gwp, 0, 0, 0, 0, "GMM",
               age, sex, dur)
        ri = write_row(ws, ri, row, {10:"DD-MM-YYYY", 11:"DD-MM-YYYY", 13:"DD-MM-YYYY"})

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}1"
    wb.save(os.path.join(OUT_DIR, "00-Templateupload.xlsx"))
    print("✓ 00-Templateupload.xlsx  (20 polis: 10 PAA[CSA] + 10 GMM[V,A,B])")


# ────────────────────────────────────────────────────────────────────────────
# 01 – Asumsi Aktuaria (per COB per tahun, lengkap)
# ────────────────────────────────────────────────────────────────────────────
def create_01_assumptions():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "assumsi"

    cols = ["sguser","cob","syear","expclaim","expopex","expriskadj"]
    widths = [10, 8, 8, 16, 16, 16]
    for ci, (h, w) in enumerate(zip(cols, widths), 1):
        c = ws.cell(row=1, column=ci, value=h)
        hdr(c)
        ws.column_dimensions[get_column_letter(ci)].width = w

    # Asumsi per COB per tahun – nilai lebih realistis berbasis TMI-3 & data industri
    # expclaim = claim ratio thd premi, expopex = expense ratio, expriskadj = RA/capital ratio
    data = [
        # CSA (Property/Casualty singkat): claim ratio ~14-18%, expense ~2.5%, RA ~20-25%
        ("ARI","CSA",2022, 0.1477, 0.025, 0.2453),
        ("ARI","CSA",2023, 0.1550, 0.025, 0.2350),
        ("ARI","CSA",2024, 0.1620, 0.025, 0.2200),
        # V (Jiwa): claim ratio ~25-28%, expense 5%, RA ~14-16%
        ("ARI","V",  2022, 0.2472, 0.050, 0.1534),
        ("ARI","V",  2023, 0.2550, 0.050, 0.1480),
        ("ARI","V",  2024, 0.2600, 0.050, 0.1450),
        # A (Kecelakaan): claim ratio ~30-38%, expense 3%, RA ~15-18%
        ("ARI","A",  2022, 0.3100, 0.030, 0.1750),
        ("ARI","A",  2023, 0.3350, 0.030, 0.1700),
        ("ARI","A",  2024, 0.3500, 0.030, 0.1650),
        # B (Kesehatan): claim ratio ~55-65%, expense 3.5%, RA ~12-15%
        ("ARI","B",  2022, 0.5500, 0.035, 0.1450),
        ("ARI","B",  2023, 0.5750, 0.035, 0.1400),
        ("ARI","B",  2024, 0.6000, 0.035, 0.1350),
    ]

    ri = 2
    for row in data:
        for ci, val in enumerate(row, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            if isinstance(val, float):
                c.number_format = "0.0000"
            bdr(c); alt(c, ri)
        ri += 1

    ws.freeze_panes = "A2"
    wb.save(os.path.join(OUT_DIR, "01-templateassumption.xlsx"))
    print("✓ 01-templateassumption.xlsx  (12 baris: COB CSA, V, A, B × 2022-2024)")


# ────────────────────────────────────────────────────────────────────────────
# 02 – Yield Curve PHEI (per tanggal akhir bulan, 2022-2024)
# ────────────────────────────────────────────────────────────────────────────
def create_02_tabphei():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "lrc_tabphei"

    cols = ["sguser","syear","sdate","srate"]
    widths = [10, 8, 14, 12]
    for ci, (h, w) in enumerate(zip(cols, widths), 1):
        c = ws.cell(row=1, column=ci, value=h)
        hdr(c)
        ws.column_dimensions[get_column_letter(ci)].width = w

    # OJK PHEI yield curve – 1yr spot rate per akhir bulan 2022-2024
    # (data representatif berdasarkan tren suku bunga OJK Indonesia)
    monthly_rates = {
        2022: [5.52, 5.60, 5.70, 5.78, 5.88, 6.05, 6.15, 6.28, 6.38, 6.45, 6.52, 6.58],
        2023: [6.55, 6.48, 6.52, 6.58, 6.62, 6.68, 6.72, 6.78, 6.82, 6.88, 6.92, 6.97],
        2024: [6.93, 6.88, 6.82, 6.76, 6.71, 6.65, 6.60, 6.54, 6.50, 6.46, 6.42, 6.38],
    }

    ri = 2
    for si, yr in enumerate([2022, 2023, 2024]):
        for month in range(1, 13):
            if month == 12:
                last_day = date(yr, 12, 31)
            else:
                last_day = date(yr, month + 1, 1) - timedelta(days=1)

            rate = monthly_rates[yr][month - 1]
            row  = ("ARI", si, last_day, round(rate, 4))
            for ci, val in enumerate(row, 1):
                c = ws.cell(row=ri, column=ci, value=val)
                if ci == 3:
                    c.number_format = "DD-MM-YYYY"
                elif ci == 4:
                    c.number_format = "0.0000"
                bdr(c); alt(c, ri)
            ri += 1

    ws.freeze_panes = "A2"
    wb.save(os.path.join(OUT_DIR, "02-templatetabphei.xlsx"))
    print(f"✓ 02-templatetabphei.xlsx  ({ri-2} baris yield curve 2022-2024)")


# ────────────────────────────────────────────────────────────────────────────
# 03 – Lapse Table (per bulan, per tahun polis, per COB – 8 tahun)
# ────────────────────────────────────────────────────────────────────────────
def create_03_lapse():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "lrc_lapsemmtable"

    cols = ["sguser","syear","smonth","smonth_th","cob","srate"]
    widths = [10, 8, 8, 10, 8, 10]
    for ci, (h, w) in enumerate(zip(cols, widths), 1):
        c = ws.cell(row=1, column=ci, value=h)
        hdr(c)
        ws.column_dimensions[get_column_letter(ci)].width = w

    # Lapse rate per bulan (disetahunkan) – berbasis data industri asuransi jiwa Indonesia
    # Format: {tahun_polis: [lapse_month1..12]}
    lapse_schedule = {
        1: [0.000, 0.000, 0.000, 0.000, 0.000, 0.002, 0.002, 0.003, 0.003, 0.004, 0.004, 0.050],
        2: [0.008, 0.008, 0.008, 0.010, 0.010, 0.010, 0.012, 0.012, 0.012, 0.015, 0.015, 0.015],
        3: [0.012, 0.012, 0.013, 0.013, 0.014, 0.014, 0.015, 0.015, 0.015, 0.016, 0.016, 0.016],
        4: [0.016, 0.016, 0.017, 0.017, 0.018, 0.018, 0.019, 0.019, 0.020, 0.020, 0.020, 0.021],
        5: [0.020, 0.020, 0.021, 0.021, 0.022, 0.022, 0.022, 0.023, 0.023, 0.024, 0.024, 0.025],
        6: [0.022, 0.022, 0.022, 0.023, 0.023, 0.023, 0.024, 0.024, 0.024, 0.025, 0.025, 0.025],
        7: [0.020, 0.020, 0.021, 0.021, 0.021, 0.022, 0.022, 0.022, 0.022, 0.023, 0.023, 0.023],
        8: [0.018, 0.018, 0.019, 0.019, 0.019, 0.020, 0.020, 0.020, 0.020, 0.020, 0.021, 0.021],
    }

    cob_rates = {
        "V":   1.00,  # jiwa: base
        "CSA": 0.30,  # property/casualty: lapse lebih rendah
        "A":   0.80,  # kecelakaan: sedikit lebih rendah dari jiwa
        "B":   1.20,  # kesehatan: lapse lebih tinggi
    }

    ri = 2
    nth = 1
    for syear in range(1, 9):
        months = lapse_schedule.get(syear, [lapse_schedule[8][0]] * 12)
        for smonth, base_rate in enumerate(months, 1):
            for cob, factor in cob_rates.items():
                rate = round(base_rate * factor, 5)
                row = ("ARI", syear, smonth, nth, cob, rate)
                for ci, val in enumerate(row, 1):
                    c = ws.cell(row=ri, column=ci, value=val)
                    if ci == 6:
                        c.number_format = "0.00000"
                    bdr(c); alt(c, ri)
                ri += 1
            nth += 1

    ws.freeze_panes = "A2"
    wb.save(os.path.join(OUT_DIR, "03-templatelapse.xlsx"))
    print(f"✓ 03-templatelapse.xlsx  ({ri-2} baris (8 tahun × 12 bulan × 4 COB))")


if __name__ == "__main__":
    print("Generating sample files v2 (data lebih realistis)...\n")
    create_00_portfolio()
    create_01_assumptions()
    create_02_tabphei()
    create_03_lapse()
    print(f"\n✅ Semua file tersimpan di: {OUT_DIR}")
