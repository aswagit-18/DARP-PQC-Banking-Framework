import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_loader import load_data
from risk_model import calculate_direct_risk
from graph_builder import build_graph
from remediation import evaluate_ecosystem, simulate_asset_remediation


class FrameworkSanityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["PQC_DATASET"] = "v1"
        cls.assets, cls.services, cls.dependencies = load_data()

    def test_direct_risk_is_bounded(self):
        risk_assets = calculate_direct_risk(self.assets)
        self.assertTrue(risk_assets["direct_risk"].between(0, 1).all())

    def test_duplicate_dependency_pairs_keep_strongest_edge(self):
        risk_assets = calculate_direct_risk(self.assets)
        graph = build_graph(risk_assets, self.services, self.dependencies)
        # V1 has duplicate A014 -> A027 rows with strengths 1.00 and 0.75.
        edge = graph.get_edge_data("A014", "A027")
        self.assertIsNotNone(edge)
        self.assertAlmostEqual(float(edge["dependency_strength"]), 1.00, places=9)

    def test_ecosystem_risk_is_bounded(self):
        result = evaluate_ecosystem(self.assets, self.services, self.dependencies)
        self.assertGreaterEqual(result["ecosystem_risk"], 0.0)
        self.assertLessEqual(result["ecosystem_risk"], 1.0)

    def test_remediation_is_monotonic_for_known_high_priority_asset(self):
        before = evaluate_ecosystem(self.assets, self.services, self.dependencies)["ecosystem_risk"]
        remediated = simulate_asset_remediation(self.assets, "A022", 0.0)
        after = evaluate_ecosystem(remediated, self.services, self.dependencies)["ecosystem_risk"]
        self.assertLess(after, before)


if __name__ == "__main__":
    unittest.main()
