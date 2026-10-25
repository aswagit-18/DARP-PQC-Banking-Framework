from graphviz import Digraph

dot = Digraph("PQC_Sequence_Diagram", format="png")

dot.attr(
    rankdir="TB",
    nodesep="0.5",
    ranksep="0.55",
    bgcolor="white"
)

dot.attr(
    "node",
    shape="box",
    style="rounded,filled",
    fillcolor="#EAF2F8",
    color="#1F4E79",
    fontname="Times New Roman",
    fontsize="10"
)

dot.attr(
    "edge",
    fontname="Times New Roman",
    fontsize="8",
    arrowsize="0.8"
)

dot.node("researcher", "Researcher / Analyst")
dot.node("main", "main.py")
dot.node("loader", "data_loader.py")
dot.node("risk", "risk_model.py")
dot.node("graph", "graph_builder.py")
dot.node("propagation", "propagation.py")
dot.node("ecosystem", "ecosystem_risk.py")
dot.node(
    "remediation",
    "remediation.py",
    fillcolor="#FCF3CF"
)
dot.node(
    "priority",
    "prioritization.py",
    fillcolor="#D5F5E3"
)
dot.node(
    "results",
    "Results\nTables + Figures",
    fillcolor="#E8DAEF"
)

dot.edge(
    "researcher",
    "main",
    label="Run Framework"
)

dot.edge(
    "main",
    "loader",
    label="Load Dataset"
)

dot.edge(
    "loader",
    "risk",
    label="Validated Data"
)

dot.edge(
    "risk",
    "graph",
    label="Direct Risk"
)

dot.edge(
    "graph",
    "propagation",
    label="Dependency Graph"
)

dot.edge(
    "propagation",
    "ecosystem",
    label="Inherited Risk"
)

dot.edge(
    "ecosystem",
    "remediation",
    label="Baseline ER"
)

dot.edge(
    "remediation",
    "priority",
    label="Delta ER for Candidates"
)

dot.edge(
    "priority",
    "remediation",
    label="Select Best Asset",
    constraint="false"
)

dot.edge(
    "priority",
    "results",
    label="Final Migration Sequence"
)

dot.edge(
    "results",
    "researcher",
    label="Risk Results"
)

dot.render(
    "sequence_diagram",
    cleanup=True
)

print("Generated: sequence_diagram.png")