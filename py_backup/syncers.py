import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from .config import RSYNC_DEFAULTS, ROBOCOPY_DEFAULTS


class SyncABC(ABC):
    _default_sync_options = []

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        self.src = self.resolve_dir(src)
        self.dst = self.resolve_dir(dst)

    @property
    def default_sync_options(self) -> list:
        return self._default_sync_options.copy()

    @staticmethod
    def resolve_dir(path: str | Path, must_exist: bool = True) -> Path:
        """
        Resolves the given path to an absolute path and checks if it points to an existing directory,
        if required. Raises a ValueError if the path is empty, or if the path does not point to an
        existing directory when `must_exist` is True.

        Args:
            path (str | Path): The file system path to resolve. Can be a string or a Path object.
            must_exist (bool, optional): If True, checks that the path points to an existing directory.
                Defaults to True.

        Returns:
            Path: The resolved absolute path as a Path object.

        Raises:
            ValueError: If the path is empty or does not point to an existing directory when required.

        Examples:
        >>> from pathlib import Path

        Resolving a relative directory path:
        >>> SyncABC.resolve_dir('py_backup').name
        'py_backup'

        Attempting to resolve a non-existing directory with must_exist=False:
        >>> SyncABC.resolve_dir('non_existing_dir', must_exist=False).name
        'non_existing_dir'

        Attempting to resolve a non-existing directory with must_exist=True:
        >>> SyncABC.resolve_dir('non_existing_dir', must_exist=True) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: ... does not point to an existing dir!

        Using an empty string as path:
        >>> SyncABC.resolve_dir('') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: path argument cannot be empty!...
        """
        if not path:
            raise ValueError(
                "path argument cannot be empty!"
                + 'If you want to specify current working directory use path = "."'
            )

        path = Path(path) if isinstance(path, str) else path
        path = path.resolve()

        if must_exist and (not path.is_dir()):
            raise ValueError(f"{path} does not point to an existing dir!")

        return path

    @staticmethod
    def filter_args(
        args: list, unwanted_args: set | None = None, duplicates_allowed: bool = True
    ) -> list:
        """
        Function to remove duplicate args and remove unwanted_args while
        maintaining args list order (if duplicate first position is kept).

        Args:
            args (list): Unfiltered args list
            unwanted_args (set, optional): Set of unwanted args to remove. Defaults to None.
            duplicates_allowed (bool, optional): Flag to allow or disallow duplicates

        Returns:
            list: Deduplicated list without unwanted args and initial order intact

        Example:
        >>> args = ["rsync", "--option1", "rsync", "--option2", "dest", "--option1"]
        >>> SyncABC.filter_args(args, {"rsync", "dest"})
        ['--option1', '--option2', '--option1']
        """
        excl = unwanted_args.copy() if unwanted_args else set()
        filtered_args = []

        for arg in args:
            if arg in excl:
                continue

            filtered_args.append(arg)
            if not duplicates_allowed:
                excl.add(arg)

        return filtered_args

    def sync(
        self,
        delete: bool = False,
        dry_run: bool = False,
        backup: str | Path = "",
        options: list | None = None,
        subprocess_kwargs: dict | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Synchronizes files from the source to the destination directory using the
        defined synchronization tool (e.g., rsync, robocopy). Optionally it also
        backs upp files about to be overwritten or deleted.

        Args:
            delete (bool, optional): If True, delete extraneous files from dest dirs. Defaults to False.
            dry_run (bool, optional): If True, perform a trial run with no changes made. Defaults to False.
            backup (str | Path, optional): Path to the backup directory. Defaults to an empty string.
            options (list | None, optional): Additional options to pass to the synchronization tool.
                If None default options will be used (see config.json).
            subprocess_kwargs (dict | None, optional): Additional kwargs to pass to subprocess.run. Defaults to None.

        Returns:
            subprocess.CompletedProcess: The result from the subprocess.run call.
        """
        # 1. Get args list to be passed to subprocess.run
        subprocess_args = self.get_args(options, delete, dry_run)

        # 2. Get (and sanitize) kwargs to be passed to subprocess.run
        subprocess_kwargs = self.get_kwargs(subprocess_kwargs)

        # 3. Call backup function to backup changed files (source <--> destination).
        # If delete == True missting files in destination directory will also be backed up.
        if backup and not dry_run:
            backup = self.resolve_dir(backup, must_exist=False)
            self.backup(backup, delete, subprocess_args)

        # 4. Call subprocess.run with error handling.
        return self.subprocess_run(subprocess_args, subprocess_kwargs)

    @staticmethod
    def get_kwargs(kwargs: dict | None) -> dict:
        """
        Prepares keyword arguments for the subprocess.run function by making a copy of the input
        kwargs dict, removing the 'shell' key if present, to avoid shell injection risks.

        Args:
            kwargs (dict | None): A dictionary of keyword arguments to be sanitized and passed to subprocess.run.

        Returns:
            dict: A sanitized dictionary of keyword arguments.

        Examples:
        >>> SyncABC.get_kwargs({'shell': True, 'stdout': subprocess.PIPE})
        {'stdout': -1}
        >>> SyncABC.get_kwargs(None)
        {}
        """
        kwargs = kwargs.copy() if kwargs else {}
        kwargs.pop("shell", None)
        return kwargs

    @staticmethod
    def subprocess_run(
        args_list: list, subprocess_kwargs: dict | None
    ) -> subprocess.CompletedProcess:
        """
        Executes a subprocess with the given arguments and keyword arguments.
        This method is a wrapper around subprocess.run, adding error handling
        for common issues like the executable not being found.

        Args:
            args_list (list): The list of arguments for subprocess.run. The first argument should be the executables name.
            subprocess_kwargs (dict | None): Additional keyword arguments to pass to subprocess.run.

        Returns:
            subprocess.CompletedProcess: The result from the subprocess.run call, which includes attributes
            like returncode, stdout, and stderr.

        Raises:
            FileNotFoundError: If the executable is not found or not executable.
        
        Example:
        >>> args_list = ['rsync', '-a', '-v', '-h', 'src', 'dst'] # doctest: +SKIP
        >>> kwargs = {'text': True, 'capture_output': True} # doctest: +SKIP
        >>> SyncABC.subprocess_run(args_list=args_list, subprocess_kwargs=kwargs) # doctest: +SKIP
        """
        try:
            completed_process = subprocess.run(
                args_list, **subprocess_kwargs, check=True
            )
        except FileNotFoundError as exc:
            cli_program = args_list[0]

            raise FileNotFoundError(
                f"{cli_program} does not seem to be installed on your system, "
                + "or path is not set.\n"
                + f"Install {cli_program} or fix path for program to work."
            ) from exc

        return completed_process

    @abstractmethod
    def backup(self, backup: Path, backup_missing: bool, args: list) -> None:
        """Abstract method. The implementation of this in each subclass should back
        up files about to be overwritten. If backup_missing is True then
        files missing from the destination directory should also be backed up.
        Backed up files should be put in the the directory specified by the backup
        Path with the directory structur in the destination folder intact.

        Args:
            backup (Path): Directory where backed up files should be put.
                Can be an existing or nonexisting dir. If nonexisting the dir
                should be created.
            backup_missing (bool): True if files existing in destination but not
                in source should be backed up.
            args (list): args that should be supplied to subprocess.run.
        """

    @abstractmethod
    def get_args(
        self, options: list | None, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        """Used by sync method to get args list for subsequent subproccess call"""


class Rsync(SyncABC):
    _default_sync_options = RSYNC_DEFAULTS

    def get_args(
        self, options: list | None, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        """
        Constructs the argument list for an rsync command based on the specified options, 
        whether to delete extraneous files from the destination, and whether to perform 
        a dry run. 

        Args:
            options (list): Additional options to pass to the rsync command.
            delete (bool): If True, include the --delete option to remove files from 
                           the destination not present in the source.
            dry_run (bool): If True, include the --dry-run option to simulate the command 
                            without making any changes.

        Returns:
            tuple[str, str, list[str]]: A tuple where the first element is the rsync command, 
                                        then follows a list of all other options.
                                        The second to last element will be the src_dir
                                        and the last element the dst_dir.

        Examples:
        >>> rsync = Rsync('tests/source', 'tests/destination')
        >>> rsync.get_args(['--archive'], delete=False, dry_run=True)  # doctest: +ELLIPSIS
        ['rsync', '--archive', '--dry-run', ..., ...]
        >>> rsync.get_args(['-ai'], delete=True, dry_run=False)  # doctest: +ELLIPSIS
        ['rsync', '-ai', '--delete', ..., ...]
        """
        # Trailing slashes are importent in rsync call for consistent behaviour
        options = options.copy() if options is not None else self.default_sync_options
        src = str(self.src) + "/"
        dst = str(self.dst) + "/"

        if delete:
            options.append("--delete")
        if dry_run:
            options.append("--dry-run")

        args = self.filter_args(options, {"rsync", src, dst})
        return ["rsync"] + args + [src, dst]

    def backup(self, backup: Path, _, args: list) -> None:
        """Rsyncs backup work by just modifying the args list in place since
        rsync have innate backup functionality"""
        for i in range(len(args) - 1, -1, -1):
            arg = args[i]

            if arg == "--backup" or arg.startswith("--backup-dir="):
                del args[i]

        args.insert(-2, "--backup")
        args.insert(-2, "--backup-dir=" + str(backup))


class Robocopy(SyncABC):
    _default_sync_options = ROBOCOPY_DEFAULTS

    def get_args(
        self, options: list | None, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        options = options.copy() if options is not None else self.default_sync_options
        src = str(self.src)
        dst = str(self.dst)

        if delete:
            options.append("/PURGE")
        if dry_run:
            options.append("/L")

        args = self.filter_args(options, {"robocopy", src, dst})
        return ["robocopy"] + [src, dst] + args

    def backup(self, backup: Path, backup_missing: bool, args: list) -> None:
        # TODO implement backup functionality
        raise NotImplementedError(
            "The backup function in robocopy is not yet implemented!"
        )
