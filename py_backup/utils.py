from pathlib import Path
from .global_vars import default_options


def get_default_args(
    func_name: str,
    source: Path,
    destination: Path,
    backup_dir: Path | None,
    delete: bool = False,
    dry_run: bool = False,
) -> tuple[str, str, list[str] | None, dict | None]:
    function_map = {
        "rsync": get_rsync_defaults,
        "robocopy": get_robocopy_defaults,
    }

    # 1. Choose the appropriate default generating funtion.
    default_func = function_map.get(func_name, get_generic_func_defaults)
    return default_func(source, destination, backup_dir, delete, dry_run)


def get_generic_func_defaults(
    source: Path,
    destination: Path,
    backup_dir: Path | None,
    delete: bool = False,
    dry_run: bool = False,
) -> tuple[str, str, list[str] | None, dict | None]:
    return (str(source), str(destination), [], {})


def get_rsync_defaults(
    source: Path,
    destination: Path,
    backup_dir: Path | None,
    delete: bool = False,
    dry_run: bool = False,
) -> tuple[str, str, list[str] | None, dict | None]:
    # Trailing slashes are importent in rsync call for consistent behaviour
    src_string = str(source) + "/"
    dst_string = str(destination) + "/"
    opts = default_options["rsync"].copy()

    if delete:
        opts.append("--delete")
    if dry_run:
        opts.append("--dry-run")
    if backup_dir:
        opts.append("--backup")
        opts.append("--backup-dir=" + str(backup_dir))

    return (src_string, dst_string, opts, {})


def get_robocopy_defaults(
    source: Path,
    destination: Path,
    backup_dir: Path | None,
    delete: bool = False,
    dry_run: bool = False,
) -> tuple[str, str, list[str] | None, dict | None]:
    src_string = str(source)
    dst_string = str(destination)
    opts = default_options["robocopy"].copy()

    if delete:
        opts.append("/PURGE")
    if dry_run:
        opts.append("/L")
    if backup_dir:
        opts.append("/BACKUP:" + str(backup_dir))

    return (src_string, dst_string, opts, {})


def get_filtered_args(args: list, unwanted_args: set | None = None) -> list:
    """Short function to remove duplicate args and remove unwanted_args while
    maintaining args list order (if duplicate first position is kept).

    Args:
        args (list): Unfiltered args list
        unwanted_args (set): Set of unwanted args to remove. Defaults to None if not provided.

    Returns:
        list: deduplicated list without unwanted args with initial order intact
    """
    excl = unwanted_args if unwanted_args else set()
    filtered_args_dict = {key: None for key in args if key not in excl}
    return list(filtered_args_dict)


def sanitize_subprocess_kwargs(kwargs: dict | None) -> dict:
    """Sanitize the subprocess keyword arguments."""
    kwargs.pop("shell", None)
    return kwargs
