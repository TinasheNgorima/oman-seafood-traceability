"""
07_verify_chapter_claims.py - compares every number reported in the chapter with the pipeline outputs.

Each row of outputs/claims_report.csv is one reported figure:
    id, section, statement, chapter_value, pipeline_value, tolerance, expected, result

expected = "match"      -> the chapter figure must agree with the pipeline within the tolerance.
expected = "discrepancy"-> reserved for a documented difference (none at present).
Exit status is non-zero if any row does not behave as expected.
"""
import sys
import numpy as np
import pandas as pd
from common import RAW, OUT, IN

rows = []


def claim(cid, section, text, chapter, pipeline, tol, expected="match", note=""):
    diff = abs(float(chapter) - float(pipeline))
    agrees = diff <= tol + 1e-12
    ok = agrees if expected == "match" else (not agrees)
    result = ("OK" if expected == "match" else "DOCUMENTED DISCREPANCY") if ok else \
             ("FAIL: differs" if expected == "match" else "FAIL: discrepancy no longer present")
    rows.append(dict(id=cid, section=section, statement=text, chapter_value=chapter,
                     pipeline_value=round(float(pipeline), 6), tolerance=tol,
                     expected=expected, result=result, note=note))


# ---------------------------------------------------------------- Layer 3 (Table 3, Section 7.3)
res = pd.read_csv(OUT / "bose_replication_results.csv")
SPEC = {"S1": "S1_Bose_window_2001_2013", "S2": "S2_Extended_conservative", "S3": "S3_Extended_maximalist"}
T3 = {  # variable: (S1, S2, S3) coef, se
    "const":    ((7.795, 2.832), (8.383, 2.057), (7.968, 2.077)),
    "lnV_lag1": ((0.516, 0.151), (0.438, 0.121), (0.454, 0.120)),
    "D_BAN":    ((-0.698, 0.209), (-0.580, 0.157), (-0.579, 0.161)),
    "D_NTB":    ((-0.023, 0.043), (0.005, 0.092), (0.074, 0.156)),
    "lnER":     ((0.587, 0.399), (1.473, 0.722), (1.628, 0.629)),
    "D_crisis": ((-0.460, 0.120), (-0.364, 0.115), (-0.337, 0.111)),
}
for var, vals in T3.items():
    for (sk, sname), (c, se) in zip(SPEC.items(), vals):
        r = res[(res.spec == sname) & (res.variable == var)].iloc[0]
        claim(f"T3.{sk}.{var}.coef", "7.3 Table 3", f"{sk} {var} coefficient", c, r.coef, 0.0005)
        claim(f"T3.{sk}.{var}.se", "7.3 Table 3", f"{sk} {var} HAC SE", se, r.hac_se, 0.0005)
for sk, n, r2 in [("S1", 13, 0.937), ("S2", 24, 0.712), ("S3", 24, 0.715)]:
    sname = SPEC[sk]
    claim(f"T3.{sk}.n", "7.3 Table 3", f"{sk} n", n, res[(res.spec == sname) & (res.variable == "__N__")].coef.iloc[0], 0)
    claim(f"T3.{sk}.R2", "7.3 Table 3", f"{sk} R-squared", r2, res[(res.spec == sname) & (res.variable == "__R2__")].coef.iloc[0], 0.0005)
P = lambda sk, v: res[(res.spec == SPEC[sk]) & (res.variable == v)].p.iloc[0]
for sk, v, pv in [("S2", "lnER", .041), ("S3", "lnER", .010)]:
    claim(f"T3.{sk}.{v}.p", "7.3", f"{sk} {v} p-value", pv, P(sk, v), 0.0005)
claim("T3.BAN.p<.01", "Abstract/7.3", "max p of D_BAN across specs below .01", 1, float(max(P(k, "D_BAN") for k in SPEC) < 0.01), 0)
claim("T3.crisis.p<.01", "7.3", "max p of D_crisis across specs below .01", 1, float(max(P(k, "D_crisis") for k in SPEC) < 0.01), 0)
bans = [1 - np.exp(res[(res.spec == SPEC[k]) & (res.variable == "D_BAN")].coef.iloc[0]) for k in SPEC]
claim("Abs.ban_pct_min", "Abstract/7.3", "smallest proportional reduction (%)", 44, 100 * min(bans), 0.5)
claim("Abs.ban_pct_max", "Abstract/7.3", "largest proportional reduction (%)", 50, 100 * max(bans), 0.5)

# ---------------------------------------------------------------- Layer 3 robustness (03b; Table 3 S4, Sections 6.4, 7.3, 8.1, 10)
rs = pd.read_csv(OUT / "layer3_regime_split.csv")
S4 = {"S4": "S4_Regime_split_conservative", "S4max": "S4_Regime_split_maximalist"}
R = lambda sk, v, col="coef": rs[(rs.spec == S4[sk]) & (rs.variable == v)][col].iloc[0]
T3S4 = {"const": (8.894, 1.964), "lnV_lag1": (0.411, 0.117), "D_BAN_A": (-0.636, 0.147),
        "D_BAN_B": (-0.554, 0.200), "D_NTB": (0.017, 0.093), "lnER": (1.396, 0.684), "D_crisis": (-0.386, 0.104)}
for v, (c, se) in T3S4.items():
    claim(f"T3.S4.{v}.coef", "7.3 Table 3", f"S4 {v} coefficient", c, R("S4", v), 0.0005)
    claim(f"T3.S4.{v}.se", "7.3 Table 3", f"S4 {v} HAC SE", se, R("S4", v, "hac_se"), 0.0005)
claim("T3.S4.n", "7.3 Table 3", "S4 n", 24, R("S4", "__N__"), 0)
claim("T3.S4.R2", "7.3 Table 3", "S4 R-squared", 0.714, R("S4", "__R2__"), 0.0005)
claim("T3.S4.lnER.sig", "7.3 Table 3", "S4 ln ER significant at 5% (**), not at 1%", 1,
      float(0.01 <= R("S4", "lnER", "p") < 0.05), 0)
claim("7.3.S4.A.p<.001", "7.3", "S4 D_BAN 2011-2018 p < .001", 1, float(R("S4", "D_BAN_A", "p") < 0.001), 0)
claim("7.3.S4.B.p", "7.3", "S4 D_BAN 2019-2024 p", .005, R("S4", "D_BAN_B", "p"), 0.0005)
claim("T3.note.wald", "7.3/Table 3 note", "Wald test D_BAN 2011-2018 = 2019-2024, conservative, p", .70, R("S4", "__WALD_A_EQ_B__", "p"), 0.005)
claim("7.3.wald.max", "7.3", "Wald test, maximalist S4, p", .31, R("S4max", "__WALD_A_EQ_B__", "p"), 0.005)
claim("Abs.regimes.p<.01", "Abstract/1/11", "both regime dummies p < .01 in both S4 versions", 1,
      float(max(R(k, v, "p") for k in S4 for v in ("D_BAN_A", "D_BAN_B")) < 0.01), 0)
allp = lambda v4, v: [P(k, v) for k in SPEC] + [R("S4", v4, "p")]
claim("7.3.AR1.min", "7.3", "smallest ln V(t-1) coefficient, S1-S4", 0.411,
      min([res[(res.spec == SPEC[k]) & (res.variable == "lnV_lag1")].coef.iloc[0] for k in SPEC] + [R("S4", "lnV_lag1")]), 0.0005)
claim("7.3.AR1.max", "7.3", "largest ln V(t-1) coefficient, S1-S4", 0.516,
      max([res[(res.spec == SPEC[k]) & (res.variable == "lnV_lag1")].coef.iloc[0] for k in SPEC] + [R("S4", "lnV_lag1")]), 0.0005)
claim("T3.AR1.p<.001", "7.3", "max p of ln V(t-1) across S1-S4 below .001", 1, float(max(allp("lnV_lag1", "lnV_lag1")) < 0.001), 0)
claim("7.3.NTB.p>=.58", "7.3", "D_NTB p at least .58 in every specification, S1-S4", 1,
      float(round(min(allp("D_NTB", "D_NTB")), 2) >= 0.58), 0, note="Rounded to two decimals. S1 p = .584.")
crisis = [res[(res.spec == SPEC[k]) & (res.variable == "D_crisis")].coef.iloc[0] for k in SPEC] + [R("S4", "D_crisis")]
claim("7.3.crisis.range", "7.3", "D_crisis within -0.337 to -0.460, S1-S4", 1,
      float(-0.4605 <= min(crisis) and max(crisis) <= -0.3365), 0)
ban3 = [res[(res.spec == SPEC[k]) & (res.variable == "D_BAN")].coef.iloc[0] for k in SPEC]
claim("1.ban.min", "1 contributions", "D_BAN beta, smallest magnitude", -0.579, max(ban3), 0.0005)
claim("1.ban.max", "1 contributions", "D_BAN beta, largest magnitude", -0.698, min(ban3), 0.0005)

ur = pd.read_csv(OUT / "layer3_unit_roots.csv")
U = lambda s, t, f, r: ur[(ur.series == s) & (ur.test == t) & (ur.form == f) & (ur.regression == r)].iloc[0]
claim("7.3.adf.lnV", "7.3", "ADF p, ln V level, constant", .23, U("lnV", "ADF", "level", "c").p, 0.005)
claim("7.3.adf.lnER", "7.3", "ADF p, ln ER level, constant", .27, U("lnER", "ADF", "level", "c").p, 0.005)
claim("7.3.kpss>=.10", "7.3", "KPSS p at least .10, both series, constant", 1,
      float(min(U("lnV", "KPSS", "level", "c").p, U("lnER", "KPSS", "level", "c").p) >= 0.10), 0,
      note="statsmodels truncates KPSS p at .10.")
claim("7.3.ur.n", "7.3/10", "unit-root sample size", 25, U("lnV", "ADF", "level", "c").n, 0)

rt = pd.read_csv(OUT / "layer3_residual_tests.csv").set_index("spec")
ALL = {**SPEC, "S4": S4["S4"]}
for sk, bg, h, hp in [("S1", .106, -2.80, .005), ("S2", .586, 0.85, .40), ("S3", .580, 0.90, .37), ("S4", .547, 2.12, .034)]:
    claim(f"T3.{sk}.bg1.p", "7.3 Table 3", f"{sk} Breusch-Godfrey(1) p", bg, rt.loc[ALL[sk], "bg1_p"], 0.0005)
    claim(f"T3.{sk}.durbin_h", "7.3 Table 3", f"{sk} Durbin's h", h, rt.loc[ALL[sk], "durbin_h"], 0.005)
    claim(f"T3.{sk}.durbin_h.p", "7.3 Table 3", f"{sk} Durbin's h p", hp, rt.loc[ALL[sk], "durbin_h_p"], 0.0005 if hp < .1 else 0.005)

bs = pd.read_csv(OUT / "layer3_break_scan.csv").set_index("start")
claim("7.3.scan.r2.2011", "7.3", "step-dummy R-squared, start 2011", .712, bs.loc[2011, "r2"], 0.0005)
claim("7.3.scan.r2.2012", "7.3", "step-dummy R-squared, start 2012", .713, bs.loc[2012, "r2"], 0.0005)
claim("7.3.scan.peak", "7.3", "no start year in the scan fits better than 2012", 2012, bs.r2.idxmax(), 0,
      note="2009 fits identically to 2011 because D_crisis covers 2009-2010.")
pl = pd.read_csv(OUT / "layer3_placebo.csv")
ctl = pl[pl.check != "placebo_pre_window"]
claim("7.3.ctl.ban.min", "7.3", "D_BAN with earlier step or trend, smallest magnitude", -0.618, ctl.ban_coef.max(), 0.0005)
claim("7.3.ctl.ban.max", "7.3", "D_BAN with earlier step or trend, largest magnitude", -1.104, ctl.ban_coef.min(), 0.0005)
claim("7.3.ctl.p<=.002", "7.3", "D_BAN p at most .002 (three decimals) with earlier step or trend", 1,
      float(round(ctl.ban_p.max(), 3) <= 0.002), 0, note="Largest p = .0024 (step from 2007).")
plc = pl[pl.check == "placebo_pre_window"].set_index("start")
claim("7.3.placebo.neg", "7.3/8.1/10", "placebo steps from 2006 and 2007 negative and p < .01", 1,
      float((plc.loc[[2006, 2007], "term_coef"] < 0).all() and (plc.loc[[2006, 2007], "term_p"] < 0.01).all()), 0)
claim("7.3.placebo.n", "7.3", "placebo window observations", 10, plc.n.iloc[0], 0)
pe = pd.read_csv(OUT / "layer3_pct_effect.csv")
claim("7.3.pct.formula", "7.3", "verifier and 03b percentage effects agree (S1-S3 range 44-50%)", 1,
      float(abs(pe[pe.variable == "D_BAN"].pct_lower.min() - 100 * min(bans)) < 1e-9), 0)

panel = pd.read_csv(OUT / "bose_replication_panel.csv")
claim("6.4.D_BAN.years", "6.4", "D_BAN = 1 in 2011-2024 (14 years)", 14, panel.D_BAN.sum(), 0)
claim("6.4.D_NTB.years", "6.4", "D_NTB = 1 in 8 Bose-observed years", 8, panel.D_NTB.sum(), 0,
      note="Chapter text says 'RASFF-notified years (2004-2013)'. Only 8 of those 10 years are coded 1 (2007 and 2009 are 0).")

# ---------------------------------------------------------------- Layer 2 (Table 2, Section 7.2)
cen = pd.read_csv(OUT / "layer2_centrality.csv").set_index("node")
T2 = {"Exporter": (52, 25, .429, .497, .182), "EU_Buyer": (25, 19, .405, .245, .173),
      "EU_CA": (19, 19, .381, .133, .166), "MAFWR": (34, 43, .405, .459, .160),
      "RASFF": (19, 19, .357, .184, .160), "Processor": (48, 25, .167, .475, .091),
      "FQCC": (23, 25, .000, .331, .049), "EU_FVO": (0, 45, .000, .310, .019)}
for node, (di, do, b, e, pr) in T2.items():
    for col, v, tol in [("degree_in_w", di, 0), ("degree_out_w", do, 0), ("betweenness", b, .0005),
                        ("eigenvector", e, .0005), ("pagerank", pr, .0005)]:
        claim(f"T2.{node}.{col}", "7.2 Table 2", f"{node} {col}", v, cen.loc[node, col], tol)
edges = pd.read_csv(OUT / "layer2_edges.csv")
claim("6.3.nodes", "6.3", "number of nodes", 8, len(cen), 0)
claim("6.3.edges", "6.3", "number of directed edges", 13, len(edges), 0)
w = edges.groupby("edge_type").weight.max()
claim("6.3.w.mds", "6.3", "ministerial decisions", 8, w["regulatory_authority"], 0)
claim("6.3.w.qc", "6.3", "peak QC-certified establishments", 25, w["certification"], 0)
claim("6.3.w.rasff", "6.3", "RASFF cases", 19, w["notification"], 0)
claim("6.3.w.fvo", "6.3", "FVO deficiency findings", 15, w["audit"], 0)
claim("6.3.w.ban", "6.3", "ban decision rows", 19, w["export_ban"], 0)
claim("7.2.rank.eig", "7.2/8.3", "Processor eigenvector rank (second)", 2, int((cen.eigenvector > cen.loc["Processor", "eigenvector"]).sum() + 1), 0)
claim("5.5.edge_types", "5.5", "six edge types, none platform-mediated", 6, edges.edge_type.nunique(), 0)

# ---------------------------------------------------------------- Layer 2 sensitivity (04b; Sections 6.3, 7.2, 8.3, Table 4)
rw = pd.read_csv(OUT / "layer2_reweight_summary.csv").set_index("node")
claim("6.3.draws", "6.3", "reweighting draws", 10000, rw.draws.iloc[0], 0)
claim("6.3.range.lo", "6.3", "reweighting multiplier, lower bound", 0.5, rw.range_low.iloc[0], 0)
claim("6.3.range.hi", "6.3", "reweighting multiplier, upper bound", 1.5, rw.range_high.iloc[0], 0)
for node, pct in [("Exporter", 47), ("Processor", 33), ("MAFWR", 19)]:
    claim(f"7.2.first.{node}", "7.2", f"{node} ranks first on eigenvector (% of draws)", pct, 100 * rw.loc[node, "share_eig_first"], 0.5)
claim("7.2.top3>=89", "7.2", "Exporter, Processor and MAFWR each in the eigenvector top three in at least 89% of draws", 1,
      float(round(100 * rw.loc[["Exporter", "Processor", "MAFWR"], "share_eig_top3"].min()) >= 89), 0)
claim("8.3.proc.top3", "8.3/Table 4", "Processor in eigenvector top three (% of draws)", 95, 100 * rw.loc["Processor", "share_eig_top3"], 0.5)
claim("7.2.exp.prk.all", "7.2", "Exporter highest PageRank in every draw (%)", 100, 100 * rw.loc["Exporter", "share_pagerank_first"], 0)
lo = pd.read_csv(OUT / "layer2_leave_one_out.csv")
claim("7.2.loo.n", "7.2", "single-edge removals", 13, len(lo), 0)
claim("7.2.loo.btw.lost", "7.2", "removals in which Exporter loses highest betweenness", 6, int((~lo.exporter_betweenness_first).sum()), 0)
claim("7.2.loo.mafwr", "7.2", "removals in which MAFWR keeps highest domestic betweenness", 12, int(lo.mafwr_domestic_betweenness_first.sum()), 0)
ed = pd.read_csv(OUT / "layer2_eig_vs_degree.csv").set_index("node")
claim("8.3.proc.resid", "8.3", "Processor eigenvector minus value predicted by weighted degree", 0.011, ed.loc["Processor", "eig_minus_predicted"], 0.0005)

# ---------------------------------------------------------------- Layer 1 (Section 7.1)
ind = pd.read_csv(OUT / "layer1_indicators_long.csv")
g = lambda i, m, y=None: (ind[(ind.indicator == i) & (ind.metric == m)].set_index("year").value if y is None
                          else ind[(ind.indicator == i) & (ind.metric == m) & (ind.year == y)].value.iloc[0])
catch = g("A_production_dynamics", "catch_tonnes"); val = g("A_production_dynamics", "value_omr_thousands")
claim("7.1.catch17", "7.1", "catch 2017 (kt)", 347.5, catch[2017] / 1e3, .05)
claim("7.1.catch24", "7.1", "catch 2024 (kt)", 794.0, catch[2024] / 1e3, .05)
claim("7.1.growth", "7.1", "catch growth 2017-2024 (%)", 128.5, 100 * (catch[2024] / catch[2017] - 1), .05)
claim("7.1.peak", "7.1", "peak catch (kt)", 920.4, catch.max() / 1e3, .05)
claim("7.1.peakyear", "7.1", "peak year", 2021, catch.idxmax(), 0)
claim("7.1.value17", "7.1", "value 2017 (OMR million)", 225.9, val[2017] / 1e3, .05)
claim("7.1.value24", "7.1", "value 2024 (OMR million)", 518.2, val[2024] / 1e3, .05)
claim("7.1.uv17", "7.1", "unit value 2017 (OMR/kg)", 0.650, val[2017] / catch[2017], .0005)
claim("7.1.uv24", "7.1", "unit value 2024 (OMR/kg)", 0.653, val[2024] / catch[2024], .0005)
sec = lambda m, y: 100 * g("C_sector_composition", m, y)
claim("7.1.art17", "7.1", "artisanal share 2017 (%)", 99.0, sec("artisanal_share", 2017), .05)
claim("7.1.art24", "7.1", "artisanal share 2024 (%)", 90.3, sec("artisanal_share", 2024), .05)
claim("7.1.com17", "7.1", "commercial share 2017 (%)", 0.1, sec("commercial_share", 2017), .05)
claim("7.1.com24", "7.1", "commercial share 2024 (%)", 8.6, sec("commercial_share", 2024), .05)
cs = 100 * g("C_sector_composition", "coastal_share")
claim("7.1.coast.min", "7.1", "coastal share minimum (%)", 0.5, cs.min(), .1)
claim("7.1.coast.max", "7.1", "coastal share maximum (%)", 1.0, cs.max(), .1)
hh = g("B_governorate_hhi", "gov_hhi"); en = g("B_governorate_hhi", "gov_effective_n")
claim("7.1.hhi.min", "7.1", "governorate HHI minimum (six governorates plus unattributed Coastal+Commercial records)", 0.20, hh.min(), .005,
      note="Seven units. See DEVIATIONS D3.")
claim("7.1.hhi.max", "7.1", "governorate HHI maximum", 0.27, hh.max(), .005)
claim("7.1.effn.min", "7.1", "effective N, lower end (rounded)", 4, round(en.min()), 0)
claim("7.1.effn.max", "7.1", "effective N, upper end (rounded)", 5, round(en.max()), 0)
sh = g("E_species_hhi_high", "species_hhi_high")
claim("7.1.shhi20", "7.1", "species HHI 2020", 0.40, sh[2020], .005)
claim("7.1.shhi24", "7.1", "species HHI 2024", 0.21, sh[2024], .005)
cov = 100 * g("E_species_hhi_high", "high_coverage_share")
claim("7.1.cov.min", "7.1", "HIGH-confidence coverage minimum (%)", 77, cov.min(), .5)
claim("7.1.cov.max", "7.1", "HIGH-confidence coverage maximum (%)", 85, cov.max(), .5)
ss = pd.read_csv(OUT / "layer1_species_share_high.csv")
top20 = 100 * ss[ss.year == 2020].share_of_high_confidence_catch.max()
claim("7.1.sardine", "7.1/8.4", "Indian Oil Sardine share of HIGH-confidence catch, 2020 (%)", 62, top20, .5)
cv = g("D_volatility_3yr", "catch_3yr_cv")
claim("7.1.cv19", "7.1", "3-year rolling CV 2019", 0.26, cv[2019], .005)
claim("7.1.cv24", "7.1", "3-year rolling CV 2024", 0.03, cv[2024], .005)
mcv = g("F_supply_stability", "monthly_catch_cv")
claim("7.1.mcv.min", "7.1", "monthly CV minimum", 0.33, mcv.min(), .005)
claim("7.1.mcv.max", "7.1", "monthly CV maximum", 0.44, mcv.max(), .005)

# ---------------------------------------------------------------- Layer 1 pathway (Section 7.1, 6.2)
pr = pd.read_csv(OUT / "layer1_path_results.csv").set_index("path")
al = pd.read_csv(OUT / "layer1_alpha.csv").set_index("construct").cronbach_alpha
fit = pd.read_csv(OUT / "layer1_sem_fit.csv", index_col=0).Value
sp = pd.read_csv(OUT / "layer1_sem_panel.csv")
claim("6.2.n", "6.2", "governorate-year cells", 48, len(sp), 0)
claim("6.2.govs", "6.2", "governorates", 6, sp.governorate.nunique(), 0)
claim("7.1.alpha.PC", "7.1", "Cronbach alpha PC", 0.68, al["PC"], .005)
claim("7.1.alpha.SV", "7.1", "Cronbach alpha SV", 0.90, al["SV"], .005)
claim("7.1.alpha.ER<0", "7.1", "Cronbach alpha ER below zero", 1, float(al["ER"] < 0), 0)
claim("7.1.ER~PC", "7.1", "ER ~ PC beta", -0.04, pr.loc["ER~PC", "coef"], .005)
claim("7.1.ER~PC.p", "7.1", "ER ~ PC p", 0.91, pr.loc["ER~PC", "p"], .005)
claim("7.1.SV~ER", "7.1", "SV ~ ER beta", -0.64, pr.loc["SV~ER", "coef"], .005)
claim("7.1.SV~PC", "7.1", "SV ~ PC beta", 0.41, pr.loc["SV~PC", "coef"], .005)
claim("7.1.SV.p<.01", "7.1", "both SV paths p < .01", 1, float(max(pr.loc["SV~ER", "p"], pr.loc["SV~PC", "p"]) < 0.01), 0)
ind_row = pr.loc["indirect PC->ER->SV"]
claim("7.1.indirect", "7.1", "indirect effect", 0.02, ind_row.coef, .005)
claim("7.1.ci.lo", "7.1", "bootstrap CI lower", -0.32, ind_row.ci_lo, .005)
claim("7.1.ci.hi", "7.1", "bootstrap CI upper", 0.47, ind_row.ci_hi, .005)
claim("7.1.CFI", "7.1", "latent model CFI", 0.65, fit["CFI"], .005)
claim("7.1.RMSEA", "7.1", "latent model RMSEA", 0.48, fit["RMSEA"], .005)

rep = pd.DataFrame(rows)
rep.to_csv(OUT / "claims_report.csv", index=False)
bad = rep[rep.result.str.startswith("FAIL")]
print(f"{len(rep)} chapter figures checked | {(rep.result == 'OK').sum()} match | "
      f"{(rep.result == 'DOCUMENTED DISCREPANCY').sum()} documented discrepancies | {len(bad)} unexpected")
if len(bad):
    print(bad[["id", "statement", "chapter_value", "pipeline_value", "result"]].to_string(index=False))
    sys.exit(1)
