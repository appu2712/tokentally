import unittest
from tokentally.git import profile_git_diff, GitDiffProfiler


class TestGit(unittest.TestCase):
    def test_profile_raw_patch(self):
        sample_patch = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
 def main():
+    print("Added feature")
     return True
"""
        res = profile_git_diff(raw_patch=sample_patch, model="gpt-4o")
        self.assertEqual(res.files_changed, 1)
        self.assertGreater(res.total_tokens, 0)
        self.assertEqual(res.file_breakdown[0].path, "src/app.py")
        self.assertEqual(res.file_breakdown[0].added_lines, 1)


if __name__ == "__main__":
    unittest.main()
