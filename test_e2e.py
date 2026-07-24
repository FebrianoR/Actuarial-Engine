"""Test end-to-end upload + batch calculate + export."""
import httpx
import os

API = "http://localhost:8000/api/v1"
KEY = {"X-API-Key": "psak117-dev-secret-key-ganti-di-production"}
TMPL = r"d:\Project\PSAK117\template"

print("=== END-TO-END TEST ===")

# 1. Upload portfolio
with open(os.path.join(TMPL, "00-Templateupload.xlsx"), "rb") as f:
    r = httpx.post(
        f"{API}/upload/portfolio", headers=KEY,
        files={"file": ("00-Templateupload.xlsx", f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
d = r.json()
print(f"1. Portfolio: {r.status_code} | {d.get('rows_parsed', 0)} polis | errors={d.get('errors', [])}")
if d.get("preview"):
    print(f"   Preview: {d['preview'][0]}")

# 2. Upload assumptions
with open(os.path.join(TMPL, "01-templateassumption.xlsx"), "rb") as f:
    r = httpx.post(
        f"{API}/upload/assumptions", headers=KEY,
        files={"file": ("01-templateassumption.xlsx", f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
d2 = r.json()
print(f"2. Assumptions: {r.status_code} | {d2.get('rows_parsed', 0)} rows")

# 3. Upload yield curve
with open(os.path.join(TMPL, "02-templatetabphei.xlsx"), "rb") as f:
    r = httpx.post(
        f"{API}/upload/tabphei", headers=KEY,
        files={"file": ("02-templatetabphei.xlsx", f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
d3 = r.json()
print(f"3. Yield Curve: {r.status_code} | {d3.get('rows_parsed', 0)} rows")

# 4. Upload lapse
with open(os.path.join(TMPL, "03-templatelapse.xlsx"), "rb") as f:
    r = httpx.post(
        f"{API}/upload/lapse", headers=KEY,
        files={"file": ("03-templatelapse.xlsx", f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
d4 = r.json()
print(f"4. Lapse: {r.status_code} | {d4.get('rows_parsed', 0)} rows")

# 5. Session status
r5 = httpx.get(f"{API}/upload/session-status", headers=KEY)
print(f"5. Session: {r5.json()}")

# 6. Batch calculate
print("6. Running batch calculate...")
r6 = httpx.post(f"{API}/upload/batch-calculate", headers=KEY, json={}, timeout=120.0)
if r6.status_code == 200:
    bd = r6.json()
    stats = bd.get("statistics", {})
    batch_id = bd.get("batch_id", "")
    print(f"   Status: 200 OK | batch_id={batch_id[:16]}...")
    print(f"   Stats: total={stats.get('total')}, success={stats.get('success')}, "
          f"paa={stats.get('paa_count')}, gmm={stats.get('gmm_count')}, "
          f"total_icl={stats.get('total_icl', 0):,.0f}")

    # 7. Export Excel
    r7 = httpx.get(f"{API}/export/excel/{batch_id}", headers=KEY, timeout=30.0)
    print(f"7. Export Excel: {r7.status_code} | {len(r7.content):,} bytes")
    if r7.status_code == 200:
        with open("test_result.xlsx", "wb") as out:
            out.write(r7.content)
        print("   Saved: test_result.xlsx")

    # 8. Export CSV
    r8 = httpx.get(f"{API}/export/csv/{batch_id}", headers=KEY, timeout=30.0)
    print(f"8. Export CSV: {r8.status_code} | {len(r8.content):,} bytes")
    if r8.status_code == 200:
        with open("test_result.csv", "wb") as out:
            out.write(r8.content)
        print("   Saved: test_result.csv")
else:
    print(f"   ERROR: {r6.status_code}")
    print(r6.text[:500])
