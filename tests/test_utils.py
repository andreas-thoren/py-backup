import unittest
from py_backup.utils import get_filtered_args


class TestUtils(unittest.TestCase):
    def test_get_filtered_args(self):
        args = ["--option1", "--option2", "--unwanted"]
        filtered = get_filtered_args(args, {"--unwanted"})
        self.assertEqual(filtered, ["--option1", "--option2"])

        args2 = ["--option1", "--option2", "--option1"]
        filtered2 = get_filtered_args(args2, {"--unwanted"})
        self.assertEqual(filtered2, ["--option1", "--option2"])
