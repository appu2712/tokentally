import os
import tempfile
import unittest
from pathlib import Path

from tokentally.packer import pack_repository, RepositoryPacker


class TestPacker(unittest.TestCase):
    def test_pack_repository(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create test files
            (tmp_path / "main.py").write_text("print('hello world')", encoding="utf-8")
            (tmp_path / "utils.py").write_text("def add(x, y): return x + y", encoding="utf-8")

            # Ignored dir
            (tmp_path / ".git").mkdir()
            (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")

            # Ignored binary
            (tmp_path / "test.png").write_bytes(b"\x89PNG\r\n\x1a\n")

            res = pack_repository(tmpdir, format_type="xml")
            self.assertEqual(res.total_files, 2)
            self.assertGreater(res.total_tokens, 0)
            self.assertIn('<file path="main.py">', res.packed_content)
            self.assertIn('<file path="utils.py">', res.packed_content)
            self.assertNotIn("HEAD", res.packed_content)
            self.assertNotIn("test.png", res.packed_content)

    def test_pack_with_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "app.py").write_text("import os", encoding="utf-8")
            out_file = str(tmp_path / "packed.xml")

            res = pack_repository(tmpdir, output_file=out_file)
            self.assertTrue(os.path.isfile(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, res.packed_content)


if __name__ == "__main__":
    unittest.main()
