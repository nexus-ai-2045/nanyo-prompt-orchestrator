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

    def test_failed_fetch_keeps_the_previous_corpus_record(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base, prompt_ids=("1", "2"))
            self._patch_mirror_url()
            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)
            before = self._corpus(base)
            self._patch_mirror_url(failing_ids={"2"}, body="refreshed prompt")

            summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            after = self._corpus(base)
            self.assertEqual([record["prompt_id"] for record in after], [1, 2])
            self.assertIn("refreshed prompt", str(after[0]["prompt_text"]))
            self.assertNotEqual(after[0], before[0])
            self.assertEqual(after[1], before[1])
            self.assertEqual(summary["error_count"], 1)
            self.assertEqual(summary["retained_previous_count"], 1)

    def test_fully_failed_refresh_leaves_the_corpus_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base, prompt_ids=("1", "2"))
            self._patch_mirror_url()
            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)
            before = (base / "prompt-bodies.jsonl").read_bytes()
            self._patch_mirror_url(failing_ids={"1", "2"})

            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            self.assertEqual((base / "prompt-bodies.jsonl").read_bytes(), before)

    def test_interrupted_refresh_leaves_the_corpus_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base, prompt_ids=("1", "2"))
            self._patch_mirror_url()
            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)
            before = (base / "prompt-bodies.jsonl").read_bytes()

            def interrupted(row: dict[str, str], timeout: int) -> tuple[str, str, str | None]:
                raise KeyboardInterrupt

            nanyo_prompt_mirror.mirror_url = interrupted

            with self.assertRaises(KeyboardInterrupt):
                nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            self.assertEqual((base / "prompt-bodies.jsonl").read_bytes(), before)
            self.assertEqual(sorted(path.name for path in base.glob("prompt-bodies*")), ["prompt-bodies.jsonl"])

    def test_failed_fetch_without_a_previous_record_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base, prompt_ids=("1", "2"))
            self._patch_mirror_url(failing_ids={"2"})

            summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            self.assertEqual([record["prompt_id"] for record in self._corpus(base)], [1])
            self.assertEqual(summary["retained_previous_count"], 0)

    def test_previous_corpus_with_invalid_bytes_does_not_stop_the_refresh(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base)
            (base / "prompt-bodies.jsonl").write_bytes(b'{"prompt_id": 1, "title": "\xe3\x81"}\n')
            self._patch_mirror_url()

            summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

            self.assertEqual(summary["mirrored_count"], 1)
            self.assertEqual([record["prompt_id"] for record in self._corpus(base)], [1])

    def test_failed_fetch_keeps_a_previous_record_containing_unicode_line_separators(self) -> None:
        for separator in (chr(0x2028), chr(0x2029), chr(0x85)):
            with self.subTest(separator=repr(separator)), TemporaryDirectory() as tmp:
                base = Path(tmp)
                self._write_inventory(base, title=f"fix{separator}ture")
                self._patch_mirror_url()
                nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)
                before = (base / "prompt-bodies.jsonl").read_bytes()
                self._patch_mirror_url(failing_ids={"1"})

                summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)

                self.assertEqual((base / "prompt-bodies.jsonl").read_bytes(), before)
                self.assertEqual(summary["retained_previous_count"], 1)

    def test_limit_keeps_previous_records_beyond_the_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_inventory(base, prompt_ids=("1", "2", "3"))
            self._patch_mirror_url()
            nanyo_prompt_mirror.mirror(base, delay=0, limit=None, timeout=1)
            before = self._corpus(base)
            self._patch_mirror_url(body="refreshed prompt")

            summary = nanyo_prompt_mirror.mirror(base, delay=0, limit=1, timeout=1)

            after = self._corpus(base)
            self.assertEqual([record["prompt_id"] for record in after], [1, 2, 3])
            self.assertIn("refreshed prompt", str(after[0]["prompt_text"]))
            self.assertEqual(after[1:], before[1:])
            self.assertEqual(summary["retained_previous_count"], 2)

    def _corpus(self, base: Path) -> list[dict[str, object]]:
        lines = (base / "prompt-bodies.jsonl").read_text(encoding="utf-8").split("\n")
        return [json.loads(line) for line in lines if line]

    def _write_inventory(self, base: Path, prompt_ids: tuple[str, ...] = ("1",), title: str = "fixture") -> None:
        with (base / "inventory-unique.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["prompt_id", "title", "source_category", "prompt_url"],
            )
            writer.writeheader()
            for prompt_id in prompt_ids:
                writer.writerow(
                    {
                        "prompt_id": prompt_id,
                        "title": title,
                        "source_category": "fixture-category",
                        "prompt_url": f"https://example.invalid/prompt/{prompt_id}",
                    }
                )

    def _patch_mirror_url(self, failing_ids: frozenset[str] | set[str] = frozenset(), body: str = "fixture prompt") -> None:
        def fake(row: dict[str, str], timeout: int) -> tuple[str, str, str | None]:
            if row["prompt_id"] in failing_ids:
                return row["prompt_url"], "", "timed out"
            return row["prompt_url"], f"<html><title>fixture</title><textarea>{body}</textarea></html>", None

        nanyo_prompt_mirror.mirror_url = fake


if __name__ == "__main__":
    unittest.main()
