# pylint: skip-file
from py_backup import folder_backup
from py_backup.syncers import SyncABC, Robocopy, Rsync


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


if __name__ == "__main__":
    test_folder_backup()
    # test_Robocopy()
    # test_Rsync()
    # test_config()
