import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "nanyo_prompt_router.py"
SPEC = importlib.util.spec_from_file_location("nanyo_prompt_router", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
nanyo_prompt_router = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = nanyo_prompt_router
SPEC.loader.exec_module(nanyo_prompt_router)


class PromptRouterTest(unittest.TestCase):
    def test_search_prioritizes_title_and_text_matches(self) -> None:
        records = [
            self._record(1, "議事録を要約する", "文章作成・要約", "議事録 要約 会議"),
            self._record(2, "画像を説明する", "画像", "写真を説明"),
        ]

        hits = nanyo_prompt_router.search_prompts(records, "議事録 要約", limit=3)

        self.assertEqual([hit.record.prompt_id for hit in hits], [1])
        self.assertGreater(hits[0].score, 0)

    def test_build_packet_preserves_source_metadata_and_target_instruction(self) -> None:
        hit = nanyo_prompt_router.SearchHit(
            score=7,
            record=self._record(370, "プロンプトを探す", "情報収集・分析", "目的から候補を探す"),
        )

        packet = nanyo_prompt_router.build_packet([hit], "候補 抽出", "subagent", max_chars=20)

        self.assertEqual(packet["selected_count"], 1)
        self.assertEqual(packet["source"]["ssot"], "data/prompts/*.json")
        self.assertIn("sub-agent packet", packet["orchestration"]["target_instruction"])
        self.assertEqual(packet["prompts"][0]["prompt_id"], 370)
        self.assertIn("source_url", packet["prompts"][0])

    def test_cli_outputs_json_packet(self) -> None:
        with TemporaryDirectory() as tmp:
            prompts_dir = Path(tmp)
            self._write_prompt(prompts_dir, 1, "議事録を要約する", "文章作成・要約", "議事録 要約")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "議事録",
                    "--prompts-dir",
                    str(prompts_dir),
                    "--target",
                    "pdca",
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            packet = json.loads(result.stdout)
            self.assertEqual(packet["target"], "pdca")
            self.assertEqual(packet["prompts"][0]["prompt_id"], 1)

    def _record(self, prompt_id: int, title: str, category: str, text: str):
        return nanyo_prompt_router.PromptRecord(
            prompt_id=prompt_id,
            title=title,
            source_category=category,
            source_url=f"https://example.invalid/source/{prompt_id}",
            retrieved_url=f"https://example.invalid/{prompt_id}.html",
            raw_html_sha256="a" * 64,
            prompt_text=text,
        )

    def _write_prompt(self, prompts_dir: Path, prompt_id: int, title: str, category: str, text: str) -> None:
        prompts_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "prompt_id": prompt_id,
            "title": title,
            "source_category": category,
            "source_url": f"https://example.invalid/source/{prompt_id}",
            "retrieved_url": f"https://example.invalid/{prompt_id}.html",
            "raw_html_sha256": "a" * 64,
            "prompt_text": text,
        }
        (prompts_dir / f"{prompt_id:03d}.json").write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
