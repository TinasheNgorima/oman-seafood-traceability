# Oman seafood traceability: replication repository

[![DOI](https://zenodo.org/badge/1436776664.svg)](https://doi.org/10.5281/zenodo.23725020)

Code, input snapshots and derived data for the book chapter *Seafood Traceability in an Emerging Economy: A Multi-Layer Framework for Food Safety, Sustainability, and Regulatory Compliance in Oman's Export Supply Chains* (T. Ngorima, Sohar University).

[![reproduce](https://github.com/TinasheNgorima/oman-seafood-traceability/actions/workflows/ci.yml/badge.svg)](https://github.com/TinasheNgorima/oman-seafood-traceability/actions)
DOI: *to be added after the first Zenodo release.*

## Data availability

The two raw workbooks are not redistributed. Both come from public sources: the MAFWR production dataset (<https://opendata.gov.om/en/datasets/e454a025-e9f8-4b4c-a77c-2f7cf51ffc52>) and Bose et al. (2017) (<https://doi.org/10.1016/j.marpol.2017.04.013>). The ministerial decisions behind `D_BAN` are on the Ministry of Justice and Legal Affairs site (<https://mjla.gov.om/>) and Decree.om (<https://decree.om/>), indexed in `data/d_ban_decisions.csv`. The Eurostat and ECB series (`data/external/`) and all derived outputs (`outputs/`) are included. Details, rebuild steps and licences: `data/README.md`.

Without the workbooks, `run_all.py` runs in **derived-only mode** and still verifies all 209 chapter figures. With them, it rebuilds every output.

## Reproduce

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python scripts/run_all.py        # about 2 minutes, offline
.venv/bin/python -m pytest -q
```

`semopy` builds from source and fails under recent `pip` and `setuptools` on Python 3.12 and later. Use Python 3.11 with `uv`, as above. The pipeline was run and tested on Linux, Python 3.11, with the versions in `requirements.txt`. Windows and macOS have not been tested.

`python scripts/run_all.py --fetch` refreshes the Eurostat and ECB series from the web. Results can then differ from the chapter.

## What each script produces

| Script | Chapter | Output |
|---|---|---|
| `01_descriptive_layer1.py` | 7.1 six production indicators | `layer1_indicators.xlsx`, `layer1_indicators_long.csv` |
| `05_sem_layer1.py` | 6.2, 7.1 governorate-year panel, latent model (CFI, RMSEA) | `layer1_sem_*.csv` |
| `05b_path_layer1.py` | 7.1 composite path model, alpha, 5,000-replication cluster bootstrap | `layer1_path_results.csv`, `layer1_alpha.csv` |
| `02_bose_replication_panel.py` | 6.4 panel and dummies | `bose_replication_panel.csv` |
| `03_bose_lightweight_replication.py` | 7.3 Table 3 (S1–S3, Newey-West bandwidth 2) | `bose_replication_results.csv`, `.._summary.txt` |
| `03b_layer3_robustness.py` | 6.4, 7.3 S4, unit roots, residual tests, break dates, placebos | `layer3_*.csv` |
| `04_layer2_network.py` | 6.3, 7.2 Table 2 | `layer2_*.csv`, `layer2_network.gexf` |
| `04b_layer2_sensitivity.py` | 6.3, 7.2 reweighting, edge removal, unit weights, node merges | `layer2_reweight_summary.csv`, `layer2_leave_one_out.csv`, `layer2_unweighted.csv`, `layer2_node_merge.csv`, `layer2_eig_vs_degree.csv` |
| `06_figures.py` | Figure 3 | `figures/figure_3_layer2_multigraph.{pdf,png}` |
| `07_verify_chapter_claims.py` | all | `claims_report.csv` (209 figures) |
| `00_fetch_external.py` | 6.4 | refreshes `data/external/` (only with `--fetch`) |

Figures 1 and 2 (conceptual and three-layer diagrams) are drawn by hand and are not generated here.

## Parameters

Every analytical parameter (seed 20260930, ban years, RASFF years, HAC lags, bootstrap replications, estimation windows) is in `config/config.yaml`. `dvc.yaml` encodes the stage graph (`dvc repro`). `dvc dag` parses it without error. `dvc repro` has not been executed.

## Chapter versus pipeline

All 209 figures reported in the chapter agree with the pipeline outputs (`outputs/claims_report.csv`). `docs/DEVIATIONS.md` lists every departure from the Layer 1 analysis plan and every Layer 3 coding change that moved a result. The plan file uses the term "pre-registration" for the internal analysis plan. No registry entry exists (see `docs/DEVIATIONS.md`).

## Provenance

`outputs/run_manifest.json` records Python and package versions, SHA-256 of every input and output, and stage timings. `data/README.md` gives the source link and licence of each input. `outputs/` is committed on purpose: it is the deposited derived data, and CI checks that a fresh run reproduces it to 1e-8.

## Limits

- Results hold for the deposited snapshots. A new Eurostat download may differ.
- The D_BAN coding rests on Gazette decrees listed in `docs/D_BAN_CODING.md`. The per-year decree table is `data/d_ban_decisions.csv`.
- Layer 2 edge weights are counts taken from Bose et al. (2017) and are re-derivable only from the Bose et al. (2017) extract, which is rebuilt from the paper (`data/README.md`). In derived-only mode they are read from `outputs/layer2_*.csv`.
- There is no MLflow tracking. `run_manifest.json` replaces it.

## Citation

See `CITATION.cff`. Code is MIT. Derived data are CC BY 4.0. Raw inputs are not distributed and keep their original terms (`data/README.md`).
