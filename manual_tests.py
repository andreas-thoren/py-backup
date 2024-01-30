from py_backup import rsync, robocopy, folder_backup


# sync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
# rsync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])


def test_rsync_folder_backup():
    folder_backup(
        rsync,
        "tests/folder1/",
        "tests/folder2/",
        backup_dir="tests/backup_dir",
        delete=False,
        dry_run=True,
    )


def test_robocopy_folder_backup():
    folder_backup(
        robocopy,
        "tests/folder1/",
        "tests/folder2/",
        delete=False,
        dry_run=True,
    )


if __name__ == "__main__":
    test_robocopy_folder_backup()
