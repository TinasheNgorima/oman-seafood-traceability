"""
02_bose_replication_panel.py

Assembles the annual panel used for the Bose-style lightweight replication
of Oman -> EU-27 fish exports over 2000-2024.

Output: bose_replication_panel.csv with columns:
    year, V_eur, lnV, lnV_lag1, qty_tonnes, eur_per_omr, lnER,
    D_BAN, D_NTB, D_NTB_max, D_crisis,
and notes on each construction decision.

Data sources:
- Eurostat COMEXT DS-045409, EU-27 (2020 def.) imports of HS chapter 03
  from Oman, 2000-2024 (value EUR, quantity 100kg).
- ECB SDW EXR A.USD.EUR.SP00.A annual averages.
- Bose et al. (2017) extract: export_ban_decisions sheet for D_BAN
  2011-2014; rasff_notifications sheet for D_NTB 2004-2013.
- Published RASFF reviews (Roszko et al. 2023; El Sheikha et al. 2024)
  searched for post-2013 Oman-origin fish notifications; none identified
  beyond those already in Bose. D_NTB set to 0 post-2013 in the
  conservative specification, with a sensitivity variant D_NTB_max that
  treats 2014-2019 as unknown and equal to the 2010-2013 mean rate.
"""
import pandas as pd
import numpy as np
from common import EXT, OUT, CFG, IN

# 1) Trade panel
trade = pd.read_csv(EXT / IN['eurostat_csv'])
trade = trade.rename(columns={'value_eur': 'V_eur',
                              'quantity_tonnes': 'qty_tonnes'})

# 2) Exchange rate
fx = pd.read_csv(EXT / IN['ecb_csv'])

panel = trade.merge(fx[['year', 'eur_per_omr']], on='year', how='left')
panel['lnV'] = np.log(panel['V_eur'])
panel['lnV_lag1'] = panel['lnV'].shift(1)
panel['lnER'] = np.log(panel['eur_per_omr'])

# 3) D_BAN — Oman's seasonal/standing export restriction on the main
#    commercial species (kanad, sahwa, jaydar group) ran continuously from
#    2011. Bose Table 2 covers MD 2/2011, 5/2011, 108/2011, 6/2012 etc.
#    through 2014. Action A (MJLA Official Gazette catalogue check, 2026)
#    confirmed annual re-issues of the "Governing Fish Exports" decree for
#    every year 2015-2018 (Gazette refs SHOW/127, /155, /259, /289, /473,
#    /509, /515, /620), and that MD 75/2019 (Gazette 1284, eff. 4/3/2019)
#    repealed the annual model and established a STANDING year-round export
#    restriction in force 2019-2024 (Arts 2-3: absolute ban on kanad and
#    sahwa; jaydar export restricted to canned/air-freight via central
#    market). The MD 230/2014 Aug-Oct kingfish *fishing* closure is a
#    domestic conservation measure and is deliberately excluded from D_BAN
#    (it is not an EU-export trade restriction). D_BAN is therefore 1 for
#    2011-2024; pre-2011 (2000-2010) is the unrestricted baseline that
#    identifies the coefficient, replicating Bose's own design extended
#    forward.
ban_years = set(CFG['layer3']['ban_years'])  # 2011-2024 inclusive
panel['D_BAN'] = panel['year'].isin(ban_years).astype(int)

# 4) D_NTB — Bose RASFF table records notifications in
#    {2004, 2005, 2006, 2008, 2010, 2011, 2012, 2013}.
ntb_years_obs = set(CFG['layer3']['ntb_years_observed'])
panel['D_NTB'] = panel['year'].isin(ntb_years_obs).astype(int)

# Maximalist sensitivity variant: treat 2014-2019 as plausibly
# notified at the 2010-2013 mean rate (= 1.0) and 2020-2024 at the
# RASFF Window-observable rate (no Oman fish notifications
# identified in published reviews; set to 0).
panel['D_NTB_max'] = panel['D_NTB'].copy()
panel.loc[panel['year'].isin(CFG['layer3']['ntb_max_extra_years']), 'D_NTB_max'] = 1

# 5) D_crisis — Bose specification dummies for 2009 and 2010 EU
#    downturn.
panel['D_crisis'] = panel['year'].isin(set(CFG['layer3']['crisis_years'])).astype(int)

out_cols = ['year', 'V_eur', 'qty_tonnes', 'eur_per_omr',
            'lnV', 'lnV_lag1', 'lnER',
            'D_BAN', 'D_NTB', 'D_NTB_max', 'D_crisis']
panel = panel[out_cols].round(6)
panel.to_csv(OUT / 'bose_replication_panel.csv', index=False)

print(panel.to_string(index=False))
print(f"\nRows: {len(panel)} | Years: {panel['year'].min()}-{panel['year'].max()}")
print(f"D_BAN active years: {sorted(panel.loc[panel.D_BAN==1,'year'].tolist())}")
print(f"D_NTB (Bose-observed) active years: {sorted(panel.loc[panel.D_NTB==1,'year'].tolist())}")
