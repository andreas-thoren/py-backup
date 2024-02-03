# pylint: skip-file
from py_backup import folder_backup
from py_backup.syncers import SyncABC, Robocopy, Rsync


def test_folder_backup():
    folder_backup(
        "tests/source",
        "tests/destination",
        delete=False,
        dry_run=False,
        backup="tests/backup_folder/",
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
    syncer.sync(delete=True, dry_run=True)


def test_filter_args():
    args3 = ["rsync", "--option1", "rsync", "--option2", "dest", "--option1"]
    filtered3 = SyncABC.filter_args(args3, {"rsync", "dest"})
    assert filtered3 == ["--option1", "--option2", "--option1"]
    print(filtered3)


def test_config():
    print(Rsync._default_sync_options)
    print(Robocopy._default_sync_options)


if __name__ == "__main__":
    # test_filter_args()
    test_Rsync()
    # test_Robocopy()
    # test_config()
    # test_folder_backup()
