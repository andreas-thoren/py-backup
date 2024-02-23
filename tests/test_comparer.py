import itertools
import unittest
from py_backup.comparer import (
    DirComparator,
    FileStatus,
    FileType,
    InfiniteDirTraversalLoopError,
)
from .global_test_vars import TEST_DATA_DIR, SOURCE, DESTINATION, NON_EXISTING_DIR


class TestFileStatus(unittest.TestCase):
    def test_file_status_membership(self):
        all_statuses = FileStatus(0)
        for fstatus in FileStatus:
            all_statuses |= fstatus

        for r in range(1, len(FileStatus) + 1):
            for combo in itertools.combinations(FileStatus, r):
                # Build combined status
                fstatus = FileStatus(0)
                for sts in combo:
                    fstatus |= sts

                # Assert status in all_statuses
                assert fstatus in all_statuses


class TestDirComparator(unittest.TestCase):
    def test_init(self):
        # Should be a succesful init
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")

        # dir2 doesnt exist
        with self.assertRaises(ValueError):
            DirComparator(DESTINATION, NON_EXISTING_DIR)

        # dir1 doesnt exist
        with self.assertRaises(ValueError):
            DirComparator(NON_EXISTING_DIR, SOURCE)

        # dir1 == dir2
        with self.assertRaises(ValueError):
            DirComparator(SOURCE, SOURCE)

        # dir1_name == dir2_name
        with self.assertRaises(ValueError):
            DirComparator(DESTINATION, SOURCE, dir1_name="my_dir", dir2_name="my_dir")

    def test_infinite_loop(self):
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")

        with self.assertRaises(InfiniteDirTraversalLoopError):
            comparer.compare_directories(follow_symlinks=True)
