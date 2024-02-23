from pathlib import Path
from py_backup.comparer import FileStatus, FileType

TEST_DATA_DIR = Path(__file__).parent / "test_dirs"
assert TEST_DATA_DIR.is_dir()

DESTINATION = TEST_DATA_DIR / "destination"
SOURCE = TEST_DATA_DIR / "source"
NON_EXISTING_DIR = TEST_DATA_DIR / "not_exist_dir"
assert DESTINATION.is_dir()
assert SOURCE.is_dir()
assert not NON_EXISTING_DIR.exists()

RESULT_DST_SRC = {
    "dst": {
        FileType.FILE: {
            FileStatus.UNIQUE: {
                "delete_file.txt",
                "common_dir/dst_file.txt",
                "common_dir/common_inner_dir/inner_dst_file.txt",
                "inner_dst_dir/inner_dst_file",
                "inner_dst_dir/nested_inner_dst_dir/nested_inner_dst_file",
                "src_file_dst_dir/.keep",
            },
            FileStatus.MISMATCHED: {"src_dir_dst_file"},
        },
        FileType.DIR: {
            FileStatus.UNIQUE: {"inner_dst_dir", "inner_dst_dir/nested_inner_dst_dir"},
            FileStatus.MISMATCHED: {"src_file_dst_dir"},
        },
    },
    "src": {
        FileType.FILE: {
            FileStatus.UNIQUE: {
                "nested_src_dir/nested_src_file.txt",
                "src_dir_dst_file/.keep",
                "common_dir/source_file.txt",
                "common_dir/common_inner_dir/inner_src_file.txt",
            },
            FileStatus.MISMATCHED: {"src_file_dst_dir"},
        },
        FileType.DIR: {
            FileStatus.UNIQUE: {"nested_src_dir"},
            FileStatus.MISMATCHED: {"src_dir_dst_file"},
        },
    },
    "mutual": {
        FileType.FILE: {
            FileStatus.CHANGED: {"testfile1.txt"},
            FileStatus.EQUAL: {
                "equal_file.txt",
                "common_dir/common_inner_dir/common_inner_file.txt",
            },
        },
        FileType.DIR: {
            FileStatus.NOT_COMPARED: {"common_dir", "common_dir/common_inner_dir"},
        },
        FileType.SYMLINK: {
            FileStatus.NOT_COMPARED: {
                "common_dir/loop_link",
                "common_dir/loop_link_windows",
            }
        },
    },
}
