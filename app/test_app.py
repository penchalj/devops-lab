import unittest

from app import health


class HealthTest(unittest.TestCase):
    def test_status_ok(self):
        self.assertEqual(health()["status"], "ok")

    def test_has_version(self):
        self.assertIn("version", health())


if __name__ == "__main__":
    unittest.main()
