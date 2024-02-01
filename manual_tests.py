from py_backup import rsync, robocopy, folder_backup
from py_backup.syncers import SyncABC, Robocopy, Rsync
from py_backup.config import ROBOCOPY_DEFAULTS, RSYNC_DEFAULTS


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
    
def test_Rsync():
    syncer = Rsync(
        "tests/folder1/",
        "tests/folder2/",
    )
    backup_dir = "tests/backup_dir"
    opts = ["-ai","--backup", "--backup-dir=" + backup_dir]
    syncer.sync(delete=False, dry_run=False, backup=backup_dir, options=opts)

def test_Robocopy():
    syncer = Robocopy(
        "tests/folder1/",
        "tests/folder2/",
    )
    syncer.sync(delete=True, dry_run=True)

def test_filter_args():
    args3 = ["rsync", "--option1", "rsync", "--option2", "dest", "--option1"]
    filtered3 = SyncABC.filter_args(args3, {"rsync", "dest"})
    assert filtered3 == ["--option1", "--option2", "--option1"]

def test_config():
    print(ROBOCOPY_DEFAULTS)
    print(RSYNC_DEFAULTS)
    

if __name__ == "__main__":
    #test_filter_args()
    #test_Rsync()
    #test_Robocopy()
    test_config()
