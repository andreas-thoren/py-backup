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
    




def rsync(
    source: str,
    destination: str,
    options: list[str] | None = None,
    subprocess_kwargs: dict | None = None,
) -> subprocess.CompletedProcess:
    """Calls rsync(options, source, destination) through subprocess run.

    Args:
        source (str): Source folder/file
        destination (str): Destination folder/file
        options (list): Args list to be passed on to rsync.
        subprocess_kwargs (dict): kwargs passed on to subproccess.run call.

    Returns:
        subprocess.CompletedProcess: returns CompletedProcess instance
        from subprocess.run.
    """
    # TODO create functional interface.
    pass


def robocopy(
    source: str,
    destination: str,
    options: list[str] | None = None,
    subprocess_kwargs: dict | None = None,
) -> subprocess.CompletedProcess:
    # TODO create functional interface
    pass