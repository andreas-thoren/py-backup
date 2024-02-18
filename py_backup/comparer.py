import os
import stat
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Iterator


class FileType(Enum):
    FILE = auto()
    DIR = auto()
    SYMLINK = auto()
    JUNCTION = auto()
    BLOCK_DEVICE = auto()
    CHARACTER_DEVICE = auto()
    FIFO = auto()
    SOCKET = auto()
    DOOR = auto()
    EVENT_PORT = auto()
    WHITEOUT = auto()
    UNKNOWN = auto()


class FileStatus(Enum):
    EQUAL = auto()
    UNIQUE = auto()
    MISMATCHED = auto()
    CHANGED = auto()
    # Currently only EQUAL, UNIQUE, MISMATCHED and CHANGED is used in the application
    NEWER = auto()
    OLDER = auto()


class InfiniteDirTraversalLoopError(Exception):
    """
    Exception raised when an infinite loop is detected due to symlinks/junctions
    during directory traversal.
    """

    def __init__(
        self, path, msg="Infinite traversal loop detected while traversing directories"
    ):
        self.path = path
        self.msg = msg
        super().__init__(f"{msg}: {path}")


class DirComparator:
    """
    Purpose of class is to compare dir at dir_path with dir at compare_dir_path.
    """

    mode_to_filetype_map = {
        stat.S_IFDIR: FileType.DIR,
        stat.S_IFREG: FileType.FILE,
        stat.S_IFLNK: FileType.SYMLINK,
        stat.S_IFBLK: FileType.BLOCK_DEVICE,
        stat.S_IFCHR: FileType.CHARACTER_DEVICE,
        stat.S_IFIFO: FileType.FIFO,
        stat.S_IFSOCK: FileType.SOCKET,
        stat.S_IFDOOR: FileType.DOOR,
        stat.S_IFPORT: FileType.EVENT_PORT,
        stat.S_IFWHT: FileType.WHITEOUT,
        0: FileType.UNKNOWN,
    }

    def __init__(
        self,
        dir1: str | Path,
        dir2: str | Path,
        dir1_name: str = "dir1",
        dir2_name: str = "dir2",
    ) -> None:
        # TODO add docstring that explains the dir1 and dir2 paths should not
        # contain symlinks since normpath can then inadvertedly change them
        self._dir1 = os.path.normpath(str(dir1))
        self._dir2 = os.path.normpath(str(dir2))
        # Check that both dirs exist
        if not os.path.exists(self._dir1):
            raise ValueError(f"{self._dir1} is not the path to an existing dir!")
        if not os.path.exists(self._dir2):
            raise ValueError(f"{self._dir2} is not the path to an existing dir!")
        if self._dir1 == self._dir2:
            raise ValueError("The directories to be compared cannot be the same!")
        if dir1_name == dir2_name:
            raise ValueError("You cannot give the 2 directories the same name!")

        # TODO add check that dir1 != dir2 and dir1_name != dir2_name
        # Useful for testing purpuses. Will wait.
        self._dir1_name = dir1_name
        self._dir2_name = dir2_name
        self._unilateral_compare = False
        self._follow_symlinks = False
        self._exclude_equal_entries = True
        self._visited = None  # Will be a set
        self._dir_comparison = {}

    @property
    def dir1(self) -> str:
        return self._dir1

    @property
    def dir2(self) -> str:
        return self._dir2

    @property
    def dir1_name(self) -> str:
        return self._dir1_name

    @property
    def dir2_name(self) -> str:
        return self._dir2_name

    @property
    def dir_comparison(self) -> dict:
        return deepcopy(self._dir_comparison)

    def get_comparison_result(self) -> str:
        result = "\n"
        for dct_name, main_dct in self._dir_comparison.items():
            for file_type, type_dct in main_dct.items():
                for status, entry_list in type_dct.items():
                    headline = f"{dct_name.upper()} {status.name} {file_type.name}s:\n"
                    result += headline
                    for entry in entry_list:
                        result += f"{entry}\n"
                    result += "\n"
        return result

    def compare_directories(
        self,
        unilateral_compare: bool = False,
        follow_symlinks: bool = False,
        exclude_equal_entries: bool = True,
        expand_dirs: bool = False,
    ) -> None:
        self._unilateral_compare = unilateral_compare
        self._follow_symlinks = follow_symlinks
        self._exclude_equal_entries = exclude_equal_entries
        self._dir_comparison.clear()
        self._visited = set()
        self._recursive_scandir_cmpr("")

        if expand_dirs:
            self.expand_dirs()

    def _recursive_scandir_cmpr(self, rel_path: str) -> None:
        """Recursive function called exclusively by dir_compare.
        Works by recursing down (depth first) dirs by repeatedly calling os.scandir.
        """
        dir1_path = os.path.join(self._dir1, rel_path)
        dir2_path = os.path.join(self._dir2, rel_path)
        common_dirs = []  # Needed if _compare_dir_entries raises. Do not remove.

        try:
            self._check_visited(dir1_path)
            with os.scandir(dir1_path) as dir1_iterator:
                with os.scandir(dir2_path) as dir2_iterator:
                    common_dirs = self._compare_dir_entries(
                        rel_path, dir1_iterator, dir2_iterator
                    )

        except PermissionError:
            print(f"Could not access {rel_path} . Skipping!")
        except OSError as exc:
            print(
                f"Unspecfic os error for path {rel_path}\n\nError Info:\n"
                + f"{exc}\n\nSkipping!"
            )

        # Recursive relation. Doesnt follow symlinks.
        for common_dir in common_dirs:
            self._recursive_scandir_cmpr(common_dir)

    def _check_visited(self, dir_path: str) -> None:
        stats = os.stat(dir_path)
        dirkey = (stats.st_dev, stats.st_ino)
        if dirkey in self._visited:
            raise InfiniteDirTraversalLoopError(path=dir_path)
        self._visited.add(dirkey)

    def _compare_dir_entries(
        self,
        rel_path: str,
        dir1_iterator: Iterator,
        dir2_iterator: Iterator,
    ) -> list[str]:
        common_dirs = []
        dir2_entries_dict = {entry.name: entry for entry in dir2_iterator}

        for dir1_entry in dir1_iterator:
            dir2_entry = dir2_entries_dict.pop(dir1_entry.name, None)
            dir1_entry_type = self._get_file_type(dir1_entry)
            dir2_entry_type = self._get_file_type(dir2_entry)
            entry_path = os.path.join(rel_path, dir1_entry.name)

            # If dir2_entry_type is None below if statement evaluates to False
            if dir1_entry_type == dir2_entry_type:
                if dir1_entry_type == FileType.DIR:
                    # Both entries are dirs
                    common_dirs.append(entry_path)
                    continue

                # Both entries have same type which are not dirs
                status = self._get_file_status(dir1_entry, dir2_entry, dir1_entry_type)
                if status == FileStatus.EQUAL and self._exclude_equal_entries:
                    continue

                key = "mutual"
            elif dir2_entry is None:
                # Unique dir1_entry
                status = FileStatus.UNIQUE
                key = self._dir1_name
            else:
                # Not same type and dir2_entry is not None -> type mismatch
                status = FileStatus.MISMATCHED
                key = self._dir1_name
                if not self._unilateral_compare:
                    self._add_dct_entry(
                        entry_path, self._dir2_name, dir2_entry_type, status
                    )

            self._add_dct_entry(entry_path, key, dir1_entry_type, status)

        if not self._unilateral_compare:
            # Add remaining (not popped) unique entries in dir2
            for unique_entry in dir2_entries_dict.values():
                entry_path = os.path.join(rel_path, unique_entry.name)
                file_type = self._get_file_type(unique_entry)
                self._add_dct_entry(
                    entry_path, self._dir2_name, file_type, FileStatus.UNIQUE
                )

        return common_dirs

    def _add_dct_entry(
        self,
        entry_path: str,
        dct_name: str,
        file_type: FileType,
        file_status: FileStatus,
    ) -> None:
        main_dct = self._dir_comparison.setdefault(dct_name, {})
        type_dct = main_dct.setdefault(file_type, {})
        type_dct.setdefault(file_status, []).append(entry_path)

    def _get_file_type(self, dir_entry: os.DirEntry | None) -> FileType | None:
        if dir_entry is None:
            return None

        try:
            # Below requires python 3.12. Skip for now. When added -> add before is_dir call.
            # if dir_entry.is_junction():
            # return "junction"

            # Exhaust is_* methods first to avoid unneccessary system calls.
            if dir_entry.is_file(follow_symlinks=self._follow_symlinks):
                return FileType.FILE
            if dir_entry.is_dir(follow_symlinks=self._follow_symlinks):
                return FileType.DIR
            if dir_entry.is_symlink():
                return FileType.SYMLINK

            stats = dir_entry.stat(follow_symlinks=self._follow_symlinks)
            mode = stat.S_IFMT(stats.st_mode)
            file_type = self.mode_to_filetype_map.get(mode, FileType.UNKNOWN)
        except OSError as exc:
            print(
                f"Error while trying to decide file type for {dir_entry}:\n"
                + f"{exc}\n"
                + "FileType set to UNKNOWN"
            )
            file_type = FileType.UNKNOWN

        return file_type

    def _get_file_status(
        self, dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, file_type: FileType
    ) -> FileType:
        if file_type == FileType.FILE:
            return self._get_regular_file_status(dir1_entry, dir2_entry)
        # Right now only files are compared all other types will compare as equal.
        return FileStatus.EQUAL

    @staticmethod
    def _get_regular_file_status(
        dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, tolerance: float = 2
    ) -> bool:
        try:
            dir1_stats = dir1_entry.stat()
            dir2_stats = dir2_entry.stat()
            time_diff = abs(dir1_stats.st_mtime - dir2_stats.st_mtime)
            size_equal = dir1_stats.st_size == dir2_stats.st_size
            if time_diff <= tolerance and size_equal:
                return FileStatus.EQUAL
        except OSError:
            # Right now OSError will lead to FileStatus.CHANGED being returned
            # since this means file will be backed up
            pass
        return FileStatus.CHANGED

    def expand_dirs(self) -> None:
        # 1. Fetch unique dirs on both sides
        dir1_dir_dct = self._dir_comparison.get(self._dir1_name, {}).get(
            FileType.DIR, {}
        )
        dir2_dir_dct = self._dir_comparison.get(self._dir2_name, {}).get(
            FileType.DIR, {}
        )
        dir1_dirs = [dir for dirs in dir1_dir_dct.values() for dir in dirs]
        dir2_dirs = [dir for dirs in dir2_dir_dct.values() for dir in dirs]

        # 2. Call _expand dir for all unique/mismatched dirs on both sides
        for dir1_dir in dir1_dirs:
            self._expand_dir(self._dir1, self._dir1_name, dir1_dir)

        for dir2_dir in dir2_dirs:
            self._expand_dir(self._dir2, self._dir2_name, dir2_dir)

    def _expand_dir(self, base_dir: str, base_dir_name: str, dir_rel_path: str) -> None:
        dir_path = os.path.join(base_dir, dir_rel_path)
        dirs = []

        try:
            self._check_visited(dir_path)
            with os.scandir(dir_path) as dir_iterator:
                for dir_entry in dir_iterator:
                    file_type = self._get_file_type(dir_entry)
                    entry_path = os.path.join(dir_rel_path, dir_entry.name)
                    self._add_dct_entry(
                        entry_path, base_dir_name, file_type, FileStatus.UNIQUE
                    )
                    if file_type == FileType.DIR:
                        dirs.append[entry_path]

        except PermissionError:
            print(f"Could not access {dir_path} . Skipping!")
        except OSError as exc:
            print(
                f"Unspecfic os error for path {dir_path}\n\nError Info:\n"
                + f"{exc}\n\nSkipping!"
            )

        # Recursive relation
        for nested_dir_path in dirs:
            self._expand_dir(base_dir, base_dir_name, nested_dir_path)