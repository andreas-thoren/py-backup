"""Contains utility functions used by core.py"""
import platform
import subprocess


def sync(source: str, destination: str, options: list | None = None) -> None:
    # Get the system's platform string
    system_platform = platform.system()

    if system_platform == "Linux":
        rsync(source, destination, options)
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
    source: str, destination: str, options: list | None = None
) -> subprocess.CompletedProcess | None:
    """Calls rsync(options, source, destination) through subprocess run.

    Args:
        source (str): Source folder/file
        destination (str): Destination folder/file
        options (list): Args list to be passed on to rsync, robocopy etc

    Returns:
        subprocess.CompletedProcess: returns CompletedProcess instance
        from subprocess.run if there is one else None.
    """

    # If user has provided options make a copy of them (to avoid mutating original list)
    # If no options are provided set arglist equal to empty list
    arglist = options[:] if options else []
    arglist = ["rsync"] + arglist
    arglist.append(source)
    arglist.append(destination)

    try:
        completed_process = subprocess.run(arglist, text=True, capture_output=True)
    except FileNotFoundError:
        raise FileNotFoundError(
            "rsync does not seem to be installed on your system (or path is not set)!\n"
            + "Install rsync or fix path for program to work."
        )
    return completed_process if completed_process else None
