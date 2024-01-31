import subprocess
from pathlib import Path


class SyncBase:
    _default_opts = []

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
        backup: str | Path = "",
        options: list | None = [],
    ) -> None:
        self.src = self.resolve_dir(src)
        self.dst = self.resolve_dir(dst)
        self.backup = self.resolve_dir(backup, must_exist=False, empty_allowed=True)
        self.options = options if options else []

    @property
    def default_opts(self):
        return self._default_opts.copy()

    @staticmethod
    def resolve_dir(
        path: str | Path, must_exist: bool = True, empty_allowed: bool = False
    ):
        if not path:
            if not empty_allowed:
                raise ValueError("Empty path not allowed!")
            return None

        path = Path(path) if isinstance(path, str) else path
        path = path.resolve()

        if must_exist and (not path.is_dir()):
            raise ValueError(f"{path} does not point to an existing dir!")

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
            list: Deduplicated list without unwanted args with initial order intact
        """
        excl = unwanted_args or set()
        args_dict = {}
        i = 0

        for option in args:
            if option not in excl:
                args_dict.setdefault(option, []).append(i)
                i += 1
        
        if not duplicates_allowed:
            return [ key for key in args_dict ]

        ordered_args = []
        for key, indices in args_dict.items():
            for index in indices:
                if len(ordered_args) <= index:
                    ordered_args.extend([None] * (index + 1 - len(ordered_args)))
                ordered_args[index] = key

        return ordered_args

    @staticmethod
    def sanitize_subprocess_kwargs(kwargs: dict | None) -> dict:
        """Sanitize the subprocess keyword arguments."""
        kwargs.pop("shell", None)
        return kwargs


class Rsync(SyncBase):
    _default_opts = ["-a", "-i", "-v", "-h"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
        backup: str | Path = "",
        options: list | None = [],
    ) -> None:
        super().__init__(src, dst, backup, options)

    def get_args(
        self, options: list, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        # Trailing slashes are importent in rsync call for consistent behaviour
        src_string = str(self.src) + "/"
        dst_string = str(self.dst) + "/"
        opts = options.copy()

        if delete:
            opts.append("--delete")
        if dry_run:
            opts.append("--dry-run")
        if self.backup:
            opts.append("--backup")
            opts.append("--backup-dir=" + str(self.backup))

        return (src_string, dst_string, opts)

    def sync(
        self,
        use_defaults: bool,
        delete: bool = False,
        dry_run: bool = False,
        subprocess_kwargs: dict | None = {},
    ) -> subprocess.CompletedProcess:
        # Create/filter args list to pass to subprocess.run
        opts = self.default_opts if use_defaults else self.options
        src_string, dst_string, opts = self.get_args(opts, delete, dry_run)
        args = self.filter_args(args, {"rsync", src_string, dst_string})
        args = ["rsync"] + args + [self.src, self.dst]

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
    _default_opts = ["/E", "/DCOPY:DAT", "/COPY:DAT", "/R:3", "/W:1"]

    def __init__(
        self,
        src: str | Path,
        dst: str | Path,
        backup: str | Path = "",
        options: list | None = [],
    ) -> None:
        super().__init__(src, dst, backup, options)

    def get_args(
        self, options: list, delete: bool, dry_run: bool
    ) -> tuple[str, str, list[str]]:
        pass

    def sync(
        self,
        use_defaults: bool,
        delete: bool = False,
        dry_run: bool = False,
        subprocess_kwargs: dict | None = {},
    ) -> subprocess.CompletedProcess:
        pass
