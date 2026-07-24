"""Test audit trail setelah fix."""
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

# Upload semua
print("=== UPLOAD ===")
for endpoint, fname in files_map:
    with open(os.path.join(SAMPLES, fname), "rb") as f:
        r = httpx.post(f"{API}/upload/{endpoint}", headers=KEY,
                       files={"file": (fname, f, MT)})
    print(f"  {endpoint}: {r.status_code} | {r.json().get('rows_parsed')} rows")

# Batch calculate
print("\n=== BATCH CALCULATE ===")
r = httpx.post(f"{API}/upload/batch-calculate", headers=KEY, json={}, timeout=60.0)
if r.status_code == 200:
    s = r.json().get("statistics", {})
    print(f"  Total={s.get('total')}, success={s.get('success')}, paa={s.get('paa_count')}, gmm={s.get('gmm_count')}")
else:
    print(f"  ERROR: {r.text[:200]}")

# Cek audit trail
print("\n=== AUDIT TRAIL ===")
r = httpx.get(f"{API}/audit/", headers=KEY)
records = r.json()
print(f"  Total records: {len(records)}")
for rec in records[:3]:
    print(f"  - trace_id: {rec.get('trace_id', '')[:16]}... | type: {rec.get('calculation_type')} | contract: {rec.get('contract_id')}")
    steps = rec.get("steps", {})
    print(f"    steps: {list(steps.keys())[:5]}")
