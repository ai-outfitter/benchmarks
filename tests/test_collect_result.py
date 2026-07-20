import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collect_result", ROOT / "scripts/collect_result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SessionScanTests(unittest.TestCase):
    def test_counts_assistant_usage_once_and_preserves_response_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            records = [
                {
                    "type": "model_change",
                    "provider": "github-models-legacy",
                    "modelId": "gpt-4.1-mini",
                },
                {
                    "type": "message",
                    "message": {
                        "role": "assistant",
                        "provider": "github-models-legacy",
                        "model": "gpt-4.1-mini",
                        "responseModel": "gpt-4.1-mini-versioned",
                        "usage": {
                            "input": 100,
                            "output": 20,
                            "cacheRead": 50,
                            "cacheWrite": 4,
                            "cost": {"input": 0.001, "total": 0.002},
                        },
                    },
                },
            ]
            (root / "session.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            value = MODULE.scan_sessions(root)

        self.assertEqual(value["models"], ["gpt-4.1-mini"])
        self.assertEqual(value["response_models"], ["gpt-4.1-mini-versioned"])
        self.assertEqual(value["usage"]["input"], 100)
        self.assertEqual(value["usage"]["output"], 20)
        self.assertEqual(value["usage"]["cache_read"], 50)
        self.assertEqual(value["usage"]["cache_write"], 4)
        self.assertEqual(value["usage"]["cost"], 0.002)


if __name__ == "__main__":
    unittest.main()
