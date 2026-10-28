"""
01_descriptive_layer1.py

Generates the six Layer 1 descriptive indicators specified in the
framework (2a__LayoutOutline) using the fisheries_production sheet
of Oman_Layer1_Clean_EN_v2.xlsx.

Indicators:
    A. Annual production dynamics       — total catch & value by year
    B. Governorate HHI                  — Herfindahl-Hirschman on catch_tonnes
    C. Sector composition               — Artisanal / Coastal / Commercial share
    D. Production volatility            — annual catch CV (3-year rolling)
    E. Species concentration (HIGH)     — HHI restricted to id_confidence=HIGH
    F. Supply stability                 — monthly catch CV within year

Outputs:
    layer1_indicators.xlsx (six sheets)
    layer1_indicators_long.csv (tidy)
"""
import pandas as pd
import numpy as np
from common import RAW, OUT, CFG, IN

src = RAW / IN['layer1_xlsx']
fp = pd.read_excel(src, sheet_name='fisheries_production')

# Normalise
fp['catch_tonnes'] = pd.to_numeric(fp['catch_tonnes'], errors='coerce').fillna(0)
fp['value_omr_thousands'] = pd.to_numeric(fp['value_omr_thousands'],
                                          errors='coerce').fillna(0)


def hhi(shares):
    s = np.asarray(shares, dtype=float)
    s = s[s > 0]
    if s.sum() == 0:
        return np.nan
    p = s / s.sum()
    return float((p ** 2).sum())


# A. Annual production dynamics
A = (fp.groupby('year')
        .agg(catch_tonnes=('catch_tonnes', 'sum'),
             value_omr_thousands=('value_omr_thousands', 'sum'))
        .reset_index())
A['catch_growth_pct'] = A['catch_tonnes'].pct_change() * 100
A['value_growth_pct'] = A['value_omr_thousands'].pct_change() * 100

# B. Governorate HHI
gov = (fp.groupby(['year', 'governorate_en'])['catch_tonnes']
         .sum().reset_index())
B = (gov.groupby('year')['catch_tonnes']
        .apply(hhi).reset_index(name='gov_hhi'))
B['gov_effective_n'] = 1.0 / B['gov_hhi']

# C. Sector composition (Artisanal / Coastal / Commercial)
sec = (fp.groupby(['year', 'sector_en'])['catch_tonnes']
         .sum().reset_index())
C = sec.pivot(index='year', columns='sector_en',
              values='catch_tonnes').fillna(0)
C_share = C.div(C.sum(axis=1), axis=0).reset_index()
C_share = C_share.rename(columns={k: f'{k.lower()}_share' for k in C.columns})

# D. Production volatility — 3-year rolling CV of annual catch
D = A[['year', 'catch_tonnes']].copy()
D['catch_3yr_mean'] = D['catch_tonnes'].rolling(3).mean()
D['catch_3yr_std']  = D['catch_tonnes'].rolling(3).std()
D['catch_3yr_cv']   = D['catch_3yr_std'] / D['catch_3yr_mean']

# E. Species concentration — HIGH-confidence subset
hi = fp[fp['id_confidence'] == 'HIGH'].copy()
spp = (hi.groupby(['year', 'species_en'])['catch_tonnes']
         .sum().reset_index())
E = (spp.groupby('year')['catch_tonnes']
        .apply(hhi).reset_index(name='species_hhi_high'))
E['species_effective_n'] = 1.0 / E['species_hhi_high']
high_share = (fp.groupby(['year', 'id_confidence'])['catch_tonnes']
                .sum().reset_index()
                .pivot(index='year', columns='id_confidence',
                       values='catch_tonnes').fillna(0))
high_share['high_coverage_share'] = (
    high_share.get('HIGH', 0) /
    high_share.sum(axis=1))
E = E.merge(high_share[['high_coverage_share']].reset_index(),
            on='year')

# F. Supply stability — within-year monthly CV of total catch
mon = (fp.groupby(['year', 'month_num'])['catch_tonnes']
         .sum().reset_index())
F = (mon.groupby('year')['catch_tonnes']
        .agg(['mean', 'std']).reset_index()
        .rename(columns={'mean': 'monthly_catch_mean',
                         'std':  'monthly_catch_std'}))
F['monthly_catch_cv'] = F['monthly_catch_std'] / F['monthly_catch_mean']

# Persist
with pd.ExcelWriter(OUT / 'layer1_indicators.xlsx', engine='openpyxl') as w:
    A.to_excel(w, sheet_name='A_production_dynamics', index=False)
    B.to_excel(w, sheet_name='B_governorate_hhi',     index=False)
    C_share.to_excel(w, sheet_name='C_sector_composition', index=False)
    D.to_excel(w, sheet_name='D_volatility_3yr',      index=False)
    E.to_excel(w, sheet_name='E_species_hhi_high',    index=False)
    F.to_excel(w, sheet_name='F_supply_stability',    index=False)

# Tidy long-form
long = []
for ind, df in [('A_production_dynamics', A),
                ('B_governorate_hhi', B),
                ('C_sector_composition', C_share),
                ('D_volatility_3yr', D),
                ('E_species_hhi_high', E),
                ('F_supply_stability', F)]:
    m = df.melt(id_vars='year', var_name='metric', value_name='value')
    m.insert(0, 'indicator', ind)
    long.append(m)
pd.concat(long).to_csv(OUT / 'layer1_indicators_long.csv', index=False)

# Sensitivity (not used in the chapter): governorate HHI with and without the unattributed
# Coastal + Commercial bucket. The chapter's Indicator B includes it (7 units).
nat = CFG['layer1']['national_label']
g6 = gov[gov['governorate_en'] != nat]
S = pd.DataFrame({
    'gov_hhi_incl_unattributed': gov.groupby('year')['catch_tonnes'].apply(hhi),
    'gov_hhi_six_governorates': g6.groupby('year')['catch_tonnes'].apply(hhi),
}).reset_index()
S['effective_n_incl_unattributed'] = 1 / S['gov_hhi_incl_unattributed']
S['effective_n_six_governorates'] = 1 / S['gov_hhi_six_governorates']
S['unattributed_share_of_catch'] = (gov[gov['governorate_en'] == nat].set_index('year')['catch_tonnes']
                                    / gov.groupby('year')['catch_tonnes'].sum()).values
S.to_csv(OUT / 'layer1_gov_hhi_sensitivity.csv', index=False)

print('Indicator A: annual production dynamics')
print(A.round(2).to_string(index=False))
print('\nIndicator B: governorate HHI')
print(B.round(4).to_string(index=False))
print('\nIndicator C: sector composition (shares)')
print(C_share.round(3).to_string(index=False))
print('\nIndicator D: 3-yr rolling production volatility')
print(D.round(3).to_string(index=False))
print('\nIndicator E: species HHI (HIGH-confidence subset)')
print(E.round(4).to_string(index=False))
print('\nIndicator F: monthly supply stability (within-year CV)')
print(F.round(3).to_string(index=False))

# G. Species shares of HIGH-confidence catch, by year (lets 07 verify the chapter's
#    sardine share without the raw workbook)
_hi = fp[fp['id_confidence'] == 'HIGH'].groupby(['year', 'species_en'])['catch_tonnes'].sum().reset_index()
_hi['share_of_high_confidence_catch'] = _hi['catch_tonnes'] / _hi.groupby('year')['catch_tonnes'].transform('sum')
_hi.to_csv(OUT / 'layer1_species_share_high.csv', index=False)
