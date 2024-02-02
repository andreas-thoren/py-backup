"""The core functions exposed directly in py_backup"""
import subprocess
import platform
from pathlib import Path
from .syncers import Rsync, Robocopy


def folder_backup(
    source: str | Path,
    destination: str | Path,
    delete: bool = False,
    dry_run: bool = False,
    backup: str | Path = "",
) -> subprocess.CompletedProcess:

    os_to_function_map = {
        "Linux": rsync,
        "Windows": robocopy
    }
    os_type = platform.system()
    
    try:
        sync_func = os_to_function_map[os_type] 
    except KeyError:
        raise NotImplementedError(f"Platform {os_type} not supported!")
    
    sync_func(source, destination, delete, dry_run, backup)

def rsync(
    source: str | Path,
    destination: str | Path,
    delete: bool = False,
    dry_run: bool = False,
    backup: str = "",
    options: list[str] | None = None,
    subprocess_kwargs: dict | None = None,
) -> subprocess.CompletedProcess:

    syncer = Rsync(source, destination)
    return syncer.sync(delete, dry_run, backup, options, subprocess_kwargs)


def robocopy(
    source: str | Path,
    destination: str | Path,
    delete: bool = False,
    dry_run: bool = False,
    backup: str = "",
    options: list[str] | None = None,
    subprocess_kwargs: dict | None = None,
) -> subprocess.CompletedProcess:

    syncer = Robocopy(source, destination)
    return syncer.sync(delete, dry_run, backup, options, subprocess_kwargs)