"""Test upload sample files end-to-end."""
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

print("=== UPLOAD SAMPLE FILES ===")
for endpoint, fname in files_map:
    with open(os.path.join(SAMPLES, fname), "rb") as f:
        r = httpx.post(f"{API}/upload/{endpoint}", headers=KEY,
                       files={"file": (fname, f, MT)})
    d = r.json()
    status = "OK" if r.status_code == 200 else "ERROR"
    print(f"  {fname}: {status} | {d.get('rows_parsed', 'N/A')} rows | errors={d.get('errors', [])}")

print("\n=== BATCH CALCULATE ===")
r = httpx.post(f"{API}/upload/batch-calculate", headers=KEY, json={}, timeout=60.0)
if r.status_code == 200:
    d = r.json()
    s = d.get("statistics", {})
    print(f"  batch_id: {d.get('batch_id', '')[:16]}...")
    print(f"  Total: {s.get('total')} | Sukses: {s.get('success')} | Error: {s.get('error')}")
    print(f"  PAA: {s.get('paa_count')} | GMM: {s.get('gmm_count')}")
    print(f"  Total ICL: Rp {s.get('total_icl', 0):,.0f}")
    print(f"  Total LRC: Rp {s.get('total_lrc', 0):,.0f}")
    print(f"  Total LIC: Rp {s.get('total_lic', 0):,.0f}")
else:
    print(f"  ERROR {r.status_code}: {r.text[:200]}")
