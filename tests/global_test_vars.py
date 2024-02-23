import platform
from pathlib import Path
from py_backup.comparer import FileStatus, FileType

user_platform = platform.system().lower()
if user_platform == "linux":
    TEST_DATA_DIR = Path(__file__).parent / "linux_dirs"
elif user_platform == "windows":
    TEST_DATA_DIR = Path(__file__).parent / "windows_dirs"
else:
    raise NotImplementedError("Platforms other then windows/linux not implemented")

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
                str(Path("delete_file.txt")),
                str(Path("common_dir/dst_file.txt")),
                str(Path("common_dir/common_inner_dir/inner_dst_file.txt")),
                str(Path("inner_dst_dir/inner_dst_file")),
                str(Path("inner_dst_dir/nested_inner_dst_dir/nested_inner_dst_file")),
                str(Path("src_file_dst_dir/.keep")),
            },
            FileStatus.MISMATCHED: {str(Path("src_dir_dst_file"))},
        },
        FileType.DIR: {
            FileStatus.UNIQUE: {str(Path("inner_dst_dir")), str(Path("inner_dst_dir/nested_inner_dst_dir"))},
            FileStatus.MISMATCHED: {str(Path("src_file_dst_dir"))},
        },
    },
    "src": {
        FileType.FILE: {
            FileStatus.UNIQUE: {
                str(Path("nested_src_dir/nested_src_file.txt")),
                str(Path("src_dir_dst_file/.keep")),
                str(Path("common_dir/source_file.txt")),
                str(Path("common_dir/common_inner_dir/inner_src_file.txt")),
            },
            FileStatus.MISMATCHED: {str(Path("src_file_dst_dir"))},
        },
        FileType.DIR: {
            FileStatus.UNIQUE: {str(Path("nested_src_dir"))},
            FileStatus.MISMATCHED: {str(Path("src_dir_dst_file"))},
        },
    },
    "mutual": {
        FileType.FILE: {
            FileStatus.CHANGED: {str(Path("testfile1.txt"))},
            FileStatus.EQUAL: {
                str(Path("equal_file.txt")),
                str(Path("common_dir/common_inner_dir/common_inner_file.txt")),
            },
        },
        FileType.DIR: {
            FileStatus.NOT_COMPARED: {str(Path("common_dir")), str(Path("common_dir/common_inner_dir"))},
        },
        FileType.SYMLINK: {
            FileStatus.NOT_COMPARED: {
                str(Path("common_dir/loop_link")),
                str(Path("common_dir/loop_link_windows")),
            }
        },
    },
}
