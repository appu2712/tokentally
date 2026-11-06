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

    def test_lockfile_classification_and_density(self):
        sample_patch = """diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,3 +1,5 @@
+"version": "1.2.3"
+"lockfileVersion": 3
diff --git a/src/logic.py b/src/logic.py
--- a/src/logic.py
+++ b/src/logic.py
@@ -1,2 +1,3 @@
+def execute(): pass
"""
        res = profile_git_diff(raw_patch=sample_patch, model="gpt-4o")
        self.assertEqual(res.files_changed, 2)
        categories = {f.path: f.category for f in res.file_breakdown}
        self.assertEqual(categories["package-lock.json"], "lockfile")
        self.assertEqual(categories["src/logic.py"], "human_code")
        self.assertLess(res.review_value_density, 1.0)
        self.assertGreater(res.generated_tokens, 0)


if __name__ == "__main__":
    unittest.main()
