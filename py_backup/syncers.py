import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class SyncABC(ABC):
    _default_opts = []

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        self.src = self.resolve_dir(src)
        self.dst = self.resolve_dir(dst)

    @property
    def default_opts(self):
        return self._default_opts.copy()

    @staticmethod
    def resolve_dir(path: str | Path, must_exist: bool = True) -> Path | None:
        if not path:
            # Wont guess what empty value means. Cannot resolve. Return
            return None

        path = Path(path) if isinstance(path, str) else path
        path = path.resolve()

        if must_exist and (not path.is_dir()):
            raise ValueError(f"{path} does not point to an existing dir!")
        
        return path

    @staticmethod
    def filter_args(args: list, unwanted_args: set | None = None, duplicates_allowed: bool = True) -> list:
        """
        Function to remove duplicate args and remove unwanted_args while
        maintaining args list order (if duplicate first position is kept).

        Args:
            args (list): Unfiltered args list
            duplicates_allowed (bool): Flag to allow or disallow duplicates
            unwanted_args (set, optional): Set of unwanted args to remove. Defaults to None.

        Returns:
            list: Deduplicated list without unwanted args and initial order intact
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
        
        args = self.get_args(options, delete, dry_run)
        subprocess_kwargs = self.get_sanitized_subprocess_kwargs(subprocess_kwargs)

        if backup and not dry_run:
            backup = self.resolve_dir(backup, must_exist=False)
            self.backup(backup, delete, args)
        
        return self.subprocess_run(args, subprocess_kwargs)

    @staticmethod
    def get_sanitized_subprocess_kwargs(kwargs: dict | None) -> dict:
        """Sanitize the subprocess keyword arguments."""
        kwargs = kwargs.copy() if kwargs else {}
        kwargs.pop("shell", None)
        return kwargs
    
    @staticmethod
    def subprocess_run(args_list: list, subprocess_kwargs: dict | None):
        try:
            completed_process = subprocess.run(args_list, **subprocess_kwargs)
        except FileNotFoundError:
            raise FileNotFoundError(
                "rsync does not seem to be installed on your system (or path is not set)!\n"
                + "Install rsync or fix path for program to work."
            )

        return completed_process

    @abstractmethod
    def backup(self, backup: Path, backup_missing: bool, args: list):
        pass

    @abstractmethod
    def get_args(
        self,
        options: list | None,
        delete: bool,
        dry_run: bool
    ) -> tuple[str, str, list[str]]:
        """Used by sync method to get args list for subsequent subproccess call"""


class Rsync(SyncABC):
    # TODO maybe put this in a config file somewhere
    _default_opts = ["-a", "-i", "-v", "-h"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        super().__init__(src, dst)

    def get_args(
        self, options: list, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        # Trailing slashes are importent in rsync call for consistent behaviour
        options = options.copy() if options is not None else self.default_opts
        src_string = str(self.src) + "/"
        dst_string = str(self.dst) + "/"

        if delete:
            options.append("--delete")
        if dry_run:
            options.append("--dry-run")
        
        args = self.filter_args(options, {"rsync", src_string, dst_string})
        return ["rsync"] + args + [src_string, dst_string]
    
    def backup(self, backup: Path, _, args: list):
        """Rsyncs backup work by just modifying the args list in place since
        rsync have innate backup functionality"""
        
        backup = self.resolve_dir(backup, must_exist=False)

        for i in range(len(args)-1, -1, -1):
            arg = args[i]

            if arg == "--backup" or arg.startswith("--backup-dir="):
                del args[i]
            
        args.insert(-3, "--backup")
        args.insert(-3, "--backup-dir=" + str(backup))


class Robocopy(SyncABC):
    # TODO maybe put this in a config file somewhere
    _default_opts = ["/E", "/DCOPY:DAT", "/COPY:DAT", "/R:3", "/W:1"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        super().__init__(src, dst)

    def get_args(
        self, options: list, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:

        options = options.copy() if options is not None else self.default_opts
        src_string = str(self.src)
        dst_string = str(self.dst)

        if delete:
            options.append("/PURGE")
        if dry_run:
            options.append("/L")

        args = self.filter_args(options, {"robocopy", src_string, dst_string})
        args = ["robocopy"] + [src_string, dst_string] + args

    def backup(self, backup: Path, backup_missing: bool, args: list):

        backup = self.resolve_dir(backup, must_exist=False)
        # TODO implement backup functionality
        raise NotImplementedError(
            "The backup function in robocopy is not yet implemented!"
        )
