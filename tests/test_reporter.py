import unittest
from tokentally.reporter import generate_report, AuditReporter


class TestReporter(unittest.TestCase):
    def test_generate_markdown_report(self):
        rep = generate_report("Hello prompt testing report generation", output_format="markdown", model="gpt-4o")
        self.assertIn("TokenTally Audit Report", rep)
        self.assertIn("Cross-Model Cost Matrix", rep)
        self.assertIn("gpt-4o", rep)

    def test_generate_csv_report(self):
        csv_rep = generate_report("Hello prompt testing csv report", output_format="csv")
        self.assertIn("model,provider,input_tokens", csv_rep)
        self.assertIn("gpt-4o", csv_rep)


if __name__ == "__main__":
    unittest.main()
