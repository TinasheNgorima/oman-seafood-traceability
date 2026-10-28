"""
06_figures.py - render the Layer 2 institutional multigraph.

Reads the pipeline's network outputs (layer2_nodes.csv, layer2_edges.csv,
layer2_centrality.csv) and draws the directed multigraph. Node size and
colour are keyed to eigenvector centrality, so the figure cannot drift
from the computed values. Parallel edges between the same pair (the
MAFWR->Exporter regulatory_authority and export_ban relations) are drawn
as separate curved arcs.

Outputs figure_2_layer2_multigraph.pdf and .png at 300 dpi.

British English. No seaborn. Single figure per call.
"""
import textwrap

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.lines import Line2D
from common import OUT, FIG

NODES = OUT / "layer2_nodes.csv"
EDGES = OUT / "layer2_edges.csv"
CENTRALITY = OUT / "layer2_centrality.csv"
OUT_STEM = FIG / "figure_3_layer2_multigraph"   # Figure 3 in the chapter

# Edge styling by relation type (colour, line style).
EDGE_STYLE = {
    "regulatory_authority": ("#1b4965", "solid"),
    "certification":        ("#2a9d8f", "solid"),
    "supply":               ("#5c5c5c", "solid"),
    "audit":                ("#7b2cbf", "dashed"),
    "notification":         ("#c1121f", "dashed"),
    "export_ban":           ("#e85d04", "solid"),
}

# Node fill by actor class.
TYPE_FILL = {
    "regulator_domestic": "#dCE5ec",
    "regulator_eu":       "#f3dce0",
    "firm_class":         "#e8efe9",
}


def load():
    nodes = pd.read_csv(NODES)
    edges = pd.read_csv(EDGES)
    cent = pd.read_csv(CENTRALITY).set_index("node")
    return nodes, edges, cent


def build_graph(nodes, edges):
    g = nx.MultiDiGraph()
    for _, r in nodes.iterrows():
        g.add_node(r["node"], type=r["type"], label=r["label"])
    for _, r in edges.iterrows():
        g.add_edge(r["source"], r["target"],
                   edge_type=r["edge_type"], weight=int(r["weight"]))
    return g


def layout(g):
    # Fixed layout encoding the governance topology: domestic regulators
    # across the top, the firm supply chain along the middle (Processor ->
    # Exporter -> EU_Buyer), and the EU alert/audit bodies along the
    # bottom. Coordinates are hand-set for legibility and reproducibility.
    return {
        "MAFWR":    (-3.2,  2.4),
        "FQCC":     (-0.4,  2.4),
        "EU_FVO":   ( 2.8,  2.4),
        "Processor":(-2.2,  0.4),
        "Exporter": ( 0.4,  0.4),
        "EU_Buyer": ( 3.0,  0.4),
        "EU_CA":    ( 2.6, -1.8),
        "RASFF":    ( 0.0, -1.8),
    }


def draw(g, pos, cent):
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_axis_off()

    nodelist = list(g.nodes)
    eig = cent["eigenvector"]
    sizes = {n: 1400 + 7000 * eig.get(n, 0.0) for n in nodelist}
    size_list = [sizes[n] for n in nodelist]
    fills = {n: TYPE_FILL.get(g.nodes[n]["type"], "#eeeeee") for n in nodelist}

    # Nodes.
    nx.draw_networkx_nodes(
        g, pos, ax=ax, nodelist=nodelist,
        node_size=size_list,
        node_color=[fills[n] for n in nodelist],
        edgecolors="#222222", linewidths=1.4)

    # Edges: draw each parallel edge on its own arc.
    pair_index = {}
    for u, v, k, d in g.edges(keys=True, data=True):
        seen = pair_index.get((u, v), 0)
        pair_index[(u, v)] = seen + 1
        rad = 0.12 + 0.18 * seen           # offset parallel edges
        if (v, u) in g.edges():
            rad += 0.08                    # separate reciprocal pairs
        colour, ls = EDGE_STYLE.get(d["edge_type"], ("#999999", "solid"))
        nx.draw_networkx_edges(
            g, pos, ax=ax, edgelist=[(u, v)],
            connectionstyle=f"arc3,rad={rad}",
            edge_color=colour, style=ls, width=0.6 + 0.12 * d["weight"],
            arrows=True, arrowsize=16, arrowstyle="-|>",
            node_size=size_list, alpha=0.85)

    # Node labels: short code plus eigenvector value.
    labels = {n: f"{n}\n(e={eig.get(n, 0):.2f})" for n in g.nodes}
    nx.draw_networkx_labels(g, pos, labels, ax=ax, font_size=9,
                            font_family="DejaVu Sans")

    # Legend for edge types.
    handles = [Line2D([0], [0], color=c, linestyle=s, lw=2,
                      label=t.replace("_", " "))
               for t, (c, s) in EDGE_STYLE.items()]
    ax.legend(handles=handles, loc="upper left", frameon=True,
              fontsize=8, title="Relation type", title_fontsize=9,
              bbox_to_anchor=(0.0, 1.0))
    ax.margins(0.16)

    ax.set_title(
        "Layer 2 — Institutional governance multigraph for Oman seafood "
        "SPS oversight\nNode size keyed to eigenvector centrality; "
        "MAFWR\u2192Exporter carries two parallel relations",
        fontsize=11, loc="left")

    fig.tight_layout()
    fig.savefig(f"{OUT_STEM}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT_STEM}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    nodes, edges, cent = load()
    g = build_graph(nodes, edges)
    pos = layout(g)
    draw(g, pos, cent)
    n_par = edges.groupby(["source", "target"]).size()
    print(f"Rendered {OUT_STEM.name}.pdf/.png | "
          f"{g.number_of_nodes()} nodes, {g.number_of_edges()} edges, "
          f"{(n_par > 1).sum()} parallel-edge pair(s)")


if __name__ == "__main__":
    main()
