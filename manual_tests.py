from py_backup.sync_utils import rsync

# sync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
rsync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])
