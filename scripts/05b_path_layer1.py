"""
05b_path_layer1.py - Layer 1 composite-indicator path analysis.

Primary estimable specification. Each construct is a standardised
composite (z-score mean of its indicators). Structural paths estimated
by OLS with governorate-clustered SEs (Cameron & Miller, 2015).

n = 48 (6 producing governorates x 8 years). PM dropped: sector
composition is national-only in the source file.

The full latent SEM (SEM_SPEC_layer1.md) is the target specified in the analysis plan;
it is underpowered at n=48 (~2 obs/parameter) and reported as such.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from common import OUT, SEED, CFG

np.random.seed(SEED)
BOOT_REPS = int(CFG['layer1']['bootstrap_reps'])
panel = pd.read_csv(OUT / "layer1_sem_panel.csv")

def z(c):
    return (c - c.mean()) / c.std(ddof=0)

# Composites (standardised mean of standardised indicators)
panel["PC"] = z(pd.concat([z(panel.catch_log), z(panel.value_log),
                           z(panel.record_density)], axis=1).mean(axis=1))
panel["ER"] = z(pd.concat([z(panel.tuna_share), z(panel.pelagic_share),
                           z(panel.unit_value)], axis=1).mean(axis=1))
panel["SV"] = z(pd.concat([z(panel.species_hhi), z(panel.seasonality_cv),
                           z(panel.top1_share)], axis=1).mean(axis=1))

print(f"n = {len(panel)}, governorates = {panel.governorate.nunique()}")

# Composite reliability (Cronbach alpha) per construct
def alpha(cols):
    X = panel[cols].apply(z); k = len(cols)
    return k/(k-1)*(1 - X.var(ddof=1).sum()/X.sum(axis=1).var(ddof=1))
print("Cronbach alpha  PC:", round(alpha(['catch_log','value_log','record_density']),3),
      " ER:", round(alpha(['tuna_share','pelagic_share','unit_value']),3),
      " SV:", round(alpha(['species_hhi','seasonality_cv','top1_share']),3))
pd.DataFrame({"construct": ["PC", "ER", "SV"],
              "cronbach_alpha": [alpha(['catch_log','value_log','record_density']),
                                 alpha(['tuna_share','pelagic_share','unit_value']),
                                 alpha(['species_hhi','seasonality_cv','top1_share'])]}
             ).to_csv(OUT / "layer1_alpha.csv", index=False)

cl = {"groups": panel["governorate"]}
m1 = smf.ols("ER ~ PC", panel).fit(cov_type="cluster", cov_kwds=cl)
m2 = smf.ols("SV ~ PC + ER", panel).fit(cov_type="cluster", cov_kwds=cl)

print("\n=== ER ~ PC ===")
print(m1.summary2().tables[1].round(4).to_string())
print(f"R2 = {m1.rsquared:.3f}")
print("\n=== SV ~ PC + ER ===")
print(m2.summary2().tables[1].round(4).to_string())
print(f"R2 = {m2.rsquared:.3f}")

# Indirect effect PC -> ER -> SV, bootstrap CI (cluster bootstrap, 5000)
def coef(d):
    a = smf.ols("ER ~ PC", d).fit().params["PC"]
    b = smf.ols("SV ~ PC + ER", d).fit().params["ER"]
    return a*b
direct = coef(panel)
govs = panel.governorate.unique()
boot = []
rng = np.random.default_rng(SEED)
for _ in range(BOOT_REPS):
    samp = rng.choice(govs, size=len(govs), replace=True)
    d = pd.concat([panel[panel.governorate==g] for g in samp], ignore_index=True)
    try: boot.append(coef(d))
    except Exception: pass
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"\nIndirect PC->ER->SV = {direct:.3f}  95% CI [{lo:.3f}, {hi:.3f}]  (cluster bootstrap, {len(boot)} reps)")

pd.DataFrame({
    "path": ["ER~PC","SV~PC","SV~ER","indirect PC->ER->SV"],
    "coef": [m1.params["PC"], m2.params["PC"], m2.params["ER"], direct],
    "se":   [m1.bse["PC"], m2.bse["PC"], m2.bse["ER"], np.nan],
    "p":    [m1.pvalues["PC"], m2.pvalues["PC"], m2.pvalues["ER"], np.nan],
    "ci_lo":[np.nan,np.nan,np.nan,lo], "ci_hi":[np.nan,np.nan,np.nan,hi],
}).to_csv(OUT / "layer1_path_results.csv", index=False)
