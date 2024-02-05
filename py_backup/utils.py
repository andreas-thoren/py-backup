"""
Functional interface for py-backup. Works by using the appropriate class in
syncers.py but abstracts this away from the user.
"""

import platform
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
from .syncers import Rsync, Robocopy, SyncABC
from .config import CONFIG, CONFIG_PATH


_INCR_BACKUP_PREFIX = "incremental_backup_"


def folder_backup(
    source: str | Path,
    destination: str | Path,
    delete: bool = False,
    dry_run: bool = False,
    backup_dir: str | Path = "",
    sync_type: str = "defaults",
) -> subprocess.CompletedProcess:
    """
    Performs file synchronization from the source to the destination directory,
    using Rsync or Robocopy depending on the operating system. This function provides
    a simplified interface for file synchronization tasks, abstracting away the direct
    interaction with different syncers.

    Parameters:
    - source (str | Path): The source directory to synchronize from.
    - destination (str | Path): The destination directory where files will be synchronized to.
    - delete (bool, optional): If True, deletes files in the destination that are not
      present in the source. This is useful for mirroring directories. Defaults to False.
    - dry_run (bool, optional): If True, performs a trial run with no actual changes made.
      Useful for testing. Defaults to False.
    - backup_dir (str | Path, optional): Specifies a directory for storing backups of
      files that are overwritten or deleted during the synchronization process.
      Defaults to an empty string, indicating that no backups will be made.
    - sync_type (str, optional): Specifies the type of synchronization to perform, based
      on predefined configurations in config.json. Defaults to "defaults", which uses the
      default synchronization options.

    Returns:
    - subprocess.CompletedProcess: The result from the subprocess call to the sync tool,
      containing information like the exit code and output of the command.

    Raises:
    - NotImplementedError: If the operating system is not supported.
    - ValueError: If the specified sync_type is not found in config.json.

    Example:
    >>> folder_backup('/path/to/source', '/path/to/destination', dry_run=True, sync_type="backup") # doctest: +SKIP
    """
    os_to_syncer_map = {"Linux": Rsync, "Windows": Robocopy}
    os_type = platform.system()

    try:
        syncer = os_to_syncer_map[os_type](source, destination)
    except KeyError as exc:
        raise NotImplementedError(f"Platform {os_type} not supported!") from exc

    try:
        options = CONFIG[sync_type][syncer.__class__.__name__.lower()]
    except KeyError as exc:
        raise ValueError(
            f"There is no sync type {sync_type} in {CONFIG_PATH}\n"
            + f"for {syncer.__name__}!"
        ) from exc

    return syncer.sync(delete, dry_run, backup_dir, options)


def backup(source: str, destination: str, dry_run: bool, backup_dir: str = ""):
    """
    Performs a non-destructive backup from source to destination,
    with optional dry run and backup directory (for overwritten files).
    """
    folder_backup(
        source,
        destination,
        delete=False,
        dry_run=dry_run,
        backup_dir=backup_dir,
        sync_type="backup",
    )


def mirror(source: str, destination: str, dry_run: bool, backup_dir: str = ""):
    """
    Mirrors the source to the destination, deleting extraneous files,
    with optional dry run and backup directory (for overwritten/deleted files).
    """
    folder_backup(
        source,
        destination,
        delete=True,
        dry_run=dry_run,
        backup_dir=backup_dir,
        sync_type="mirror",
    )


def incremental(
    source: str, destination: str, dry_run: bool, backup_dir: str, num_incremental: int
):
    """
    Performs an incremental backup from the source directory to the destination directory,
    while managing the total number of incremental backups to retain. After performing the
    new backup, older backups beyond the specified limit are removed, ensuring efficient
    storage usage.

    Each incremental backup directory will contain files/folders that were overwritten
    or deleted in the corresponding incremental backup.

    Parameters:
    - source (str | Path): The source directory from which files are backed up.
    - destination (str | Path): The destination directory to which files are backed up.
    - dry_run (bool): If True, simulates the backup process and deletion of old backups
      without making any actual changes, providing a summary of actions that would be taken.
    - backup_dir (str | Path): The base directory where incremental backups are stored. Each
      new backup is stored in a subdirectory named with the current timestamp.
    - num_incremental (int): The maximum number of incremental backup directories to retain.
      Older backups beyond this limit are deleted, starting with the oldest.

    Raises (based on potential raised errors in folder_backup call):
    - NotImplementedError: If the operating system is not supported by the underlying sync tools.
    - ValueError: If the 'incremental' keyword is not found in config.json.

    Example:
    >>> incremental('/path/to/source', '/path/to/destination', dry_run=True, backup_dir='/path/to/backups', num_incremental=5)  # doctest: +SKIP
    """
    backup_dir_path = Path(backup_dir)
    nested_dir_path = _get_nested_path(backup_dir_path, datetime.now())

    folder_backup(
        source,
        destination,
        delete=True,
        dry_run=dry_run,
        backup_dir=nested_dir_path,
        sync_type="incremental",
    )

    if nested_dir_path.is_dir():
        for old_backup in _get_old_backups(backup_dir_path, num_incremental):
            if dry_run:
                print(f"Dry run: would delete {old_backup}")
            else:
                shutil.rmtree(old_backup)


def _get_nested_path(backup_path: Path, backup_time: datetime) -> Path:
    """
    Generates a nested directory path for an incremental backup based on the
    backup_path and backup_time.

    Parameters:
    - backup_path (Path): The base dir_path used to genereate directory name.
    - backup_time (datetime): datetime used to generate the directory name.

    Returns:
    - Path: The full path for the new backup directory.

    >>> from datetime import datetime
    >>> backup_time = datetime(2023, 1, 1, 12, 0, 0)
    >>> backup_path = Path("/example/backup")
    >>> _get_nested_path(backup_path, backup_time)
    PosixPath('/example/backup/incremental_backup_230101_120000')
    """
    nested_dir_name = f"{_INCR_BACKUP_PREFIX}{backup_time.strftime('%y%m%d_%H%M%S')}"
    nested_dir = backup_path / nested_dir_name
    return nested_dir


def _get_old_backups(backup_path: Path, num_incremental: int) -> Iterator[Path]:
    """
    Yields paths to old backup directories that should be deleted to maintain
    the specified number of incremental backups.

    Parameters:
    - backup_path (Path): The base path where incremental backups are stored.
    - num_incremental (int): The maximum number of incremental backups to retain.

    Yields:
    - Iterator[Path]: A generator over the paths to the backups that should be deleted.

    >>> from pathlib import Path
    >>> path = Path('tests/backups/incr_backups')
    >>> list(_get_old_backups(path, 4)) # tests directory contains 5 nested dirs.
    [PosixPath('tests/backups/incr_backups/incremental_backup_230102_120000')]
    """
    incremental_backups = sorted(backup_path.glob(f"{_INCR_BACKUP_PREFIX}*"))

    for old_backup in incremental_backups[:-num_incremental]:
        yield old_backup
