import unittest
from py_backup.syncers import SyncABC


class TestUtils(unittest.TestCase):
    def test_filter_args(self):
        filter_args = SyncABC.filter_args
        args = ["--option1", "--option2", "--unwanted"]
        filtered = filter_args(args, {"--unwanted"})
        self.assertEqual(filtered, ["--option1", "--option2"])

        args2 = ["--option1", "--option2", "--option1"]
        filtered2 = filter_args(args2, {"--unwanted"}, False)
        self.assertEqual(filtered2, ["--option1", "--option2"])

        args3 = ["rsync", "--option1", "rsync", "--option2", "dest", "--option1"]
        filtered3 = filter_args(args3, {"rsync", "dest"})
        self.assertEqual(filtered3, ["--option1", "--option2", "--option1"])
