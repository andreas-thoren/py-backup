# pylint: skip-file
import json
import os
import platform
from py_backup import folder_backup
from py_backup.syncers import Robocopy, Rsync
from py_backup.comparer import DirComparator, FileType, FileStatus

current_os = platform.system()
if current_os == "Linux":
    SOURCE_PATH = "tests/linux_dirs/source"
    DESTINATION_PATH = "tests/linux_dirs/destination"
elif current_os == "Windows":
    SOURCE_PATH = "tests/windows_dirs/source"
    DESTINATION_PATH = "tests/windows_dirs/destination"
else:
    SOURCE_PATH = "tests/non_existing/source"
    DESTINATION_PATH = "tests/non_existing/destination"
    
assert os.path.exists(SOURCE_PATH)
assert os.path.exists(DESTINATION_PATH)


def test_folder_backup():
    folder_backup(
        "tests/source",
        "tests/destination",
        delete=True,
        dry_run=False,
    )


def test_Rsync():
    syncer = Rsync(
        "tests/source",
        "tests/destination",
    )
    backup_dir = "tests/backup_dir"
    opts = ["-aivh"]
    kwargs = {"text": True, "capture_output": True}
    output = syncer.sync(
        delete=True,
        dry_run=False,
        backup=backup_dir,
        options=opts,
        subprocess_kwargs=kwargs,
    )
    print(output.stdout)


def test_Robocopy():
    syncer = Robocopy(
        "tests/source",
        "tests/destination",
    )
    backup_dir = "tests/backup_dir"
    opts = ["-aivh"]
    kwargs = {"text": True, "capture_output": True}
    output = syncer.sync(
        delete=True,
        dry_run=False,
        backup=backup_dir,
        options=opts,
        subprocess_kwargs=kwargs,
    )
    print(output.stdout)


def test_config():
    print(Rsync._default_sync_options)
    print(Robocopy._default_sync_options)


def test_dir_comparator():
    comparator = DirComparator(DESTINATION_PATH, SOURCE_PATH, dir1_name="dst", dir2_name="src")
    comparator.compare_directories(follow_symlinks=False)
    print(comparator.dir_comparison)
    print("\nBefore expand_dirs:".upper())
    print(comparator.get_comparison_result())
    comparator.expand_dirs()
    print("After expand dirs:".upper())
    print(comparator.get_comparison_result())

    # Using dir1 or dst (which were used when createing comparator has the same effect)
    entries = comparator.get_entries(entry_types=[FileType.FILE, FileType.DIR], target_statuses=[FileStatus.UNIQUE, FileStatus.MISMATCHED])
    entries1 = comparator.get_entries(["dst", "mutual"], [FileType.FILE], [FileStatus.UNIQUE, FileStatus.CHANGED])
    entries2 = comparator.get_entries(["dir1", "mutual"], [FileType.FILE], [FileStatus.UNIQUE, FileStatus.CHANGED])
    assert entries1 == entries2
    print("[")
    for entry in entries:
        print(f"    {entry},")
    print("]")
  


if __name__ == "__main__":
    test_dir_comparator()
    # test_Robocopy()
    # test_Rsync()
    # test_config()
