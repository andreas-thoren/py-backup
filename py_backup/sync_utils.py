"""Contains utility functions used by core.py"""
import platform
import subprocess


def sync(
    source: str,
    destination: str,
    options: list | None = None,
    backup: bool = False,
    backup_dir: str = "",
    subprocess_kwargs: dict | None = None,
) -> None:

    sanitized_subprocess_kwargs = sanitize_subprocess_kwargs(subprocess_kwargs)
    system_platform = check_system_platform()
    sync_function = get_sync_function(system_platform)
    sync_function(
        source, destination, options, backup, backup_dir, sanitized_subprocess_kwargs
    )


def rsync(
    source: str,
    destination: str,
    options: list | None = None,
    backup: bool = False,
    backup_dir: str = "",
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
    args = options[:] if options else []
    args = args + ["--backup"] if backup else args
    args = args + [f"--backup-dir={backup_dir}"] if backup_dir else args
    args = get_filtered_args(args, {"rsync", source, destination})
    args = ["rsync"] + args + [source, destination]

    # Ensure kwargs is dict if rsync is called directly
    kwargs = subprocess_kwargs.copy() if subprocess_kwargs else {}

    try:
        completed_process = subprocess.run(args, **kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(
            "rsync does not seem to be installed on your system (or path is not set)!\n"
            + "Install rsync or fix path for program to work."
        )

    return completed_process


def check_system_platform() -> str:
    """Returns system platform as string. Checks that platform is supported else
    raises error.

    Raises:
        NotImplementedError: _description_

    Returns:
        str: System platform as string
    """

    system_platform = platform.system()

    # Below control statement raises error of platform is not supported
    if system_platform == "Linux":
        pass
    elif system_platform == "Windows":
        # TODO Implement this via robocopy. Will require mappings of options (dict)
        raise NotImplementedError(f"Functionality for Windows is not implemented!")
    elif system_platform == "Darwin":
        # TODO Maybe implement this in the future
        raise NotImplementedError(
            f"Functionality for Darwin (MacOS) is not implemented!"
        )
    else:
        raise NotImplementedError(
            f"Functionality for {system_platform} is not implemented!"
        )

    return system_platform


def get_sync_function(system_platform: str):
    """Get the synchronization function based on the system platform."""
    platform_to_function_map = {
        "Linux": rsync,
        # "Windows": robocopy, # Uncomment when implemented
        # "Darwin": some_other_sync_function, # Uncomment when implemented
    }

    return platform_to_function_map.get(system_platform, None)


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
    sanitized_kwargs = kwargs.copy() if kwargs else {}
    sanitized_kwargs.pop("shell", None)
    return sanitized_kwargs
