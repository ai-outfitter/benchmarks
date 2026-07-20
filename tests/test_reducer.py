import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reduce_results", ROOT / "scripts/reduce_results.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def result(cell_id: str, harness: str, status: str):
    return {
        "cell_id": cell_id,
        "variant": {
            "harness": harness,
            "provider": "provider",
            "requested_model": "publisher/model",
        },
        "experiment": {"task_id": "task-001"},
        "execution": {
            "agent_status": "success",
            "runtime": {"pi": "0.80.9"},
            "session": {"response_models": ["resolved-model"]},
        },
        "outcome": {
            "status": status,
            "failure_class": "none" if status == "pass" else "benchmark",
        },
    }


class ReducerTests(unittest.TestCase):
    def test_invalid_cells_are_excluded_from_pass_rate(self):
        summary = MODULE.summarize(
            [
                result("a", "base-pi", "pass"),
                result("b", "base-pi", "fail"),
                result("c", "base-pi", "invalid"),
            ]
        )
        base = summary["variants"]["base-pi"]
        self.assertEqual(base["total"], 3)
        self.assertEqual(base["valid"], 2)
        self.assertEqual(base["invalid"], 1)
        self.assertEqual(base["pass_rate"], 0.5)

    def test_markdown_preserves_claim_boundary(self):
        report = MODULE.markdown(MODULE.summarize([result("a", "outfitter-pi", "pass")]))
        self.assertIn("does **not** establish", report)
        self.assertIn("outfitter-pi", report)

    def test_expected_cells_and_runtime_parity_are_enforced(self):
        values = [
            result("outfitter-pi-task-001-r1", "outfitter-pi", "pass"),
            result("base-pi-task-001-r1", "base-pi", "pass"),
        ]
        MODULE.validate_comparison(
            values,
            {"outfitter-pi-task-001-r1", "base-pi-task-001-r1"},
            True,
        )
        values[1]["execution"]["runtime"]["pi"] = "different"
        with self.assertRaisesRegex(ValueError, "Pi runtime mismatch"):
            MODULE.validate_comparison(values, set(), True)


if __name__ == "__main__":
    unittest.main()
