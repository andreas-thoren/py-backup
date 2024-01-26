from py_backup.utils import rsync

output = rsync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"])
print(output.stdout)