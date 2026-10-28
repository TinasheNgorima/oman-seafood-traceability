# Data sources and access

This repository distributes **code and derived data only**. The two raw workbooks are not redistributed. Each is obtained from its public source below. The pipeline runs without them in derived-only mode (see the last section).

## Inputs

| Input | Used by | Source | Distributed here |
|---|---|---|---|
| `data/raw/Oman_Layer1_Clean_EN_v2.xlsx` | Layer 1 (01, 05) | Ministry of Agriculture, Fisheries and Water Resources (MAFWR), Oman Open Data Platform: <https://opendata.gov.om/en/datasets/e454a025-e9f8-4b4c-a77c-2f7cf51ffc52> | No. Link only |
| `data/raw/Oman_Layer23_Bose2017_Extract.xlsx` | Layer 2 (04) | Bose, S., Al-Yahyai, T., Al-Balushi, M. (2017). *Marine Policy* 82, 93-103: <https://doi.org/10.1016/j.marpol.2017.04.013> | No. Link only |
| Official Gazette decisions behind `D_BAN` | Layer 3 coding (02) | Ministry of Justice and Legal Affairs: <https://mjla.gov.om/>. Decree.om: <https://decree.om/> | Index only: `data/d_ban_decisions.csv` |
| `data/external/eurostat_eu27_imp_oman_hs03_annual_2000_2024.csv` | Layer 3 (02) | Eurostat COMEXT DS-045409 | Yes (CC BY 4.0) |
| `data/external/ecb_eur_per_omr_annual_2000_2024.csv` | Layer 3 (02) | ECB SDW series EXR.A.USD.EUR.SP00.A, converted at 2.6008 USD/OMR | Yes (ECB reuse policy) |

### MAFWR fisheries production (`Oman_Layer1_Clean_EN_v2.xlsx`)

- Content: governorate x month x species catch (tonnes) and value (OMR thousands), 2017-2024, 26,089 rows, sheet `fisheries_production`.
- Download the production dataset from the portal link above. The workbook used in the chapter is a cleaned English version of it, with species identification and an `id_confidence` flag (HIGH, MEDIUM, LOW). The portal download will not be byte-identical to it. `All Governorates` holds all Coastal and Commercial fleet records (`docs/DEVIATIONS.md`, D3).
- The workbook's provenance sheet records the cleaning steps. The author can supply the cleaned workbook on request for audit. It is not deposited.
- Retrieved: 5 May 2026.
- Licence: set by the portal. Not verified here. Cite as: MAFWR (2026), Fisheries production statistics, Oman Open Data Platform.

### Bose et al. (2017) extract (`Oman_Layer23_Bose2017_Extract.xlsx`)

- Content: counts and timelines transcribed by hand from the paper's tables and narrative. Sheets: `regulatory_md_timeline`, `haccp_qc_establishments`, `rasff_notifications`, `export_ban_decisions`, `eu_fvo_findings`.
- Rebuild: read Tables 1-4 and the regulatory narrative in the paper (DOI above) and enter the counts into these sheets. Layer 2 consists of 8 nodes and 13 edges, so the transcription is short.
- Licence: the paper is published by Elsevier. Facts and counts are reusable. The paper's tables are not reproduced here.

### Official Gazette decisions (`D_BAN`)

- `D_BAN` = 1 for 2011-2024. `data/d_ban_decisions.csv` lists, per year, the MJLA decision page (show ID), issue date (d/m/y), subject and whether the decision enters the coding. `docs/D_BAN_CODING.md` explains the rule.
- Open any entry at `https://mjla.gov.om/decisions/<category>/show/<id>`. The same decisions are indexed on Decree.om with the pattern `https://decree.om/<year>/moaf<year><number>/`.
- The PDFs are not redistributed. Download them from the MJLA page for each entry.

## Checksums

| File | SHA-256 |
|---|---|
| `Oman_Layer1_Clean_EN_v2.xlsx` | `8fbe86d6...` (full value in `raw/checksums.sha256`) |
| `Oman_Layer23_Bose2017_Extract.xlsx` | `13cd78bf...` (full value in `raw/checksums.sha256`) |

A rebuilt workbook with different bytes can still be valid. Compare outputs, not hashes: run `python scripts/compare_to_deposit.py <copy of outputs/>`.

## Run modes

- **Full rebuild** (both workbooks in `data/raw/`): all 8 stages run. Outputs match the committed `outputs/` to 1e-8.
- **Derived-only** (workbooks absent): stages 01, 05 and 04 are skipped. Stages 05b, 02, 03, 06 and 07 run from committed `outputs/` and `data/external/`. All 145 chapter figures still verify. `outputs/run_manifest.json` records the mode.

Derived data in `outputs/` are released under CC BY 4.0. Code is MIT.
