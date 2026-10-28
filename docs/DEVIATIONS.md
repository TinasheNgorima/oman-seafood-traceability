# Deviations from the analysis plan, and changes in analysis decisions

Source of the plan: `SEM_SPEC_layer1.md` (copied here as found in the pipeline folder). The plan text is unaltered. The estimation addendum dated 9 June 2026 is appended at the end.

Terminology. The plan file uses "pre-registration" and "pre-registered" for this internal analysis plan. The plan was not lodged with a registry, and no registration identifier exists. The chapter therefore describes the model as "specified in the analysis plan".

## A. Layer 1 deviations from `SEM_SPEC_layer1.md`

| # | Plan | What was done | Reason | Where in code |
|---|---|---|---|---|
| D1 | Four constructs (PC, PM, ER, SV) | Production Modernization dropped. Model is PC -> ER -> SV | Fleet shares exist only for the unattributed bucket, so PM indicators have zero between-governorate variance | `05_sem_layer1.py` |
| D2 | n = 88 (11 governorates x 8 years) | n = 48 (6 governorates x 8 years) | The source file has six governorates with non-zero catch plus the bucket in D3 | `05_sem_layer1.py` |
| D3 | The seventh region label treated as a "national-aggregate row" | It holds **all Coastal and Commercial fleet records** (343.6 kt, 1% of catch in 2017 and 10% in 2024). The six governorates hold only Artisanal records. The row is not a duplicate total. | Found on audit, 22 Oct 2026 | `01` keeps it (national totals and sector shares are correct, governorate HHI treats it as a seventh unit). `05` drops it, so the SEM panel measures artisanal catch only. Sensitivity: `outputs/layer1_gov_hhi_sensitivity.csv` |
| D4 | WLSMV estimator | ML (Wishart) in semopy | All indicators are continuous | `05_sem_layer1.py` |
| D5 | Latent SEM as the estimate | Latent form fitted and reported (CFI 0.649, RMSEA 0.482), then replaced by a composite-indicator OLS path model with governorate-clustered SEs and a 5,000-replication cluster bootstrap | n = 48 is too small for 9 indicators and 3 constructs | `05_sem_layer1.py`, `05b_path_layer1.py` |
| D6 | Decision B3: clustered SEs | Honoured | | `05b` |
| D7 | Decision B1: unit_value in ER | Honoured. ER Cronbach alpha is -0.31 | | `05`, `05b` |
| D8 | Bias-corrected bootstrap intervals | Percentile intervals (2.5, 97.5) | Simpler under 6 clusters | `05b` |
| D9 | Sobel z | Not computed | The planned indirect path ran through PM, which was dropped (D1). For PC → ER → SV, the normal-theory Sobel test ignores clustering and is unreliable at n = 48, so inference uses the cluster bootstrap only. | |
| D10 | The addendum calls the Layer 1 pathway "Proposition 4" and records it as not supported | The chapter reports this pathway as an exploratory question (§5.4, §7.1). The chapter's separate joint production–network proposition is restated as a question for further work and is not tested. | n = 48 cannot support a confirmatory test, and no data overlap the restriction period. | |

## B. Layer 3 analysis decisions that changed during the project

These are not deviations from the SEM plan. They are listed because they changed reported results.

| Date | Decision | Effect |
|---|---|---|
| Early June 2026 | D_BAN = 1 for 2011-2014 only. Bose Table 2 ends in 2014 | S2 D_BAN = -0.594, S3 = -0.465, D_NTB(S2) = +0.292 (p = .06) |
| After the MJLA Official Gazette catalogue check | D_BAN = 1 for 2011-2024. Annual re-issues 2015-2018 and the standing regime of MD 75/2019 from 2019. MD 230/2014 kingfish fishing closure excluded as a domestic conservation measure | S2 D_BAN = -0.580, S3 = -0.579, D_NTB(S2) = +0.005 (p = .96). These are the chapter's values. |

Both versions were estimated on the same trade data. The recode, not the estimator, moved the extended-window results.

## C. Analyses added in response to peer review (October 2026)

None of these analyses was in the analysis plan. They were added after peer review and are reported as robustness checks. All read committed `outputs/` files only, so they run in derived-only mode. Parameters are in `config/config.yaml` (`layer3` and `layer2`).

| Analysis | Reviewer point | Script | Output |
|---|---|---|---|
| S4: D_BAN split into 2011–2018 and 2019–2024 regimes, with D_NTB and D_NTB_max, Wald test of equality | 2 | `03b_layer3_robustness.py` | `layer3_regime_split.csv`, `layer3_pct_effect.csv` |
| Unit-root tests (ADF, KPSS) on ln V and ln ER, Engle–Granger cointegration test | 3 | `03b_layer3_robustness.py` | `layer3_unit_roots.csv` |
| Residual tests for S1–S4 (Breusch–Godfrey, Durbin–Watson, Durbin's h) | 3 | `03b_layer3_robustness.py` | `layer3_residual_tests.csv` |
| Break-date scan, earlier steps, linear trend and pre-window placebos | 3 | `03b_layer3_robustness.py` | `layer3_break_scan.csv`, `layer3_placebo.csv` |
| Network edge-weight reweighting, 10,000 draws | 4 | `04b_layer2_sensitivity.py` | `layer2_reweight_summary.csv` |
| Leave-one-edge-out, unit weights and node merges | 4 | `04b_layer2_sensitivity.py` | `layer2_leave_one_out.csv`, `layer2_unweighted.csv`, `layer2_node_merge.csv` |
| Eigenvector centrality against weighted degree | 4 | `04b_layer2_sensitivity.py` | `layer2_eig_vs_degree.csv` |
