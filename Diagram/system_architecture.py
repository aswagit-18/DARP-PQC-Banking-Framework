from graphviz import Digraph

dot = Digraph("PQC_System_Architecture", format="png")

dot.attr(
    rankdir="TB",
    splines="ortho",
    nodesep="0.5",
    ranksep="0.6",
    bgcolor="white"
)

dot.attr(
    "node",
    shape="box",
    style="rounded,filled",
    fontname="Times New Roman",
    fontsize="11",
    color="#1F4E79",
    fillcolor="#EAF2F8",
    penwidth="1.5"
)

dot.attr(
    "edge",
    color="#404040",
    penwidth="1.2",
    arrowsize="0.8"
)

dot.node(
    "dataset",
    "SYNTHETIC DIGITAL BANKING ECOSYSTEM\n"
    "250 Assets | 20 Banking Services | 720 Dependencies"
)

dot.node(
    "loader",
    "DATA LOADING AND VALIDATION\n"
    "Assets | Services | Dependencies"
)

dot.node(
    "risk",
    "DIRECT QUANTUM RISK MODEL\n"
    "Quantum Vulnerability + Data Sensitivity\n"
    "+ Data Lifetime + Business Criticality\n"
    "+ External Exposure"
)

dot.node(
    "graph",
    "MULTI-TIER DEPENDENCY GRAPH\n"
    "Service → Internal → Third-Party → Sub-Tier"
)

dot.node(
    "propagation",
    "PATH-AWARE RISK PROPAGATION\n"
    "Path Risk = Direct Risk × Product(Dependency Strengths)"
)

dot.node(
    "service",
    "SERVICE-LEVEL RISK\n"
    "Direct Service Risk + Inherited Quantum Risk"
)

dot.node(
    "ecosystem",
    "ECOSYSTEM-WIDE QUANTUM RISK\n"
    "Criticality-Weighted ER Score"
)

dot.node(
    "remediation",
    "PQC REMEDIATION SIMULATION\n"
    "Delta ER = ER_before - ER_after"
)

dot.node(
    "priority",
    "DYNAMIC MIGRATION PRIORITIZATION\n"
    "Priority = Delta ER / Migration Cost"
)

dot.node(
    "output",
    "EXPERIMENTAL OUTPUTS\n"
    "Migration Ranking | Comparison Tables | Figures"
)

dot.edge("dataset", "loader")
dot.edge("loader", "risk")
dot.edge("risk", "graph")
dot.edge("graph", "propagation")
dot.edge("propagation", "service")
dot.edge("service", "ecosystem")
dot.edge("ecosystem", "remediation")
dot.edge("remediation", "priority")
dot.edge("priority", "output")

dot.render("system_architecture", cleanup=True)

print("Generated: system_architecture.png")