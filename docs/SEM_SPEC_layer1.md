# Layer 1 SEM — Specification for Review

## Sample
- Unit of analysis: governorate × year cell, fisheries-production dataset
- Available years: 2017–2024 (n = 8 years)
- Governorates: 11 with non-zero catch
- Effective n (governorate × year): 88
- Estimator: WLSMV (continuous + ordinal mix is not required here; all
  observed indicators are continuous), with FIML for any missing cells.
- Software: `semopy` (Python). All exogenous covariates standardised
  before estimation. Constructs identified via fixed unit-loading
  (first indicator loading set to 1).

The framework document specifies four latent constructs.

## Latent constructs and observed indicators

### Production Capacity (PC)
Magnitude of fisheries output absorbed by the governorate per year.
1. `catch_log`  = log(catch_tonnes + 1)
2. `value_log`  = log(value_omr_thousands + 1)
3. `record_density` = log(n_observation_rows + 1) — proxy for the
   number of distinct species × month landings reported

### Production Modernisation (PM)
Shift from artisanal toward coastal and commercial fleets.
1. `commercial_share` = catch_commercial / catch_total
2. `coastal_share`    = catch_coastal    / catch_total
3. `artisanal_share_neg` = −(catch_artisanal / catch_total)   ⟵ inverted

The artisanal share is sign-flipped so all three indicators load
positively on PM.

### Export Readiness (ER)
Concentration on tradable, high-value species at the governorate level.
1. `tuna_share`        = catch_(tuna species, HIGH) / catch_total
2. `pelagic_share`     = catch_(pelagic, HIGH)      / catch_total
3. `unit_value`        = value_omr_thousands / catch_tonnes

"Tuna species" = HIGH-confidence species mapped to genera *Thunnus*,
*Euthynnus*, *Sarda*, *Auxis*, *Katsuwonus*.

### SPS Vulnerability (SV)
Structural exposure to SPS-relevant disruption.
1. `species_hhi_high`  = HIGH-confidence species HHI
2. `seasonality_cv`    = within-year monthly catch CV
3. `concentration_top1`= share of largest single species in the
   governorate-year

## Structural model

```
PM  ~ PC                                                (β1)
ER  ~ PC + PM                                          (β2, β3)
SV  ~ PC + ER                                          (β4, β5)
```

Indirect effect of interest: PC → PM → ER → SV. Sobel z and 5,000
bias-corrected bootstrap intervals on the product-of-coefficients
path.

## Identification

- Each latent has ≥ 3 indicators (counting rule satisfied).
- All loadings free except the first per construct (scaling).
- Residual covariances permitted within the same data-source block:
  - cov(catch_log, value_log) — both from the catch ledger
  - cov(tuna_share, pelagic_share) — both pelagic-derived
  - cov(species_hhi_high, concentration_top1) — algebraically related,
    flagged as a non-zero covariance to avoid spurious common loading
- All other residual covariances fixed at zero.

## Fit criteria (Q1 reporting threshold)

| Index             | Threshold        |
|---|---|
| Robust χ² / df    | ≤ 3.0            |
| CFI               | ≥ 0.95           |
| TLI               | ≥ 0.95           |
| RMSEA (90% CI)    | ≤ 0.08 (≤ 0.06 preferred) |
| SRMR              | ≤ 0.08           |

## Pre-registration commitments

1. Indicator set is locked at the values above. Re-specification on the
   basis of modification indices is not permitted; any indicator
   removal will be reported as a robustness sub-model alongside the
   original.
2. Bootstrap iterations: 5,000. Seed: 20260930.
3. Limitations to be reported irrespective of fit:
   - n_years = 8 limits temporal generalisability and rules out
     cross-lagged effects beyond a one-period structure.
   - Governorate-level aggregation conceals within-governorate
     establishment heterogeneity.
   - Indicators for ER and SV partially overlap mechanically; the
     residual covariance between `species_hhi_high` and
     `concentration_top1` is one mitigation.

## Confirmed decisions

All specification decisions are closed (confirmed B1–B3); the model is
estimation-ready.

- **B1.** `unit_value` (OMR/kg) is retained as an indicator of Export
  Readiness (ER), not as a separate Market Value latent and not as an
  indicator of SPS Vulnerability. Theoretical rationale documented inline
  in Section 6.2 of the chapter.
- **B2.** 2024 is retained. The MAFWR annual database is confirmed
  complete for 2024; the analytical sample is n = 88 governorate-year
  observations (2017–2024).
- **B3.** Governorate variance is absorbed via clustered standard errors
  at the governorate level (Cameron & Miller, 2015) rather than
  governorate fixed effects, preserving the between-governorate variance
  required to identify Proposition 4.

---

## Estimation addendum (2026-06-09)

The pre-registration above is retained unaltered. This addendum records
what was estimable against the delivered MAFWR file
(`Oman_Layer1_Clean_EN_v2.xlsx`) and the deviations forced by the data.

**Sample.** n = 48, not 88. The source file contains six governorates
with non-zero catch plus a seventh "All Governorates" national-aggregate
row, which is excluded. Effective sample is 6 governorates × 8 years.

**Production Modernisation dropped.** Sector composition (artisanal,
coastal, commercial shares) is reported only at the national "All
Governorates" level. At the governorate level these three PM indicators
have zero between-governorate variance and cannot be identified. The
estimated structural model is therefore three-construct: PC → ER → SV,
with paths `ER ~ PC` and `SV ~ PC + ER` and indirect effect
PC → ER → SV.

**Estimator.** WLSMV was pre-registered on the assumption it would be
needed; all observed indicators are continuous, so WLSMV does not apply.
The latent form was fitted by maximum likelihood (semopy, Wishart
objective). It is reported as a pre-registered specification rather than
a confirmatory result: at n = 48 the sample-size-to-parameter ratio is
below the level at which the global fit indices are interpretable, and
the fitted model returned CFI = 0.65 and RMSEA = 0.48.

**Primary estimable specification.** The production pathway is reported
as a composite-indicator path model. Each construct is the standardised
mean of its (standardised) indicators. Structural coefficients are
estimated by OLS in statsmodels (Seabold & Perktold, 2010) with standard
errors clustered at the governorate level (Cameron & Miller, 2015). The
indirect effect is assessed by a 5,000-replication cluster bootstrap
(seed 20260930), resampling governorates.

**Result.** The Export Readiness composite is not internally consistent
(Cronbach α below zero), `PC → ER` is null (β = −0.04, p = 0.91), and the
indirect effect is 0.02 with a 95% cluster-bootstrap interval of
[−0.32, 0.47]. Proposition 4 is not supported in these data. Both PC
(α = 0.68) and SV (α = 0.90) cohere acceptably. SV ~ ER (β = −0.64) and
SV ~ PC (β = 0.41) are precisely estimated but share a catch-share
denominator and are not interpreted as structural evidence.

**Scripts.** `05_sem_layer1.py` builds the panel and fits the latent
form; `05b_path_layer1.py` reads that panel and estimates the composite
path model. Both are registered in `run_all.py` after
`01_descriptive_layer1.py`.

**Status of B1–B3.** B1 (unit_value in ER) and B3 (clustered SEs) are
honoured. B2 is revised: 2024 is retained, but the sample is n = 48, not
n = 88.
