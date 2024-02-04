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

def sync(*args):
    # TODO change this into an actual function
    print(f"sync called with args {args}")

def backup(*args):
    # TODO change this into an actual function
    print(f"backup called with args {args}")
