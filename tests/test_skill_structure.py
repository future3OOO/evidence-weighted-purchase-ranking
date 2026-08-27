import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "best-buy"
OLD_SKILL_DIR = REPO / "skills" / "evidence-weighted-purchase-ranking"


class SkillStructureTests(unittest.TestCase):
    def test_entry_skill_is_concise_and_routes_to_existing_resources(self) -> None:
        self.assertTrue(SKILL_DIR.is_dir(), "canonical skill directory must be skills/best-buy")
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(skill.splitlines()), 100)
        self.assertLessEqual(len(skill.split()), 400)
        self.assertRegex(skill, r"(?m)^name: best-buy$")
        self.assertRegex(skill, r"(?m)^# Best Buy$")
        self.assertRegex(skill, r"(?m)^description: .+retailers.+marketplaces.+$")
        linked_paths = re.findall(r"\]\(([^)]+)\)", skill)
        required_links = {
            "references/EVIDENCE-AND-IDENTITY.md",
            "references/RETAILER-FIELDS.md",
            "references/RANKING-MODEL.md",
            "references/NZ-AU-PURCHASE-POLICY.md",
            "references/CALIBRATION.md",
            "references/ALIEXPRESS-PARSEBOT.md",
        }
        self.assertLessEqual(required_links, set(linked_paths))
        for linked_path in linked_paths:
            self.assertTrue((SKILL_DIR / linked_path).is_file(), linked_path)
        self.assertIn("one known-count exact consumer review", skill)
        self.assertIn("Products with no usable exact review evidence are unranked", skill)
        self.assertIn("A response fails this skill if its first ranking is ordered by price", skill)

    def test_skill_identity_is_consistently_best_buy(self) -> None:
        self.assertFalse(OLD_SKILL_DIR.exists())
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Best Buy"', metadata)
        self.assertIn("$best-buy", metadata)
        self.assertNotIn("$evidence-weighted-purchase-ranking", metadata)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertRegex(readme, r"(?m)^# Best Buy$")
        self.assertIn("$best-buy", readme)
        self.assertIn("/skills/best-buy", readme)
        self.assertNotIn("/skills/evidence-weighted-purchase-ranking", readme)

    def test_executable_resources_are_present(self) -> None:
        self.assertTrue((SKILL_DIR / "scripts" / "rank.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "model.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "default-policy.json").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "input-template.json").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "aliexpress.py").is_file())


if __name__ == "__main__":
    unittest.main()
