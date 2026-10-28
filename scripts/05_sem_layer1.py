"""
05_sem_layer1.py - Layer 1 confirmatory SEM estimation.

Builds the governorate-year indicator panel from the MAFWR production
ledger and estimates the structural model with semopy.

Specification follows SEM_SPEC_layer1.md / chapter Section 6.2, with two
data-forced deviations recorded inline:
  - Production Modernisation (PM) is dropped. Sector composition
    (artisanal/coastal/commercial) is recorded only for the unattributed
    Coastal and Commercial records in the source file (DEVIATIONS D3), so the three PM
    indicators have zero between-governorate variance and cannot be
    identified at the governorate-year unit of analysis.
  - n = 48 (6 producing governorates x 8 years), not 88. The seventh
    region label holds the unattributed Coastal and Commercial records and
    is excluded (DEVIATIONS D3).

Estimated model: PC -> ER -> SV  (three constructs, 9 indicators).

Estimator: WLSMV was specified in the analysis plan but does not apply here -- all
observed indicators are continuous. The latent form is fitted by
maximum likelihood (Wishart objective). At n=48 it is underpowered
and is reported as the planned specification, not a confirmatory
result; the composite path model in 05b_path_layer1.py is primary.
"""
import numpy as np
import pandas as pd
from semopy import Model
from common import RAW, OUT, SEED, CFG, IN

np.random.seed(SEED)

SRC = RAW / IN['layer1_xlsx']
TUNA_GENERA = tuple(CFG['layer1']['tuna_genera'])
NATIONAL = CFG['layer1']['national_label']

df = pd.read_excel(SRC, sheet_name="fisheries_production")
df = df[df["governorate_en"] != NATIONAL].copy()
df["catch_tonnes"] = df["catch_tonnes"].fillna(0.0)
df["value_omr_thousands"] = df["value_omr_thousands"].fillna(0.0)

high = df[df["id_confidence"] == "HIGH"].copy()


def hhi(shares):
    s = shares[shares > 0]
    return float((s ** 2).sum())


rows = []
for (gov, yr), g in df.groupby(["governorate_en", "year"]):
    catch = g["catch_tonnes"].sum()
    value = g["value_omr_thousands"].sum()
    if catch <= 0:
        continue
    nrows = len(g)

    gh = high[(high.governorate_en == gov) & (high.year == yr)]
    catch_high = gh["catch_tonnes"].sum()

    # ER indicators
    sci = gh["species_scientific"].fillna("")
    is_tuna = sci.str.startswith(TUNA_GENERA)
    tuna_share = gh.loc[is_tuna, "catch_tonnes"].sum() / catch if catch else 0.0
    is_pelagic = gh["species_en"].str.contains("Pelagic|Sardine|Anchovy|Mackerel|Tuna",
                                               case=False, na=False)
    pelagic_share = gh.loc[is_pelagic, "catch_tonnes"].sum() / catch if catch else 0.0
    unit_value = value / catch if catch else 0.0

    # SV indicators
    sp_catch = gh.groupby("species_en")["catch_tonnes"].sum()
    sp_shares = sp_catch / sp_catch.sum() if sp_catch.sum() > 0 else sp_catch
    species_hhi = hhi(sp_shares) if len(sp_shares) else 0.0
    top1 = float(sp_shares.max()) if len(sp_shares) else 0.0
    monthly = g.groupby("month_num")["catch_tonnes"].sum()
    seasonality_cv = float(monthly.std() / monthly.mean()) if monthly.mean() > 0 else 0.0

    rows.append(dict(
        governorate=gov, year=yr,
        catch_log=np.log(catch + 1),
        value_log=np.log(value + 1),
        record_density=np.log(nrows + 1),
        tuna_share=tuna_share,
        pelagic_share=pelagic_share,
        unit_value=unit_value,
        species_hhi=species_hhi,
        seasonality_cv=seasonality_cv,
        top1_share=top1,
    ))

panel = pd.DataFrame(rows)
print(f"Panel: n = {len(panel)} ({panel.governorate.nunique()} governorates x "
      f"{panel.year.nunique()} years)")

ind_cols = ["catch_log", "value_log", "record_density", "tuna_share",
            "pelagic_share", "unit_value", "species_hhi", "seasonality_cv",
            "top1_share"]
Z = panel[ind_cols].apply(lambda c: (c - c.mean()) / c.std(ddof=0))

desc = """
PC =~ catch_log + value_log + record_density
ER =~ tuna_share + pelagic_share + unit_value
SV =~ species_hhi + seasonality_cv + top1_share
ER ~ PC
SV ~ PC + ER
species_hhi ~~ top1_share
"""

model = Model(desc)
res = model.fit(Z, obj="MLW")  # ML (Wishart); WLSMV N/A for continuous indicators
print("\n", res)

est = model.inspect(std_est=True)
print("\n=== Parameter estimates ===")
print(est.to_string())

import semopy
stats = semopy.calc_stats(model)
print("\n=== Fit statistics ===")
print(stats.T.to_string())

panel.to_csv(OUT / "layer1_sem_panel.csv", index=False)
est.to_csv(OUT / "layer1_sem_estimates.csv", index=False)
stats.T.to_csv(OUT / "layer1_sem_fit.csv")
