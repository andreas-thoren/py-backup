import itertools
import os
import pathlib
import unittest
from copy import deepcopy
from py_backup.comparer import (
    DirComparator,
    FileStatus,
    InfiniteDirTraversalLoopError,
)
from .global_test_vars import SOURCE, DESTINATION, NON_EXISTING_DIR, RESULT_DST_SRC


def dicts_are_equal(dict1: dict, dict2: dict) -> bool:
    for key, val1 in dict1.items():
        val2 = dict2.pop(key, None)

        if val2 is None:
            print(f"Nested dict {val1} has no corresponding dict in dict2")
            return False

        if isinstance(val1, dict) and isinstance(val2, dict):
            nested_dict_is_equal = dicts_are_equal(val1, val2)
            if not nested_dict_is_equal:
                return False
        elif isinstance(val1, set) and isinstance(val2, set):
            sets_equal = sets_are_equal(val1, val2)
            if not sets_equal:
                return False
        else:
            raise ValueError("dict_is_equal can only evaluate dict/set values!")

    if dict2:
        print(
            f"The following keys exist in dict2 that does not in dict1:\n{list(dict2.keys())}"
        )
        return False
    return True


def sets_are_equal(set1: set, set2: set) -> bool:
    set_diff1 = set1 - set2
    set_diff2 = set2 - set1

    if set_diff1:
        print(f"The following items do not exist in set2:\n{set_diff1}")

    if set_diff2:
        print(f"The following items do not exist in set1:\n{set_diff2}")

    return not (set_diff1 or set_diff2)


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

    def test_compare_directories_bilat(self):
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")
        comparer.compare_directories(expand_dirs=True, include_equal_entries=True)
        result = comparer.dir_comparison
        # dicts_are_equal modifies dict. Deepcopy first!
        expected_result = deepcopy(RESULT_DST_SRC)
        self.assertTrue(dicts_are_equal(result, expected_result))

    def test_compare_directories_unilat(self):
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")
        comparer.compare_directories(
            expand_dirs=True, include_equal_entries=True, unilateral_compare=True
        )
        result = comparer.dir_comparison
        # Deepcopy before modifying
        expected_result = deepcopy(RESULT_DST_SRC)
        del expected_result["src"]
        self.assertTrue(dicts_are_equal(result, expected_result))

    def test_compare_with_simple_excludes(self):
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")
        comparer.compare_directories(expand_dirs=True, include_equal_entries=True)
        all_entries_set = set(comparer.get_entries())

        excl = ["*.txt"]
        comparer = DirComparator(
            DESTINATION, SOURCE, dir1_name="dst", dir2_name="src", exclude_patterns=excl
        )
        comparer.compare_directories(expand_dirs=True, include_equal_entries=True)
        filtered_entries_set = set(comparer.get_entries())
        only_textfiles_set = all_entries_set - filtered_entries_set

        self.assertEqual(len(only_textfiles_set), 12)
        for path in only_textfiles_set:
            self.assertEqual(pathlib.Path(path).suffix, ".txt")

    def test_compare_with_leaf_excludes(self):
        # Get all entries without excludes
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src")
        comparer.compare_directories(expand_dirs=True, include_equal_entries=False)
        all_entries_set = set(comparer.get_entries())

        # Test destination leaf exclude
        excl = ["common_dir/common_inner_dir/inner_dst_file.txt"]
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src", exclude_patterns=excl)
        comparer.compare_directories(expand_dirs=True, include_equal_entries=False)
        excl_entries_set = set(comparer.get_entries())
        missing = os.path.join(DESTINATION, "common_dir/common_inner_dir/inner_dst_file.txt")
        set_diff_expected = {missing}
        set_diff_actual = all_entries_set - excl_entries_set
        self.assertEqual(set_diff_actual, set_diff_expected)

        # Test source leaf exclude
        excl = ["common_dir/common_inner_dir/inner_src_file.txt"]
        comparer = DirComparator(DESTINATION, SOURCE, dir1_name="dst", dir2_name="src", exclude_patterns=excl)
        comparer.compare_directories(expand_dirs=True, include_equal_entries=False)
        excl_entries_set = set(comparer.get_entries())
        missing = os.path.join(SOURCE, "common_dir/common_inner_dir/inner_src_file.txt")
        set_diff_expected = {missing}
        set_diff_actual = all_entries_set - excl_entries_set
        self.assertEqual(set_diff_actual, set_diff_expected)
        