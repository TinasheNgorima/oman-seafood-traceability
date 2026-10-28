"""
run_all.py - reproduces every table, figure and statistic in the chapter.

    python scripts/run_all.py            # offline: uses the deposited Eurostat/ECB snapshots
    python scripts/run_all.py --fetch    # also re-downloads Eurostat COMEXT and ECB (network; may change results)

Derived-only mode: the two raw workbooks (data/raw/*.xlsx) are not distributed. If they are absent,
stages 01, 05 and 04 are skipped and the committed outputs/ files they would write are used as inputs
to the remaining stages. Place the workbooks in data/raw/ (see data/README.md) for a full rebuild.

Stage order (each stage reads only data/ and earlier outputs/):
    01  Layer 1 descriptive indicators                   -> outputs/layer1_indicators*.{xlsx,csv}
    05  Layer 1 latent SEM (semopy, ML-Wishart)          -> outputs/layer1_sem_{panel,estimates,fit}.csv
    05b Layer 1 composite path model + cluster bootstrap -> outputs/layer1_path_results.csv
    02  Layer 3 panel assembly                           -> outputs/bose_replication_panel.csv
    03  Layer 3 OLS, three specifications (HAC, bw=2)    -> outputs/bose_replication_{results.csv,summary.txt}
    03b Layer 3 robustness: S4 regime split, unit roots,
        residual tests, break dates, placebos            -> outputs/layer3_*.csv
    04  Layer 2 institutional network + centrality       -> outputs/layer2_*.csv, layer2_network.gexf
    04b Layer 2 sensitivity: reweighting, edge removal,
        unit weights, node merges, degree comparison     -> outputs/layer2_{reweight_summary,leave_one_out,
                                                            unweighted,node_merge,eig_vs_degree}.csv
    06  Figure 3 (Layer 2 multigraph)                    -> outputs/figures/
    07  Compare every number in the chapter with outputs -> outputs/claims_report.csv

Writes outputs/run_manifest.json (package versions, input and output SHA-256, per-stage timings).
"""
import hashlib
import json
import platform
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

from common import ROOT, OUT, RAW, EXT, IN

SCRIPTS = ["01_descriptive_layer1.py", "05_sem_layer1.py", "05b_path_layer1.py",
           "02_bose_replication_panel.py", "03_bose_lightweight_replication.py", "03b_layer3_robustness.py",
           "04_layer2_network.py", "04b_layer2_sensitivity.py", "06_figures.py", "07_verify_chapter_claims.py"]
NEEDS_RAW = {"01_descriptive_layer1.py": "layer1_xlsx", "05_sem_layer1.py": "layer1_xlsx",
              "04_layer2_network.py": "layer23_xlsx"}
PKGS = ["pandas", "numpy", "scipy", "statsmodels", "semopy", "networkx", "matplotlib", "openpyxl", "PyYAML"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    fetch = "--fetch" in sys.argv
    scripts = (["00_fetch_external.py"] if fetch else []) + SCRIPTS
    here = Path(__file__).parent
    timings = {}
    t0 = time.time()
    skipped = []
    for s in scripts:
        if s in NEEDS_RAW and not (RAW / IN[NEEDS_RAW[s]]).exists():
            print(f"\n=== {s}: SKIPPED (data/raw/{IN[NEEDS_RAW[s]]} not present, using committed outputs) ===")
            skipped.append(s)
            continue
        print(f"\n=== {s} ===", flush=True)
        t = time.time()
        rc = subprocess.run([sys.executable, str(here / s)], cwd=ROOT).returncode
        timings[s] = round(time.time() - t, 1)
        if rc != 0:
            print(f"FAILED at {s} (exit {rc})")
            return rc
    total = round(time.time() - t0, 1)
    manifest = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: metadata.version(p) for p in PKGS},
        "fetched_fresh_external_data": fetch,
        "mode": "derived-only" if skipped else "full",
        "skipped_stages": skipped,
        "inputs_sha256": {str(p.relative_to(ROOT)): sha(p)
                          for p in sorted(list(RAW.glob("*.xlsx")) + list(EXT.glob("*.csv")))},
        "outputs_sha256": {str(p.relative_to(ROOT)): sha(p)
                           for p in sorted(OUT.glob("*.csv")) if p.name != "claims_report.csv"},
        "stage_seconds": timings,
        "total_seconds": total,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nAll stages completed in {total} s ({'derived-only, skipped ' + ', '.join(skipped) if skipped else 'full rebuild'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
