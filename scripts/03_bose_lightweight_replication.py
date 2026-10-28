"""
03_bose_lightweight_replication.py

Lightweight aggregate replication of the Bose-style OLS specification on the
extended Oman -> EU-27 fish export panel (n = 25, 2000-2024).

Baseline specification:
    ln V_t = b0 + b1 ln V_{t-1} + b2 D_BAN_t + b3 D_NTB_t + b4 ln ER_t + b5 D_crisis_t + e_t

We estimate three specifications:
    (S1) Bose-window subset 2000-2013, Bose-observed D_NTB and D_BAN.
    (S2) Extended window 2000-2024, Bose-observed D_NTB (post-2013 = 0).
    (S3) Extended window 2000-2024, maximalist D_NTB.

All standard errors are Newey-West HAC with bandwidth = 2.

Outputs:
    - bose_replication_results.csv  (long-format coefficient table)
    - bose_replication_summary.txt  (human-readable summaries)
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from common import OUT, CFG

panel = pd.read_csv(OUT / 'bose_replication_panel.csv').dropna(subset=['lnV_lag1'])

def fit(df, ntb_col='D_NTB', label=''):
    X = df[['lnV_lag1', 'D_BAN', ntb_col, 'lnER', 'D_crisis']].rename(
        columns={ntb_col: 'D_NTB'})
    X = sm.add_constant(X)
    y = df['lnV']
    m = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': CFG['layer3']['hac_maxlags']})
    return label, m

results = []
W = CFG['layer3']['windows']
results.append(fit(panel[panel.year.between(*W['S1_Bose_window_2001_2013'])], 'D_NTB', 'S1_Bose_window_2001_2013'))
results.append(fit(panel[panel.year.between(*W['S2_Extended_conservative'])], 'D_NTB', 'S2_Extended_conservative'))
results.append(fit(panel[panel.year.between(*W['S3_Extended_maximalist'])], 'D_NTB_max', 'S3_Extended_maximalist'))

# Long-format coefficient table
rows = []
for label, m in results:
    for v in m.params.index:
        rows.append({
            'spec': label,
            'variable': v,
            'coef': m.params[v],
            'hac_se': m.bse[v],
            't': m.tvalues[v],
            'p': m.pvalues[v],
            'sig': ('***' if m.pvalues[v] < 0.01 else
                    '**'  if m.pvalues[v] < 0.05 else
                    '*'   if m.pvalues[v] < 0.10 else 'n.s.')
        })
    rows.append({
        'spec': label, 'variable': '__N__',
        'coef': int(m.nobs), 'hac_se': np.nan, 't': np.nan,
        'p': np.nan, 'sig': ''
    })
    rows.append({
        'spec': label, 'variable': '__R2__',
        'coef': m.rsquared, 'hac_se': np.nan, 't': np.nan,
        'p': np.nan, 'sig': ''
    })

tbl = pd.DataFrame(rows)
tbl.to_csv(OUT / 'bose_replication_results.csv', index=False)

# Human-readable summary
with open(OUT / 'bose_replication_summary.txt', 'w') as f:
    for label, m in results:
        f.write('=' * 72 + '\n')
        f.write(label + '\n')
        f.write('=' * 72 + '\n')
        # Date/Time lines removed so the file is byte-reproducible.
        txt = '\n'.join(l for l in m.summary().as_text().splitlines()
                         if not l.startswith(('Date:', 'Time:')))
        f.write(txt + '\n\n')

print(tbl.to_string(index=False, float_format=lambda x: f'{x:.4f}'))
print('\n--- Compact coefficient comparison ---')
piv_coef = tbl.pivot(index='variable', columns='spec', values='coef').round(3)
piv_sig  = tbl.pivot(index='variable', columns='spec', values='sig')
for v in ['const', 'lnV_lag1', 'D_BAN', 'D_NTB', 'lnER', 'D_crisis', '__N__', '__R2__']:
    if v in piv_coef.index:
        line = f'  {v:<10s} '
        for s in piv_coef.columns:
            c = piv_coef.loc[v, s]
            sig = piv_sig.loc[v, s] if v not in ('__N__', '__R2__') else ''
            line += f' {c:>10.3f} {sig:<4s} |'
        print(line)
