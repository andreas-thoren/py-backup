from py_backup.sync_utils import sync

# sync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
sync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])
