"""
04b_layer2_sensitivity.py

Sensitivity of the Layer 2 centrality results (04_layer2_network.py) to edge weights,
single edges and node aggregation, added in response to peer review. None of these
analyses was in the analysis plan (docs/DEVIATIONS.md, Section C). Reads only
outputs/layer2_edges.csv and outputs/layer2_nodes.csv, so it runs in derived-only mode.

Centrality definitions are those of 04: eigenvector on the weighted undirected
projection, PageRank on the weighted multigraph, betweenness unweighted and normalised,
degree as weighted in-degree plus out-degree.

Checks:
    Reweighting: every edge weight multiplied by an independent U(perturb_range) draw,
        perturb_draws times, seed from config.yaml.
    Leave one edge out: each of the 13 edges removed in turn.
    Unit weights: every edge weight set to 1.
    Node merges: EU_CA with RASFF (one EU alert node), FQCC into MAFWR.
    Eigenvector against weighted degree: residual from a linear fit of eigenvector
        centrality on weighted total degree.

Outputs:
    layer2_reweight_summary.csv  layer2_leave_one_out.csv  layer2_unweighted.csv
    layer2_node_merge.csv        layer2_eig_vs_degree.csv
"""
import networkx as nx
import numpy as np
import pandas as pd

from common import CFG, OUT, SEED

L2 = CFG["layer2"]
E = pd.read_csv(OUT / "layer2_edges.csv")
NODES = pd.read_csv(OUT / "layer2_nodes.csv").node.tolist()
DOMESTIC = ["MAFWR", "FQCC", "Processor"]


def build(edges, nodes=NODES):
    G = nx.MultiDiGraph()
    G.add_nodes_from(nodes)
    for s, t, w in zip(edges.source, edges.target, edges.weight):
        G.add_edge(s, t, weight=w)
    return G


def metrics(G):
    m = pd.DataFrame({
        "eigenvector": nx.eigenvector_centrality_numpy(G.to_undirected(), weight="weight"),
        "pagerank": nx.pagerank(G, weight="weight"),
        "betweenness": nx.betweenness_centrality(G, weight=None, normalized=True),
        "degree_w": {n: G.in_degree(n, weight="weight") + G.out_degree(n, weight="weight") for n in G},
    })
    # Rank on values rounded to 1e-10 so that exact ties (FQCC and EU_FVO under unit weights)
    # share a rank instead of being split by floating-point noise from the eigensolver.
    m["eig_rank"] = m.eigenvector.round(10).rank(ascending=False, method="min").astype(int)
    return m


base = metrics(build(E))
cen = pd.read_csv(OUT / "layer2_centrality.csv").set_index("node")
assert np.allclose(base.loc[cen.index, ["eigenvector", "pagerank", "betweenness"]].to_numpy(),
                   cen[["eigenvector", "pagerank", "betweenness"]].to_numpy(), atol=1e-9), \
    "baseline does not reproduce layer2_centrality.csv"

# ------------------------------------------------------------------ reweighting
rng = np.random.default_rng(SEED)
lo, hi = L2["perturb_range"]
R = int(L2["perturb_draws"])
eig_first = dict.fromkeys(NODES, 0)
eig_top3 = dict.fromkeys(NODES, 0)
prk_first = dict.fromkeys(NODES, 0)
for _ in range(R):
    m = metrics(build(E.assign(weight=E.weight * rng.uniform(lo, hi, len(E)))))
    order = m.eigenvector.sort_values(ascending=False).index
    eig_first[order[0]] += 1
    for n in order[:3]:
        eig_top3[n] += 1
    prk_first[m.pagerank.idxmax()] += 1
rw = pd.DataFrame({"node": NODES,
                   "baseline_eigenvector": base.loc[NODES, "eigenvector"].to_numpy(),
                   "baseline_eig_rank": base.loc[NODES, "eig_rank"].to_numpy(),
                   "share_eig_first": [eig_first[n] / R for n in NODES],
                   "share_eig_top3": [eig_top3[n] / R for n in NODES],
                   "share_pagerank_first": [prk_first[n] / R for n in NODES],
                   "draws": R, "range_low": lo, "range_high": hi, "seed": SEED})
rw.sort_values(["baseline_eig_rank", "node"]).to_csv(OUT / "layer2_reweight_summary.csv", index=False)

# ------------------------------------------------------------------ leave one edge out
rows = []
for i, r in E.iterrows():
    m = metrics(build(E.drop(index=i)))
    top3 = m.eigenvector.sort_values(ascending=False).index[:3].tolist()
    rows.append({"dropped_edge": f"{r.source}->{r.target}", "edge_type": r.edge_type, "weight": r.weight,
                 "eig_first": top3[0], "eig_top3": ";".join(top3),
                 "exporter_eig": m.loc["Exporter", "eigenvector"],
                 "processor_eig": m.loc["Processor", "eigenvector"],
                 "mafwr_eig": m.loc["MAFWR", "eigenvector"],
                 "processor_eig_rank": m.loc["Processor", "eig_rank"],
                 "processor_in_eig_top3": "Processor" in top3,
                 "exporter_pagerank_first": m.pagerank.idxmax() == "Exporter",
                 "exporter_betweenness_first": m.betweenness.idxmax() == "Exporter",
                 "mafwr_domestic_betweenness_first": m.loc[DOMESTIC, "betweenness"].idxmax() == "MAFWR"})
pd.DataFrame(rows).to_csv(OUT / "layer2_leave_one_out.csv", index=False)

# ------------------------------------------------------------------ unit weights
mu = metrics(build(E.assign(weight=1)))
mu.rename_axis("node").reset_index().sort_values(["eig_rank", "node"]).to_csv(OUT / "layer2_unweighted.csv", index=False)

# ------------------------------------------------------------------ node merges
MERGES = {"EU_CA+RASFF->EU_ALERT": {"EU_CA": "EU_ALERT", "RASFF": "EU_ALERT"},
          "FQCC->MAFWR": {"FQCC": "MAFWR"}}
rows = []
for name, mp in MERGES.items():
    Em = E.replace({"source": mp, "target": mp})
    Em = Em[Em.source != Em.target]            # an edge between merged nodes becomes a self-loop and is dropped
    nodes = list(dict.fromkeys(mp.get(n, n) for n in NODES))
    m = metrics(build(Em, nodes))
    for n in m.rename_axis("node").reset_index().sort_values(["eig_rank", "node"]).node:
        rows.append({"merge": name, "node": n, "edges": len(Em), **m.loc[n].to_dict(),
                     "eig_rank": int(m.loc[n, "eig_rank"])})
pd.DataFrame(rows).to_csv(OUT / "layer2_node_merge.csv", index=False)

# ------------------------------------------------------------------ eigenvector against weighted degree
b = base.copy()
b["deg_rank"] = b.degree_w.rank(ascending=False, method="min").astype(int)
slope, intercept = np.polyfit(b.degree_w, b.eigenvector, 1)
b["eig_predicted"] = intercept + slope * b.degree_w
b["eig_minus_predicted"] = b.eigenvector - b.eig_predicted
b["fit_slope"], b["fit_intercept"] = slope, intercept
(b.rename_axis("node").reset_index()
 [["node", "degree_w", "deg_rank", "eigenvector", "eig_rank", "eig_predicted", "eig_minus_predicted",
   "fit_slope", "fit_intercept"]]
 .sort_values(["eig_rank", "node"]).to_csv(OUT / "layer2_eig_vs_degree.csv", index=False))

# ------------------------------------------------------------------ console summary
for f in ("layer2_reweight_summary", "layer2_leave_one_out", "layer2_unweighted",
          "layer2_node_merge", "layer2_eig_vs_degree"):
    print(f"--- {f}.csv")
    print(pd.read_csv(OUT / f"{f}.csv").round(3).to_string(index=False), "\n")
