from py_backup import rsync, folder_backup


# sync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
# rsync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])
folder_backup(
    rsync, "tests/folder1/", "tests/folder2/", backup_dir="tests/backup_dir", delete=True, dry_run=False
)
