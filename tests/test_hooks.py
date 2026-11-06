import tempfile
import unittest
from pathlib import Path

from tokentally.hooks import scaffold_github_workflow, install_git_precommit_hook


class TestHooks(unittest.TestCase):
    def test_scaffold_github_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wf_path = scaffold_github_workflow(tmpdir)
            self.assertTrue(wf_path.is_file())
            content = wf_path.read_text(encoding="utf-8")
            self.assertIn("AI Token & Budget Gate", content)

    def test_install_git_precommit_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_hooks = Path(tmpdir) / ".git" / "hooks"
            git_hooks.mkdir(parents=True)
            hook_file = install_git_precommit_hook(tmpdir)
            self.assertTrue(hook_file.is_file())
            content = hook_file.read_text(encoding="utf-8")
            self.assertIn("tokentally diff", content)


if __name__ == "__main__":
    unittest.main()
