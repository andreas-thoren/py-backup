"""The core functions exposed directly in py_backup"""
import subprocess
from pathlib import Path
from typing import Callable


def folder_backup(
    backup_func: Callable[
        [str, str, list[str] | None, dict | None], subprocess.CompletedProcess
    ],
    source: str | Path,
    destination: str | Path,
    backup_dir: str | Path = "",
    delete: bool = False,
    dry_run: bool = False,
) -> subprocess.CompletedProcess:
    """
    Purpose of this function is to provide a higer level interface to
    rsync/robocopy functions where default options are provided. In the case of robocopy
    it also extends its functionality so that you can backup files to be
    deleted/overwritten to a specified dir. rsync provides this functionality natively
    so if backup_dir is provided it just enables the necessary flags for this to work.

    Args:
        backup_func (callable): The callable this function uses to perform the folder backup.
            Currently only rsync is supported.
        source (str | Path): Existing folder path
        destination (str | Path): Existing folder path
        backup_dir (str | Path, optional): Folder path where
            overwritten/deleted files should be backed up
        delete (bool, optional): Wether to delete files not existing in source
            in destination. Defaults to False.
        dry_run (bool, optional): Only test what would happen.
            Does not perform any actual actions. Defaults to False.

    Raises:
        ValueError: If source or destination does not point to existing dirs.
        NotImplementedError: If using backup_func not working with this function.
    """
    # TODO create function that creates appropriate syncer depending
    # on user platform.
    pass


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