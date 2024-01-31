import subprocess
from pathlib import Path


class SyncBase:
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

    @staticmethod
    def sanitize_subprocess_kwargs(kwargs: dict | None) -> dict:
        """Sanitize the subprocess keyword arguments."""
        kwargs.pop("shell", None)
        return kwargs


class Rsync(SyncBase):
    # TODO maybe put this in a config file somewhere
    _default_opts = ["-a", "-i", "-v", "-h"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        super().__init__(src, dst)

    def get_args(
        self, options: list, delete: bool, dry_run: bool) -> tuple[str, str, list[str]]:
        # Trailing slashes are importent in rsync call for consistent behaviour
        src_string = str(self.src) + "/"
        dst_string = str(self.dst) + "/"
        opts = options.copy()

        if delete:
            opts.append("--delete")
        if dry_run:
            opts.append("--dry-run")

        return (src_string, dst_string, opts)

    def sync(
        self,
        delete: bool = False,
        dry_run: bool = False,
        backup: str | Path = "",
        options: list | None = None,
        subprocess_kwargs: dict | None = {},
    ) -> subprocess.CompletedProcess:
        opts = options.copy() if options is not None else self.default_opts
        src_string, dst_string, opts = self.get_args(opts, delete, dry_run)

        # rsync have built in backup functionality. Simply add flags!
        if backup:
            backup = self.resolve_dir(backup, must_exist=False)
            # If backup or backup-dir is specified through options remove dupl flags.
            opts = [
                opt for opt in opts
                if not (opt == "--backup" or opt.startswith("--backup-dir="))
            ]
            opts.append("--backup")
            opts.append("--backup-dir=" + str(backup))

        args = self.filter_args(opts, {"rsync", src_string, dst_string})
        args = ["rsync"] + args + [src_string, dst_string]

        # Ensure kwargs is dict if rsync is called directly
        kwargs = subprocess_kwargs.copy() if subprocess_kwargs else {}
        sanitized_subprocess_kwargs = self.sanitize_subprocess_kwargs(kwargs)

        try:
            completed_process = subprocess.run(args, **sanitized_subprocess_kwargs)
        except FileNotFoundError:
            raise FileNotFoundError(
                "rsync does not seem to be installed on your system (or path is not set)!\n"
                + "Install rsync or fix path for program to work."
            )

        return completed_process


class Robocopy(SyncBase):
    # TODO maybe put this in a config file somewhere
    _default_opts = ["/E", "/DCOPY:DAT", "/COPY:DAT", "/R:3", "/W:1"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:
        super().__init__(src, dst)

    def get_args(
        self, options: list, delete: bool, dry_run: bool) -> tuple[str, str, list[str]]:
        src_string = str(self.src)
        dst_string = str(self.dst)
        opts = options.copy()

        if delete:
            opts.append("/PURGE")
        if dry_run:
            opts.append("/L")

        return (src_string, dst_string, opts)

    def sync(
        self,
        delete: bool = False,
        dry_run: bool = False,
        backup: str | Path = "",
        options: list | None = None,
        subprocess_kwargs: dict | None = {},
    ) -> subprocess.CompletedProcess:
        opts = options.copy() if options is not None else self.default_opts
        src_string, dst_string, opts = self.get_args(opts, delete, dry_run)
        
        if backup:
            backup = self.resolve_dir(backup, must_exist=False)
            # TODO implement backup functionality
            raise NotImplementedError(
                "The backup function in robocopy is not yet implemented!"
            )

        args = self.filter_args(opts, {"robocopy", src_string, dst_string})
        args = ["robocopy"] + [src_string, dst_string] + args

        # Ensure kwargs is dict if rsync is called directly
        kwargs = subprocess_kwargs.copy() if subprocess_kwargs else {}
        sanitized_subprocess_kwargs = self.sanitize_subprocess_kwargs(kwargs)

        try:
            completed_process = subprocess.run(args, **sanitized_subprocess_kwargs)
        except FileNotFoundError:
            raise FileNotFoundError(
                "robocopy does not seem to be installed on your system (or path is not set)!\n"
                + "Install robocopy or fix path for program to work."
            )

        return completed_process
