"""
Test vektor audit untuk verifikasi independen hasil kalkulasi BBA.
Format: satu file JSON per skenario, berisi input + expected output.
Digunakan oleh peer reviewer aktuaria untuk memvalidasi engine.
"""

# Cara penggunaan:
# Simpan file di tests/audit_vectors/bba_scenario_01.json dengan format:
# {
#   "scenario": "Kontrak Jiwa 20 Tahun – Profitable",
#   "assumption_version": "2024.Q4.1",
#   "input": { ... },
#   "expected": {
#     "pvfcf": 1234567.89,
#     "risk_adjustment": 150000.0,
#     "csm": 200000.0,
#     "insurance_contract_liability": 1584567.89
#   },
#   "tolerance": 1.0,
#   "reviewer": "Aktuaris Berwenang – No. FSAI: XXXX",
#   "review_date": "2024-10-15",
#   "spa04_reference": "SPA-04 Bagian 4.2 – Verifikasi Model"
# }

AUDIT_VECTOR_DIR: str = "tests/audit_vectors/"
