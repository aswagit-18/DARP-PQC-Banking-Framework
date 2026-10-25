from graphviz import Digraph

dot = Digraph("PQC_Use_Case", format="png")

dot.attr(
    rankdir="LR",
    bgcolor="white",
    nodesep="0.4",
    ranksep="0.6"
)

dot.attr(
    "node",
    fontname="Times New Roman",
    fontsize="10"
)

dot.attr(
    "edge",
    fontname="Times New Roman",
    fontsize="8"
)

dot.node(
    "actor",
    "Researcher /\nBanking Security Analyst",
    shape="box",
    style="rounded,filled",
    fillcolor="#D6EAF8"
)

with dot.subgraph(name="cluster_system") as system:
    system.attr(
        label="Dependency-Aware PQC Banking Risk Framework",
        color="#1F4E79",
        penwidth="1.5",
        fontname="Times New Roman"
    )

    system.node("u1", "Load Banking Dataset", shape="ellipse")
    system.node("u2", "Validate Dataset", shape="ellipse")
    system.node("u3", "Configure Risk Parameters", shape="ellipse")
    system.node("u4", "Calculate Direct Quantum Risk", shape="ellipse")
    system.node("u5", "Build Dependency Graph", shape="ellipse")
    system.node("u6", "Calculate Inherited Risk", shape="ellipse")
    system.node("u7", "Calculate Ecosystem Risk", shape="ellipse")
    system.node("u8", "Simulate PQC Remediation", shape="ellipse")
    system.node("u9", "Calculate Delta ER", shape="ellipse")
    system.node("u10", "Rank Migration Priorities", shape="ellipse")
    system.node("u11", "Run Dynamic Migration Strategy", shape="ellipse")
    system.node("u12", "Compare Baseline Models", shape="ellipse")
    system.node("u13", "Review Results and Figures", shape="ellipse")

for use_case in [
    "u1",
    "u3",
    "u10",
    "u11",
    "u12",
    "u13"
]:
    dot.edge(
        "actor",
        use_case,
        arrowhead="none"
    )

dot.edge("u1", "u2", label="<<include>>")
dot.edge("u2", "u4", label="<<include>>")
dot.edge("u4", "u5", label="<<include>>")
dot.edge("u5", "u6", label="<<include>>")
dot.edge("u6", "u7", label="<<include>>")
dot.edge("u8", "u9", label="<<include>>")
dot.edge("u9", "u10", label="<<include>>")
dot.edge("u10", "u11", label="<<include>>")

dot.render("use_case_diagram", cleanup=True)

print("Generated: use_case_diagram.png")