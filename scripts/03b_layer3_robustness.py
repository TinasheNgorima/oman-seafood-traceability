"""
03b_layer3_robustness.py

Robustness checks on the Layer 3 OLS (03_bose_lightweight_replication.py), added in
response to peer review. None of these analyses was in the analysis plan
(docs/DEVIATIONS.md, Section C). Reads only outputs/bose_replication_panel.csv, so it
runs in derived-only mode. S1-S3 are re-estimated here exactly as in 03 and are not
written back, so the deposited 03 outputs are unchanged.

Checks:
    S4   D_BAN split into regime A (2011-2018) and regime B (2019-2024), estimated
         with D_NTB (conservative) and D_NTB_max (maximalist), Wald test A = B.
    Unit roots on ln V and ln ER, 2000-2024: ADF (constant; constant and trend;
         first difference), KPSS (constant; constant and trend), Engle-Granger.
    Residual tests on the OLS residuals of S1-S4: Breusch-Godfrey, Durbin-Watson,
         Durbin's h.
    Break dates: a step dummy replaces D_BAN in S2 for every start year in
         break_scan. Earlier steps and a linear trend are added to S2 next to D_BAN.
         Placebo steps are estimated inside the pre-restriction window.
    Percentage effect of each restriction dummy, 100[1 - exp(b)], with the
         Kennedy (1981) adjustment 100[1 - exp(b - Var(b)/2)] for comparison.

All standard errors are Newey-West HAC with the bandwidth in config.yaml.

Outputs:
    layer3_regime_split.csv     layer3_unit_roots.csv     layer3_residual_tests.csv
    layer3_break_scan.csv       layer3_placebo.csv        layer3_pct_effect.csv
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import adfuller, coint, kpss

from common import CFG, OUT

# statsmodels >= 0.15 warns that adfuller, kpss and acorr_breusch_godfrey will return result
# objects in a later release. The tuple form is used here because it works in every version.
warnings.filterwarnings("ignore", message=".*returns a plain tuple.*", category=FutureWarning)

L3 = CFG["layer3"]
HAC = {"cov_type": "HAC", "cov_kwds": {"maxlags": L3["hac_maxlags"]}}
W = L3["windows"]
REG = L3["ban_regimes"]

panel = pd.read_csv(OUT / "bose_replication_panel.csv")
est = panel.dropna(subset=["lnV_lag1"]).copy()
est["D_BAN_A"] = est.year.between(*REG["A"]).astype(int)
est["D_BAN_B"] = est.year.between(*REG["B"]).astype(int)
assert (est.D_BAN_A + est.D_BAN_B).equals(est.D_BAN), "regimes must partition the D_BAN years"

# spec -> (window, NTB column, restriction dummies)
SPECS = {
    "S1_Bose_window_2001_2013": (W["S1_Bose_window_2001_2013"], "D_NTB", ["D_BAN"]),
    "S2_Extended_conservative": (W["S2_Extended_conservative"], "D_NTB", ["D_BAN"]),
    "S3_Extended_maximalist": (W["S3_Extended_maximalist"], "D_NTB_max", ["D_BAN"]),
    "S4_Regime_split_conservative": (W["S2_Extended_conservative"], "D_NTB", ["D_BAN_A", "D_BAN_B"]),
    "S4_Regime_split_maximalist": (W["S3_Extended_maximalist"], "D_NTB_max", ["D_BAN_A", "D_BAN_B"]),
}


def design(df, ntb, ban, extra=()):
    return sm.add_constant(df[["lnV_lag1", *ban, ntb, "lnER", "D_crisis", *extra]])


def fit(df, X, hac=True):
    return sm.OLS(df.lnV, X).fit(**HAC) if hac else sm.OLS(df.lnV, X).fit()


def pct(b):
    return 100 * (1 - np.exp(b))


fits = {}
for spec, (win, ntb, ban) in SPECS.items():
    d = est[est.year.between(*win)]
    X = design(d, ntb, ban)
    fits[spec] = (d, X, ntb, ban, fit(d, X), fit(d, X, hac=False))

# ------------------------------------------------------------------ S4 regime split
rows = []
for spec in ("S4_Regime_split_conservative", "S4_Regime_split_maximalist"):
    d, X, ntb, ban, m, _ = fits[spec]
    for v in m.params.index:
        rows.append({"spec": spec, "variable": v, "coef": m.params[v], "hac_se": m.bse[v],
                     "t": m.tvalues[v], "p": m.pvalues[v],
                     "pct_lower": pct(m.params[v]) if v in ban else np.nan})
    w = m.wald_test("D_BAN_A = D_BAN_B", scalar=True, use_f=False)
    rows += [{"spec": spec, "variable": "__WALD_A_EQ_B__", "coef": float(w.statistic), "p": float(w.pvalue)},
             {"spec": spec, "variable": "__N__", "coef": int(m.nobs)},
             {"spec": spec, "variable": "__R2__", "coef": m.rsquared}]
pd.DataFrame(rows).to_csv(OUT / "layer3_regime_split.csv", index=False)

# ------------------------------------------------------------------ unit roots and cointegration
rows = []
for v in ("lnV", "lnER"):
    s = panel[v].to_numpy()
    for reg in ("c", "ct"):
        r = adfuller(s, regression=reg, autolag="AIC")
        rows.append({"series": v, "test": "ADF", "form": "level", "regression": reg, "stat": r[0],
                     "p": r[1], "lags": r[2], "n": len(s), "cv5": r[4]["5%"]})
    r = adfuller(np.diff(s), regression="c", autolag="AIC")
    rows.append({"series": v, "test": "ADF", "form": "first_difference", "regression": "c", "stat": r[0],
                 "p": r[1], "lags": r[2], "n": len(s) - 1, "cv5": r[4]["5%"]})
    for reg in ("c", "ct"):
        with warnings.catch_warnings():      # KPSS p is truncated to [0.01, 0.10] by statsmodels
            warnings.simplefilter("ignore", InterpolationWarning)
            k = kpss(s, regression=reg, nlags="auto")
        rows.append({"series": v, "test": "KPSS", "form": "level", "regression": reg, "stat": k[0],
                     "p": k[1], "lags": k[2], "n": len(s), "cv5": k[3]["5%"]})
eg = coint(panel.lnV, panel.lnER, trend="c")
rows.append({"series": "lnV~lnER", "test": "Engle-Granger", "form": "level", "regression": "c",
             "stat": eg[0], "p": eg[1], "lags": np.nan, "n": len(panel), "cv5": eg[2][1]})
pd.DataFrame(rows).to_csv(OUT / "layer3_unit_roots.csv", index=False)

# ------------------------------------------------------------------ residual autocorrelation
rows = []
for spec, (d, X, ntb, ban, m, ols) in fits.items():
    row = {"spec": spec, "n": int(ols.nobs)}
    for lag in L3["bg_lags"]:
        lm, lmp, _, _ = acorr_breusch_godfrey(ols, nlags=lag)
        row[f"bg{lag}_lm"], row[f"bg{lag}_p"] = lm, lmp
    dw = durbin_watson(ols.resid)
    nvb = ols.nobs * ols.bse["lnV_lag1"] ** 2        # Durbin's h uses the OLS variance of b1
    h = (1 - dw / 2) * np.sqrt(ols.nobs / (1 - nvb)) if nvb < 1 else np.nan
    row.update({"dw": dw, "durbin_h": h, "durbin_h_p": 2 * norm.sf(abs(h)) if np.isfinite(h) else np.nan})
    rows.append(row)
pd.DataFrame(rows).to_csv(OUT / "layer3_residual_tests.csv", index=False)

# ------------------------------------------------------------------ break-date scan (S2, step replaces D_BAN)
d2 = est[est.year.between(*W["S2_Extended_conservative"])].copy()
rows = []
for y0 in range(L3["break_scan"][0], L3["break_scan"][1] + 1):
    d2["STEP"] = (d2.year >= y0).astype(int)
    m = fit(d2, design(d2, "D_NTB", ["STEP"]))
    rows.append({"start": y0, "coef": m.params.STEP, "hac_se": m.bse.STEP, "p": m.pvalues.STEP,
                 "r2": m.rsquared, "llf": m.llf, "n": int(m.nobs)})
pd.DataFrame(rows).to_csv(OUT / "layer3_break_scan.csv", index=False)

# ------------------------------------------------------------------ earlier steps, trend, placebos
rows = []
for y0 in L3["earlier_steps"]:
    d2["STEP"] = (d2.year >= y0).astype(int)
    m = fit(d2, design(d2, "D_NTB", ["D_BAN"], ["STEP"]))
    rows.append({"check": "S2_plus_earlier_step", "start": y0, "window": "2001-2024", "n": int(m.nobs),
                 "ban_coef": m.params.D_BAN, "ban_p": m.pvalues.D_BAN,
                 "term_coef": m.params.STEP, "term_p": m.pvalues.STEP})
d2["TREND"] = d2.year - (W["S2_Extended_conservative"][0] - 1)
m = fit(d2, design(d2, "D_NTB", ["D_BAN"], ["TREND"]))
rows.append({"check": "S2_plus_linear_trend", "start": np.nan, "window": "2001-2024", "n": int(m.nobs),
             "ban_coef": m.params.D_BAN, "ban_p": m.pvalues.D_BAN,
             "term_coef": m.params.TREND, "term_p": m.pvalues.TREND})
pw = L3["placebo_window"]
pre = est[est.year.between(*pw)].copy()
for y0 in L3["placebo_starts"]:
    pre["FAKE"] = (pre.year >= y0).astype(int)
    m = fit(pre, sm.add_constant(pre[["lnV_lag1", "FAKE", "lnER", "D_crisis"]]))
    rows.append({"check": "placebo_pre_window", "start": y0, "window": f"{pw[0]}-{pw[1]}", "n": int(m.nobs),
                 "ban_coef": np.nan, "ban_p": np.nan,
                 "term_coef": m.params.FAKE, "term_p": m.pvalues.FAKE})
pd.DataFrame(rows).to_csv(OUT / "layer3_placebo.csv", index=False)

# ------------------------------------------------------------------ percentage effects
rows = []
for spec, (d, X, ntb, ban, m, _) in fits.items():
    for v in ban:
        b, var = m.params[v], m.bse[v] ** 2
        rows.append({"spec": spec, "variable": v, "coef": b, "hac_se": m.bse[v],
                     "pct_lower": pct(b), "pct_lower_kennedy": pct(b - var / 2)})
pct_tbl = pd.DataFrame(rows)
pct_tbl.to_csv(OUT / "layer3_pct_effect.csv", index=False)

# ------------------------------------------------------------------ console summary
print(pd.read_csv(OUT / "layer3_regime_split.csv").round(3).to_string(index=False))
print()
print(pd.read_csv(OUT / "layer3_unit_roots.csv").round(3).to_string(index=False))
print()
print(pd.read_csv(OUT / "layer3_residual_tests.csv").round(3).to_string(index=False))
print()
print(pd.read_csv(OUT / "layer3_placebo.csv").round(3).to_string(index=False))
print()
print(pct_tbl.round(1).to_string(index=False))
