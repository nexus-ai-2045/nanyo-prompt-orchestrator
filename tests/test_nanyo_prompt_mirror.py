import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "nanyo_prompt_mirror.py"
SPEC = importlib.util.spec_from_file_location("nanyo_prompt_mirror", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
nanyo_prompt_mirror = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = nanyo_prompt_mirror
SPEC.loader.exec_module(nanyo_prompt_mirror)


class MirrorOutputShapeTest(unittest.TestCase):
    def test_default_json_excludes_raw_html_but_keeps_checksum_and_prompt_text(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base)
            self._patch_mirror_url()

            summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            record = json.loads((base / "prompts" / "001.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["mirrored_count"], 1)
            self.assertNotIn("raw_html", record)
            self.assertIn("raw_html_sha256", record)
            self.assertIn("prompt_text", record)
            self.assertIn("fixture prompt", record["prompt_text"])

    def test_raw_html_dir_writes_unembedded_cache(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw_dir = base / "raw-html"
            self._write_inventory(base)
            self._patch_mirror_url()

            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1, raw_html_dir=raw_dir)

            record = json.loads((base / "prompts" / "001.json").read_text(encoding="utf-8"))
            self.assertNotIn("raw_html", record)
            self.assertIn("fixture prompt", (raw_dir / "001.html").read_text(encoding="utf-8"))

    def _write_inventory(self, base: Path) -> None:
        with (base / "inventory-unique.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["prompt_id", "title", "source_category", "prompt_url"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "prompt_id": "1",
                    "title": "fixture",
                    "source_category": "fixture-category",
                    "prompt_url": "https://example.invalid/prompt/1",
                }
            )

    def _patch_mirror_url(self) -> None:
        nanyo_prompt_mirror.mirror_url = lambda row, timeout: (
            row["prompt_url"],
            "<html><title>fixture</title><textarea>fixture prompt</textarea></html>",
            None,
        )


if __name__ == "__main__":
    unittest.main()
