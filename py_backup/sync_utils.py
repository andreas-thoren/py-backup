"""Contains utility functions used by core.py"""
import subprocess


def rsync(
    source: str,
    destination: str,
    options: list | None = None,
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
    options: list | None = None,
    subprocess_kwargs: dict | None = None,
) -> None:
    # TODO
    pass


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
