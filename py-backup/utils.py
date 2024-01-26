"""Contains utility functions used by core.py"""
import pathlib
import platform
import subprocess


def sync(source: pathlib.Path, destination: pathlib.Path, options: list) -> None:
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
    source: pathlib.Path, destination: pathlib.Path, options: list | None
) -> subprocess.CompletedProcess | None:
    """Calls rsync(options, source, destination) through subprocess run.

    Args:
        source (pathlib.Path): Source folder/file
        destination (pathlib.Path): Destination folder/file
        options (list): Args list to be passed on to rsync, robocopy etc

    Returns:
        subprocess.CompletedProcess: returns CompletedProcess instance
        from subprocess.run if there is one else None.
    """

    arglist = options[:] if options else []
    arglist.append(source)
    arglist.append(destination)
    completed_process = subprocess.run(arglist, text=True, capture_output=True)
    return completed_process.returncode if completed_process else None


if __name__ == "__main__":
    sync()
