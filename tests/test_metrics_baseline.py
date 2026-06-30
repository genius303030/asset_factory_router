import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
METRICS_CSV = REPO_ROOT / "examples" / "metrics" / "owner_pricing_pr_metrics.csv"
METRICS_SCRIPT = REPO_ROOT / "scripts" / "collect_pr_metrics.py"


def load_metrics_module():
    spec = importlib.util.spec_from_file_location("collect_pr_metrics", METRICS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MetricsBaselineTests(unittest.TestCase):
    def setUp(self):
        self.metrics = load_metrics_module()
        self.rows = self.metrics.load_metrics(METRICS_CSV)

    def test_required_pr_rows_are_present(self):
        present_prs = {row["pr_number"] for row in self.rows}
        self.assertEqual(set(self.metrics.REQUIRED_PR_NUMBERS), present_prs)

    def test_metrics_schema_validates(self):
        self.assertEqual([], self.metrics.validate_rows(self.rows))

    def test_all_rows_preserve_production_behavior(self):
        changed_rows = [
            row["pr_number"]
            for row in self.rows
            if row["production_behavior_changed"] != "no"
        ]
        self.assertEqual([], changed_rows)

    def test_owner_pricing_ci_recovery_is_visible(self):
        rows_by_pr = {row["pr_number"]: row for row in self.rows}
        self.assertEqual("fail", rows_by_pr["20"]["ci_status"])
        self.assertEqual("pass", rows_by_pr["21"]["ci_status"])
        self.assertEqual("pass", rows_by_pr["23"]["ci_status"])

    def test_g2_review_status_uses_durable_evidence_rule(self):
        invalid_rows = [
            row["pr_number"]
            for row in self.rows
            if row["g2_review_status"] not in self.metrics.G2_REVIEW_STATUS_VALUES
        ]
        self.assertEqual([], invalid_rows)
        self.assertTrue(any(row["g2_review_status"] == "missing" for row in self.rows))

    def test_summary_is_network_free(self):
        summary = self.metrics.summarize_rows(self.rows)
        self.assertIn("rows: 9", summary)
        self.assertIn("production_behavior_changed=yes: 0", summary)


if __name__ == "__main__":
    unittest.main()
