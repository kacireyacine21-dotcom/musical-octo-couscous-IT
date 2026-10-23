import unittest
from pathlib import Path


class OpenAIConfigTestCase(unittest.TestCase):
    def test_openai_env_var_exists(self):
        env_file = Path(__file__).resolve().parents[1] / ".env"
        text = env_file.read_text(encoding="utf-8")
        self.assertIn("OPENAI_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
