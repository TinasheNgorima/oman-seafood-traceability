"""
04_layer2_network.py

Constructs the directed institutional-actor network from the Bose
2017 extract sheets:
    - regulatory_md_timeline   (MAFWR -> downstream regulatory targets)
    - haccp_qc_establishments  (FQCC -> processor class certification load)
    - rasff_notifications      (EU CA -> RASFF; RASFF -> MAFWR)
    - export_ban_decisions     (MAFWR -> exporter class)
    - eu_fvo_findings          (EU-FVO -> MAFWR)

Nodes (8): MAFWR, FQCC, EU_FVO, RASFF, EU_CA, Processor, Exporter, EU_Buyer.
Edges are typed:
    'regulatory_authority'  MD-issuance
    'certification'         FQCC -> processor
    'notification'           CA -> RASFF, RASFF -> MAFWR
    'supply'                Processor -> Exporter -> EU_Buyer
    'audit'                 EU_FVO -> MAFWR (with deficiency count weight)
    'export_ban'            MAFWR -> Exporter (with ban-count weight)

Outputs:
    layer2_edges.csv
    layer2_nodes.csv
    layer2_centrality.csv
    layer2_network.gexf  (Gephi / NetworkX interchange)
"""
import pandas as pd
import networkx as nx
from common import RAW, OUT, IN

src = RAW / IN['layer23_xlsx']
mds   = pd.read_excel(src, sheet_name='regulatory_md_timeline')
hqc   = pd.read_excel(src, sheet_name='haccp_qc_establishments')
ras   = pd.read_excel(src, sheet_name='rasff_notifications')
ban   = pd.read_excel(src, sheet_name='export_ban_decisions')
fvo   = pd.read_excel(src, sheet_name='eu_fvo_findings')

NODES = {
    'MAFWR':     {'type': 'regulator_domestic',
                  'label': 'Ministry of Agriculture, Fisheries & Water Resources'},
    'FQCC':      {'type': 'regulator_domestic',
                  'label': 'Fish Quality Control Centre'},
    'EU_FVO':    {'type': 'regulator_eu',
                  'label': 'EU Food & Veterinary Office (now DG SANTE)'},
    'RASFF':     {'type': 'regulator_eu',
                  'label': 'Rapid Alert System for Food & Feed'},
    'EU_CA':     {'type': 'regulator_eu',
                  'label': 'EU Member State Competent Authorities'},
    'Processor': {'type': 'firm_class',
                  'label': 'Domestic processor establishments (QC-certified)'},
    'Exporter':  {'type': 'firm_class',
                  'label': 'Exporter establishments'},
    'EU_Buyer':  {'type': 'firm_class',
                  'label': 'EU importing buyers'}
}

# Edge weights from Bose data
n_mds       = len(mds)                 # 8 MDs 1997-2011
n_processors = int(hqc['qc_certified_establishments'].max())   # peak QC-cert count
n_rasff     = len(ras)                 # 19 RASFF cases 2004-2013
n_ban_dec   = len(ban)                 # 19 ban-decision rows 2011-2014
n_fvo       = len(fvo)                 # 15 FVO deficiency findings

EDGES = [
    ('MAFWR', 'FQCC',      'regulatory_authority', n_mds),
    ('MAFWR', 'Processor', 'regulatory_authority', n_mds),
    ('MAFWR', 'Exporter',  'regulatory_authority', n_mds),
    ('MAFWR', 'Exporter',  'export_ban',           n_ban_dec),
    ('FQCC',  'Processor', 'certification',        n_processors),
    ('Processor','Exporter','supply',              n_processors),
    ('Exporter','EU_Buyer','supply',               n_processors),
    ('EU_Buyer','EU_CA',   'notification',         n_rasff),
    ('EU_CA',  'RASFF',    'notification',         n_rasff),
    ('RASFF',  'MAFWR',    'notification',         n_rasff),
    ('EU_FVO', 'MAFWR',    'audit',                n_fvo),
    ('EU_FVO', 'FQCC',     'audit',                n_fvo),
    ('EU_FVO', 'Processor','audit',                n_fvo),
]

G = nx.MultiDiGraph()
for n, attrs in NODES.items():
    G.add_node(n, **attrs)
for s, t, etype, w in EDGES:
    G.add_edge(s, t, edge_type=etype, weight=w)

# Persist edges/nodes
nodes_df = pd.DataFrame([{'node': n, **a} for n, a in NODES.items()])
edges_df = pd.DataFrame([{'source': s, 'target': t, 'edge_type': e, 'weight': w}
                         for (s, t, e, w) in EDGES])
nodes_df.to_csv(OUT / 'layer2_nodes.csv', index=False)
edges_df.to_csv(OUT / 'layer2_edges.csv', index=False)

# Centrality measures
deg_in   = dict(G.in_degree(weight='weight'))
deg_out  = dict(G.out_degree(weight='weight'))
btw      = nx.betweenness_centrality(G, weight=None, normalized=True)
# Eigenvector centrality: undirected projection (directed eigenvector
# requires strong connectivity, which the institutional network lacks
# by construction — regulators have no incoming supply edges).
eig = nx.eigenvector_centrality_numpy(G.to_undirected(), weight='weight')
prk      = nx.pagerank(G, weight='weight')

cen = pd.DataFrame({
    'node':            list(G.nodes()),
    'degree_in_w':     [deg_in[n]  for n in G.nodes()],
    'degree_out_w':    [deg_out[n] for n in G.nodes()],
    'betweenness':     [btw[n]     for n in G.nodes()],
    'eigenvector':     [eig[n]     for n in G.nodes()],
    'pagerank':        [prk[n]     for n in G.nodes()],
})
cen = cen.sort_values('pagerank', ascending=False).reset_index(drop=True)
cen.to_csv(OUT / 'layer2_centrality.csv', index=False)

nx.write_gexf(G, str(OUT / 'layer2_network.gexf'))

print(f'Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}')
print('Edge-type weights:')
print(edges_df.groupby('edge_type')['weight']
              .agg(['sum', 'count']).reset_index().to_string(index=False))
print('\nCentrality (sorted by PageRank):')
print(cen.round(3).to_string(index=False))
