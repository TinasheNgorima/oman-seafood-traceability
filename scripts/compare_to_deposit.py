"""Numerically compare freshly generated outputs with a copy of the deposited ones.
Usage: python scripts/compare_to_deposit.py <deposit_dir> [tol]
Byte equality is not required (BLAS builds differ at ~1e-12), numeric equality at tol is."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

dep, tol = Path(sys.argv[1]), float(sys.argv[2]) if len(sys.argv) > 2 else 1e-8
new = Path(__file__).resolve().parents[1] / "outputs"
worst, bad = 0.0, []
for f in sorted(dep.glob("*.csv")):
    if f.name == "claims_report.csv":
        continue
    a, b = pd.read_csv(new / f.name), pd.read_csv(f)
    assert a.shape == b.shape and list(a.columns) == list(b.columns), f.name
    # Columns that mix numbers with text markers (semopy writes "-" for fixed parameters) are read
    # as text. Compare their numeric entries at tol and their text entries exactly.
    for c in a.columns.difference(a.select_dtypes("number").columns):
        na, nb = pd.to_numeric(a[c], errors="coerce"), pd.to_numeric(b[c], errors="coerce")
        if na.notna().any() and na.isna().equals(nb.isna()):
            a[f"{c}__num"], b[f"{c}__num"] = na, nb
            a[c], b[c] = a[c].where(na.isna()), b[c].where(nb.isna())
    n = a.select_dtypes("number").columns
    d = float(np.nanmax(np.abs(a[n].values - b[n].values))) if len(n) else 0.0
    same_text = a.drop(columns=n).fillna("").equals(b.drop(columns=n).fillna(""))
    worst = max(worst, d)
    if d > tol or not same_text:
        bad.append((f.name, d, same_text))
print(f"max numeric difference {worst:.2e}; files outside tolerance: {bad or 'none'}")
sys.exit(1 if bad else 0)
