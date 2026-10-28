# D_BAN coding evidence

D_BAN = 1 for 2011-2024 (14 years). 2000-2010 is the unrestricted baseline that identifies the coefficient. The ban is coded as an export-restriction regime, not as a sanitary measure.

| Years | Basis | Source |
|---|---|---|
| 2011-2014 | Annual "Governing Fish Exports" decisions, including MD 2/2011, 5/2011, 108/2011, 6/2012 | Bose et al. (2017), Table 2 |
| 2015-2018 | Annual re-issues of the same decree. Gazette references named in `02_bose_replication_panel.py`: SHOW/127, /155, /259, /289, /473, /509, /515, /620 | MJLA Official Gazette decisions index |
| 2019-2024 | MD 75/2019 (Official Gazette 1284, effective 4 March 2019). Repeals MD 132/2018. Absolute ban on kanad and sahwa, jaydar restricted to canned or air-freight via the central market, mandatory domestic supply quotas | MJLA Official Gazette |
| excluded | MD 230/2014 (August-October kingfish **fishing** closure) | Domestic conservation measure, not an export restriction |
| excluded | Import bans on foreign origins that appear in the same index (Colombia, Iraq, France, Romania, Faroe Islands, Italy, Denmark and others) | Not Oman export-side decisions |

**Per-year decision table.** `data/d_ban_decisions.csv` lists each MJLA decision page (show ID, URL, issue date as d/m/y, subject, whether it enters the coding). Every year 2011-2019 has at least one export-regulation decision. The 2019 decision (MD 75/2019, show/723, 4 March 2019) is a standing regime and covers 2019-2024.

**Note.** MD 75/2019 takes effect on 4 March 2019, so 2019 is a partial year under the old regime. The coding treats 2019 as 1 under both.
