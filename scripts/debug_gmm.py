"""Cek detail hasil kalkulasi GMM per polis."""
import httpx, os

API = "http://localhost:8000/api/v1"
KEY = {"X-API-Key": "psak117-dev-secret-key-ganti-di-production"}
SAMPLES = r"d:\Web\Actuarial Engine\data\samples"
MT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

files_map = [
    ("portfolio", "00-Templateupload.xlsx"),
    ("assumptions", "01-templateassumption.xlsx"),
    ("tabphei", "02-templatetabphei.xlsx"),
    ("lapse", "03-templatelapse.xlsx"),
]

for endpoint, fname in files_map:
    with open(os.path.join(SAMPLES, fname), "rb") as f:
        httpx.post(f"{API}/upload/{endpoint}", headers=KEY, files={"file": (fname, f, MT)})

r = httpx.post(f"{API}/upload/batch-calculate", headers=KEY, json={}, timeout=60.0)
d = r.json()

print("=== DETAIL PER POLIS ===")
fmt = lambda n: f"{n:>15,.2f}" if isinstance(n, (int, float)) else str(n)
for res in d.get("results", []):
    m = res.get("method", "")
    if m == "GMM":
        gwp = res.get("gwp", 0)
        tsi = res.get("tsi", 0)
        pvfcf = res.get("pvfcf", 0)
        ra = res.get("risk_adjustment", 0)
        csm = res.get("csm", 0)
        icl = res.get("insurance_contract_liability", 0)
        onerous = res.get("is_onerous", False)
        pno = res.get("policyno", "?")
        print(f"\n[GMM] {pno}")
        print(f"  GWP/yr={gwp:,.0f}  TSI={tsi:,.0f}")
        print(f"  PVFCF  ={fmt(pvfcf)}")
        print(f"  RA     ={fmt(ra)}")
        print(f"  CSM    ={fmt(csm)}")
        print(f"  ICL    ={fmt(icl)}")
        print(f"  Onerous={onerous}")
        print(f"  qx base={(0.26 * gwp / tsi) if tsi else 0:.4%}")
