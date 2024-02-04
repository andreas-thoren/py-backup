"""
Functional interface for py-backup. Works by using the appropriate class in
syncers.py but abstracts this away from the user.
"""

import subprocess
import platform
from pathlib import Path
from .syncers import Rsync, Robocopy, SyncABC
from .config import CONFIG, CONFIG_PATH


def folder_backup(
    source: str | Path,
    destination: str | Path,
    delete: bool = False,
    dry_run: bool = False,
    backup_dir: str | Path = "",
    sync_type: str = "defaults",
    sync_class: SyncABC | None = None,
) -> subprocess.CompletedProcess:
    os_to_syncer_map = {"Linux": Rsync, "Windows": Robocopy}
    os_type = platform.system()

    if sync_class is None:
        try:
            syncer = os_to_syncer_map[os_type](source, destination)
        except KeyError as exc:
            raise NotImplementedError(f"Platform {os_type} not supported!") from exc
    else:
        syncer = sync_class(source, destination)

    try:
        options = CONFIG[sync_type][syncer.__class__.__name__.lower()]
    except KeyError as exc:
        raise ValueError(
            f"There is no sync type {sync_type} in {CONFIG_PATH}\n"
            + f"for {syncer.__name__}!"
        ) from exc

    return syncer.sync(delete, dry_run, backup_dir, options)


def backup(source: str, destination: str, dry_run: bool, backup_dir: str = ""):
    # TODO change this into an actual function
    print(
        f"backup called with args source={source}, destination={destination}, "
        + f"backup_dir={backup_dir}, dry_run={dry_run}"
    )


def mirror(source: str, destination: str, dry_run: bool, backup_dir: str = ""):
    # TODO change this into an actual function
    print(
        f"mirror called with args source={source}, destination={destination}, "
        + f"backup_dir={backup_dir}, dry_run={dry_run}"
    )


def incremental(
    source: str, destination: str, dry_run: bool , backup_dir: str, num_incremental: int
):
    # TODO change this into an actual function
    print(
        f"incremental called with args source={source}, destination={destination}, "
        + f"backup_dir={backup_dir}, num_incremental={num_incremental}, dry_run={dry_run}"
    )
