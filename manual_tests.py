from py_backup import rsync, robocopy, folder_backup
from py_backup.syncers import SyncABC, Robocopy, Rsync


# sync("entry.py", "tests/entry.py", ["-a", "--itemize-changes"], {"text": True, "capture_output": True})
# rsync("entry.py", "tests/entry.py", ["rsync", "-a", "--itemize-changes", "entry.py"])


def test_folder_backup():
    folder_backup(
        "tests/folder1/",
        "tests/folder2/",
        delete=False,
        dry_run=True,
        backup="tests/backup_folder/"
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
    #opts = ["-ai","--backup", "--backup-dir=" + backup_dir]
    opts = None
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
    print(Rsync._default_sync_options)
    print(Robocopy._default_sync_options)
    

if __name__ == "__main__":
    #test_filter_args()
    #test_Rsync()
    #test_Robocopy()
    #test_config()
    test_folder_backup()
