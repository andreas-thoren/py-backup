from py_backup.sync_utils import rsync

#output = rsync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
completed_process = rsync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])
print(completed_process)