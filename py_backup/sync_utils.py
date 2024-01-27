"""Contains utility functions used by core.py"""
import platform
import subprocess


def sync(source: str, destination: str, options: list | None = None, subprocess_kwargs: dict | None = None) -> None:
    kwargs = subprocess_kwargs if subprocess_kwargs else {}
    
    # Remove shell key if exists since shell calls with subprocess.run are not allowed.
    kwargs.pop("shell", None)

    # Get the system's platform string
    system_platform = platform.system()

    # Deduce which os the user runs and call the appropriate function
    if system_platform == "Linux":
        rsync(source, destination, options, kwargs)
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

def rsync(
    source: str, destination: str, options: list | None = None, subprocess_kwargs: dict | None = None
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
    args = get_filtered_args(args, {"rsync", source, destination})
    args = ["rsync"] + args + [source, destination]
    
    # Make sure kwargs is dict even if subprocess_kwargs were not provided
    kwargs = subprocess_kwargs if subprocess_kwargs else {}

    try:
        completed_process = subprocess.run(args, **kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(
            "rsync does not seem to be installed on your system (or path is not set)!\n"
            + "Install rsync or fix path for program to work."
        )

    return completed_process

def get_filtered_args(args: list, unwanted_args: set | None = None) -> list:
    """Short function to remove duplicate args and remove unwanted_args while
    maintaining args list order (if duplicate first position is kept).

    Args:
        args (list): Unfiltered args list
        unwanted_args (set): Set of unwanted args to remove. Defaults to None if not provided.

    Returns:
        list: deduplicated list without unwanted args with initial order intact
    """

    args_dict = { key: None for key in args }
    excl = unwanted_args if unwanted_args else set()
    filtered_args_dict = { key: None for key in args_dict if key not in excl }
    return list(filtered_args_dict)
    