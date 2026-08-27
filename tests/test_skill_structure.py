import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "evidence-weighted-purchase-ranking"


class SkillStructureTests(unittest.TestCase):
    def test_entry_skill_is_concise_and_routes_to_existing_resources(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(skill.splitlines()), 100)
        self.assertRegex(skill, r"(?m)^name: evidence-weighted-purchase-ranking$")
        self.assertRegex(skill, r"(?m)^description: .+retailers.+marketplaces.+$")
        linked_paths = re.findall(r"\]\(([^)]+)\)", skill)
        self.assertGreaterEqual(len(linked_paths), 5)
        for linked_path in linked_paths:
            self.assertTrue((SKILL_DIR / linked_path).is_file(), linked_path)

    def test_executable_resources_are_present(self) -> None:
        self.assertTrue((SKILL_DIR / "scripts" / "rank.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "model.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "default-policy.json").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "input-template.json").is_file())


if __name__ == "__main__":
    unittest.main()
