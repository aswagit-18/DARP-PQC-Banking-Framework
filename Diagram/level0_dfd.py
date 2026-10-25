from graphviz import Digraph

dot = Digraph("PQC_DFD", format="png")

dot.attr(
    rankdir="TB",
    splines="ortho",
    nodesep="0.6",
    ranksep="0.7",
    bgcolor="white"
)

dot.attr(
    "node",
    fontname="Times New Roman",
    fontsize="11",
    style="filled",
    color="#1F4E79"
)

dot.attr(
    "edge",
    fontname="Times New Roman",
    fontsize="9",
    arrowsize="0.8"
)

dot.node(
    "analyst",
    "Researcher / Banking\nSecurity Analyst",
    shape="box",
    fillcolor="#D6EAF8"
)

dot.node(
    "p1",
    "1. Load and Validate\nBanking Data",
    shape="ellipse",
    fillcolor="#EAF2F8"
)

dot.node(
    "p2",
    "2. Direct Risk Assessment\nand Dependency Graph",
    shape="ellipse",
    fillcolor="#EAF2F8"
)

dot.node(
    "p3",
    "3. Path-Aware Risk Propagation\nand Ecosystem Risk",
    shape="ellipse",
    fillcolor="#FCF3CF"
)

dot.node(
    "p4",
    "4. PQC Remediation Simulation\nand Dynamic Prioritization",
    shape="ellipse",
    fillcolor="#D5F5E3"
)

dot.node(
    "d1",
    "D1\nbanking_assets.csv",
    shape="cylinder",
    fillcolor="#F8F9F9"
)

dot.node(
    "d2",
    "D2\nbanking_services.csv",
    shape="cylinder",
    fillcolor="#F8F9F9"
)

dot.node(
    "d3",
    "D3\nbanking_dependencies.csv",
    shape="cylinder",
    fillcolor="#F8F9F9"
)

dot.node(
    "output",
    "Risk Tables\nDelta ER\nMigration Sequence\nModel Comparison",
    shape="box",
    fillcolor="#E8DAEF"
)

dot.edge(
    "analyst",
    "p1",
    label="Dataset / Parameters"
)

dot.edge(
    "d1",
    "p1",
    label="Asset Data"
)

dot.edge(
    "d2",
    "p1",
    label="Service Data"
)

dot.edge(
    "d3",
    "p1",
    label="Dependency Data"
)

dot.edge(
    "p1",
    "p2",
    label="Validated Data"
)

dot.edge(
    "p2",
    "p3",
    label="Direct Risk + Graph"
)

dot.edge(
    "p3",
    "p4",
    label="Service Risk + ER"
)

dot.edge(
    "p4",
    "output",
    label="Prioritized Results"
)

dot.edge(
    "output",
    "analyst",
    label="Analysis Output"
)

dot.render("level0_dfd", cleanup=True)

print("Generated: level0_dfd.png")