"""
00_fetch_external.py

Pulls the two external snapshots required by the panel:
    - Eurostat COMEXT DS-045409, EU-27 imports of HS chapter 03 from
      Oman, 2000-2024 (annual, value EUR + quantity 100kg).
    - ECB SDW EXR A.USD.EUR.SP00.A annual average.

Both are idempotent. Re-running overwrites local snapshots, so the
session can be reproduced from a clean clone of the project folder.
"""
import requests
import pandas as pd
import json
import hashlib
import datetime
from common import EXT, CFG, IN


# Eurostat COMEXT
def fetch_eurostat():
    base = ('https://ec.europa.eu/eurostat/api/comext/dissemination/'
            'statistics/1.0/data/DS-045409')
    r = requests.get(base, params=dict(format='JSON', lang='EN',
                                       REPORTER='EU27_2020',
                                       PARTNER='OM',
                                       PRODUCT='03',
                                       FLOW='1'),
                     timeout=60)
    r.raise_for_status()
    j = r.json()
    dim_ids = j['id']
    sizes = j['size']
    keys = {d: sorted(j['dimension'][d]['category']['index'].items(),
                      key=lambda kv: kv[1]) for d in dim_ids}
    keys_only = {d: [k for k, _ in keys[d]] for d in dim_ids}
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    fi = dim_ids.index('freq')
    ii = dim_ids.index('indicators')
    ti = dim_ids.index('time')

    rows = []
    for f, fk in enumerate(keys_only['freq']):
        if fk != 'A':
            continue
        for i, ik in enumerate(keys_only['indicators']):
            for t, tk in enumerate(keys_only['time']):
                if '-' in tk:
                    continue
                idxs = [0] * len(sizes)
                idxs[fi] = f; idxs[ii] = i; idxs[ti] = t
                flat = sum(idxs[k] * strides[k] for k in range(len(sizes)))
                v = j['value'].get(str(flat))
                if v is not None and 2000 <= int(tk) <= 2024:
                    rows.append(dict(year=int(tk), indicator=ik, value=v))

    df = (pd.DataFrame(rows)
            .pivot_table(index='year', columns='indicator',
                         values='value').reset_index())
    df.columns.name = None
    df['quantity_tonnes']      = df['QUANTITY_IN_100KG'] * 0.1
    df['value_million_eur']    = df['VALUE_IN_EUROS'] / 1e6
    df['unit_value_eur_per_kg'] = df['VALUE_IN_EUROS'] / (df['QUANTITY_IN_100KG'] * 100)
    out = df[['year', 'VALUE_IN_EUROS', 'value_million_eur',
              'quantity_tonnes', 'unit_value_eur_per_kg']].rename(
                  columns={'VALUE_IN_EUROS': 'value_eur'})
    out.to_csv(EXT / IN['eurostat_csv'], index=False)
    print(f'  Eurostat COMEXT: {len(out)} years 2000-2024 -> '
          f'eurostat_eu27_imp_oman_hs03_annual_2000_2024.csv')


# ECB EXR
def fetch_ecb():
    r = requests.get(
        'https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A',
        headers={'Accept': 'application/json'},
        timeout=30)
    r.raise_for_status()
    j = r.json()
    obs = j['dataSets'][0]['series']['0:0:0:0:0']['observations']
    times = j['structure']['dimensions']['observation'][0]['values']
    rows = []
    for k, v in obs.items():
        rows.append((times[int(k)]['id'], v[0]))
    df = pd.DataFrame(rows, columns=['year', 'usd_per_eur'])
    df['year'] = df['year'].astype(int)
    df = df[(df['year'] >= 2000) & (df['year'] <= 2024)].reset_index(drop=True)
    # OMR fixed peg 1 OMR = 2.6008 USD
    df['eur_per_omr'] = CFG['layer3']['omr_usd_peg'] / df['usd_per_eur']
    df.to_csv(EXT / IN['ecb_csv'], index=False)
    print(f'  ECB EXR: {len(df)} years 2000-2024 -> '
          f'ecb_eur_per_omr_annual_2000_2024.csv')


def write_manifest():
    # Checksums + retrieval date, so a refreshed snapshot is distinguishable from the deposited one.
    files = [IN['eurostat_csv'], IN['ecb_csv']]
    lines = [f"{hashlib.sha256((EXT / f).read_bytes()).hexdigest()}  {f}" for f in files]
    (EXT / 'checksums.sha256').write_text("\n".join(lines) + "\n")
    (EXT / 'retrieved_at.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n")


if __name__ == '__main__':
    fetch_eurostat()
    fetch_ecb()
    write_manifest()
    print('  NOTE: snapshots refreshed. Compare data/external/checksums.sha256 with the deposited version '
          'before comparing results with the chapter.')
