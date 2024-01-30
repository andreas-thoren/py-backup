"""The core functions exposed directly in py_backup"""
import subprocess
from pathlib import Path
from .utils import get_filtered_args, sanitize_subprocess_kwargs
from .global_vars import default_options


def folder_backup(
    backup_func: callable,
    source: str | Path,
    destination: str | Path,
    backup_dir: str | Path = "",
    delete: bool = False,
    dry_run: bool = False,
) -> None:
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

    # Make sure that source and destination are specified since Path("") -> Path(".")
    # I want user to have to specify dir!
    if not (source and destination):
        raise ValueError("You need to specify source and destination!")

    # Make sure all dirs are converted to Paths if not already
    source = Path(source) if isinstance(source, str) else source
    destination = Path(destination) if isinstance(destination, str) else destination
    source = source.resolve()
    destination = destination.resolve()

    # Convert backup_dir to a Path object if it's a non-empty string. Resolve path.
    if not backup_dir:
        backup_dir = None
    elif isinstance(backup_dir, str):
        backup_dir = Path(backup_dir).resolve()
    else:  # backup_dir is Path. Resolve it
        backup_dir = backup_dir.resolve()

    # Checks if paths are valid dir paths!
    if not source.is_dir():
        raise ValueError(f"{str(source)} is not the path to an existing dir")
    if not destination.is_dir():
        raise ValueError(f"{str(destination)} is not the path to an existing dir")

    func_name = backup_func.__name__

    # Call the actual syncing functions below.
    if func_name == "rsync":
        options = _get_rsync_options(backup_dir, delete, dry_run)
        # Important for subsequent rsync call that folder paths ends with "/"
        src_string = str(source) + "/"
        dst_string = str(destination) + "/"
        rsync(src_string, dst_string, options)
    elif func_name == "robocopy":
        # TODO implement functionality in _robocopy_backup.
        raise NotImplementedError(
            "robocopy will be implemented in the future but not now..."
        )
    else:
        raise NotImplementedError(f"{func_name} is not a valid backup_function")


def _get_rsync_options(
    backup_dir: Path | None,
    delete: bool = False,
    dry_run: bool = False,
):
    opts = default_options.get("rsync", []).copy()
    if delete:
        opts.append("--delete")
    if dry_run:
        opts.append("--dry-run")
    if backup_dir:
        opts.append("--backup")
        opts.append("--backup-dir=" + str(backup_dir))
    return opts


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

    # Create/filter args list to pass to subprocess.run
    args = options.copy() if options else []
    args = get_filtered_args(args, {"rsync", source, destination})
    args = ["rsync"] + args + [source, destination]

    # Ensure kwargs is dict if rsync is called directly
    kwargs = subprocess_kwargs.copy() if subprocess_kwargs else {}
    sanitized_subprocess_kwargs = sanitize_subprocess_kwargs(kwargs)

    try:
        completed_process = subprocess.run(args, **sanitized_subprocess_kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(
            "rsync does not seem to be installed on your system (or path is not set)!\n"
            + "Install rsync or fix path for program to work."
        )

    return completed_process


def robocopy(
    source: str,
    destination: str,
    options: list[str] | None = None,
    subprocess_kwargs: dict | None = None,
) -> None:

    # TODO
    pass
