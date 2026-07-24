"""Baca detail template Excel PSAK 117 dan compare dengan implementasi."""
import openpyxl

def read_template(path, label, max_sheets=None):
    wb = openpyxl.load_workbook(path, data_only=True)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Sheets ({len(wb.sheetnames)}): {wb.sheetnames}")
    sheets = wb.sheetnames if max_sheets is None else wb.sheetnames[:max_sheets]
    for sname in sheets:
        ws = wb[sname]
        print(f"\n  --- {sname} ({ws.max_row}r x {ws.max_column}c) ---")
        for r in range(1, min(7, ws.max_row+1)):
            row_vals = [ws.cell(r,c).value for c in range(1, min(15,ws.max_column+1))]
            non_null = [(i+1, str(v)[:30]) for i, v in enumerate(row_vals) if v is not None]
            if non_null:
                print(f"    R{r}: {non_null}")
    wb.close()

# Template LRC GMM
read_template(
    r"d:\Project\PSAK117\template\Template LRC GMM 18062026 test.xlsx",
    "TEMPLATE LRC GMM",
    max_sheets=6
)

# Template PAA
read_template(
    r"d:\Project\PSAK117\template\Template PAA with accretion + LC GMM Check HE 14.04.26 (test).xlsx",
    "TEMPLATE PAA",
    max_sheets=6
)
