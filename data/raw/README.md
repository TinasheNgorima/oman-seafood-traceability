# data/raw

The two raw workbooks are **not distributed** with this repository. Obtain them as described in `../README.md` and place them here under these exact names:

- `Oman_Layer1_Clean_EN_v2.xlsx`
- `Oman_Layer23_Bose2017_Extract.xlsx`

`checksums.sha256` lists the SHA-256 of the files used for the chapter. `tests/test_pipeline.py` checks any workbook present against it. Without the workbooks, `scripts/run_all.py` runs in derived-only mode and reads the committed `outputs/` files.
