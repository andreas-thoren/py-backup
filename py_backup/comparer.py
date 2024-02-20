"""
This module provides functionality to compare two directories, identifying files and
subdirectories that are equal, unique, mismatched in type, or have content changes.

It defines:
- `FileType` Enum: Represents different types of file system objects.
- `FileStatus` Enum: Describes the comparison result between corresponding entries in the two directories.
- `InfiniteDirTraversalLoopError` Exception: Custom exception for infinite traversal loops.
- `DirComparator` Class: Main class for comparing directories.

Example usage is provided in the `DirComparator` class docstring.
"""
import os
import stat
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Iterator, Iterable


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
    NOT_COMPARED = auto()
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
    Compares two directories, reporting on differences and similarities
    between them, including file types and statuses.

    Attributes:
        dir1 (str | Path): Path to the first directory.
        dir2 (str | Path): Path to the second directory.
        dir1_name (str): Identifier for the first directory in comparison results.
        dir2_name (str): Identifier for the second directory in comparison results.

    Example:
    >>> from py_backup.comparer import DirComparator
    >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2")
    >>> comparator.compare_directories()
    >>> result = comparator.dir_comparison
    >>> print(result)
    # Indentation below only for readability. Key order is not guaranteed.
    # Note that FileStatus and FileType members are used as dictionary keys.
    {
        'dir1': {
            <FileType.DIR: 2>: {
                <FileStatus.UNIQUE: 2>: {'rel_path/to/sample/dir', ...}
            },
            <FileType.FILE: 1>: {...}
        },
        'mutual': {
            <FileType.FILE: 1>: {
                <FileStatus.CHANGED: 2>: {'rel_path/to/sample/file, ...}
            }
        }
        'dir2': ... # Same nesting as above
    }
    """

    _mutual_key = "mutual"

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
        """
        Initializes the DirComparator with two directories to compare.

        Args:
            dir1 (str | Path): The first directory to compare.
            dir2 (str | Path): The second directory to compare.
            dir1_name (str): Optional. A name to represent the first directory in comparison results.
            dir2_name (str): Optional. A name to represent the second directory in comparison results.

        Raises:
            ValueError: If either directory does not exist,
                if the same directory is provided for both,
                or if the names are identical.
        """
        # TODO add docstring that explains the dir1 and dir2 paths should not
        # contain symlinks since normpath can then inadvertedly change them
        self._dir1 = os.path.normpath(str(dir1))
        self._dir2 = os.path.normpath(str(dir2))

        # Error checks
        if not os.path.exists(self._dir1):
            raise ValueError(f"{self._dir1} is not the path to an existing dir!")
        if not os.path.exists(self._dir2):
            raise ValueError(f"{self._dir2} is not the path to an existing dir!")
        if self._dir1 == self._dir2:
            raise ValueError("The directories to be compared cannot be the same!")
        if dir1_name == dir2_name:
            raise ValueError("You cannot give the 2 directories the same name!")

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
        """
        Creates and returns a formatted multiline string summarizing
        the comparison results between the two directories.

        Returns:
            A formatted string representing the comparison result.

        Example:
        >>> from py_backup.comparer import DirComparator
        >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2")
        >>> comparator.compare_directories()
        >>> print(comparator.get_comparison_result())
        DIR1 UNIQUE FILEs:
        path/to/dir1/unique_file.txt

        DIR2 UNIQUE FILEs:
        path/to/dir2/unique_file2.txt
        ...
        """
        result = "\n"
        for dct_name, main_dct in self._dir_comparison.items():
            for file_type, type_dct in main_dct.items():
                for status, entry_set in type_dct.items():
                    headline = (
                        f"{dct_name.upper()} {status.name.replace('_', ' ')} "
                        + f"{file_type.name}s:\n"
                    )
                    result += headline
                    for entry in entry_set:
                        result += f"{entry}\n"
                    result += "\n"
        return result

    def get_entries(
        self,
        base_dirs: Iterable[str] | None = None,
        entry_types: Iterable[FileType] | None = None,
        entry_statuses: Iterable[FileStatus] | None = None,
    ) -> list[str]:
        """
        Retrieves a list of entries filtered by specified directories, types, and statuses.

        Args:
            base_dirs (Iterable[str] | None): Optional. Directories to include (dir1, dir2, mutual). None for all.
            entry_types (Iterable[FileType] | None): Optional. Types of entries to include. None for all.
            entry_statuses (Iterable[FileStatus] | None): Optional. Statuses to include. None for all.

        Returns:
            list[str]: Paths of entries that match the filters.

        Example:
        >>> from py_backup.comparer import DirComparator, FileType, FileStatus
        >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2", "src", "dst")
        >>> comparator.compare_directories()
        >>> dirs = ["src", "mutual"] # OR (equivalent) dirs = ["dir1", "mutual"]
        >>> types = [FileType.FILE]
        >>> statuses = [FileStatus.UNIQUE, FileStatus.CHANGED]
        >>> comparator.get_entries(dirs, types, statuses)
        ['path/to/dir1/changed_mutual_file.txt', 'path/to/dir2/changed_mutual_file.txt',
        'path/to/dir1/unique_dir1_file.txt', ...]

        Note: Mutual files gets included on both sides, se example above
        """
        if base_dirs:
            subst_map = {"dir1": self._dir1_name, "dir2": self._dir2_name}
            base_dirs = {subst_map.get(base_dir, base_dir) for base_dir in base_dirs}
        else:
            base_dirs = {self._dir1_name, self._dir2_name, self._mutual_key}

        types = set(entry_types) if entry_types else set(FileType)
        statuses = set(entry_statuses) if entry_statuses else set(FileStatus)
        entries = []
        base_to_root_path_map = {
            self._dir1_name: (self._dir1,),
            self._dir2_name: (self._dir2,),
            self._mutual_key: (self._dir1, self._dir2),
        }

        for dct_name, main_dct in self._dir_comparison.items():
            if dct_name not in base_dirs:
                continue

            for file_type, type_dct in main_dct.items():
                if file_type not in types:
                    continue

                for status, entry_set in type_dct.items():
                    if status not in statuses:
                        continue

                    root_paths = base_to_root_path_map[dct_name]
                    for root_path in root_paths:
                        paths = [os.path.join(root_path, entry) for entry in entry_set]
                        entries.extend(paths)

        return entries

    def compare_directories(
        self,
        unilateral_compare: bool = False,
        follow_symlinks: bool = False,
        exclude_equal_entries: bool = True,
        expand_dirs: bool = False,
    ) -> None:
        """
        Key method of the DirComparator class. Almost all use cases will call this
        method at least once. Performs the directory comparison based on the
        provided args. After calling this method you can:
        - get the results dict with the dir_comparison property
        - get filtered result entries with the get_entries method
        - get a formatted result string with the get_comparison_result method.

        Args:
            unilateral_compare (bool): Optional. If True, compares in one direction only.
            follow_symlinks (bool): Optional. If True, follows symbolic links.
            exclude_equal_entries (bool): Optional. If True, equal entries are not listed in the comparison result.
            expand_dirs (bool): Optional. If True, include items nested in unique dirs

        Example:
        >>> from py_backup.comparer import DirComparator
        >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2")
        >>> comparator.compare_directories(expand_dirs=True, exclude_equal_entries=False)
        >>> result = comparator.dir_comparison
        # Do something with the result. Note that with the options above all items
        # in the compared directories will be included in the result.
        """
        self._unilateral_compare = unilateral_compare
        self._follow_symlinks = follow_symlinks
        self._exclude_equal_entries = exclude_equal_entries
        self._dir_comparison.clear()
        self._visited = set()
        self._recursive_scandir_cmpr("")

        if expand_dirs:
            self.expand_dirs()

    def expand_dirs(self) -> None:
        """
        Expands all unique directories found in the comparison results
        to include all nested items.

        This method iterates over unique directories in the comparison result.
        It recursively scans these directories, adding all nested files and
        subdirectories to the comparison results with their respective statuses
        set to UNIQUE. This provides a complete inventory of all items
        that do not have a counterpart in the other directory.

        Note:
            - This method should be called after `compare_directories` to ensure that there are
              comparison results to expand.
            - The method modifies the internal comparison results dictionary to include entries
              for all nested items within unique directories.
            - If `compare_directories` is called with `expand_dirs=True`,
              this method is implicitly called, and there's no need to call it separately.

        Example:
            >>> from py_backup.comparer import DirComparator
            >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2")
            >>> comparator.compare_directories()
            # Initially, only top-level unique dirs are included.
            >>> comparator.expand_dirs()
            # Now, the comparison results also include detailed entries
            # for all items within unique directories.
        """
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
                        dirs.append(entry_path)

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
        # Set initial vars
        common_dirs = []
        dir2_entries_dict = {entry.name: entry for entry in dir2_iterator}

        # Iterate over and compare each dir1_entry
        # with the corresponding dir2_entry (if any)
        for dir1_entry in dir1_iterator:
            # Get corresponding dir2_entry
            dir2_entry = dir2_entries_dict.pop(dir1_entry.name, None)
            # Get FileType:s of DirEntry:s
            dir1_entry_type = self._get_file_type(dir1_entry)
            dir2_entry_type = self._get_file_type(dir2_entry)
            # Get rel path of DirEntry:s
            entry_path = os.path.join(rel_path, dir1_entry.name)

            # Below if block evaluates and handles logic for different 
            # type alignments between dir1_entry and dir2_entry
            if dir1_entry_type == dir2_entry_type:
                if dir1_entry_type == FileType.DIR:
                    # Both entries are dirs
                    common_dirs.append(entry_path)

                status = self._get_file_status(dir1_entry, dir2_entry, dir1_entry_type)
                if (
                    status in {FileStatus.EQUAL, FileStatus.NOT_COMPARED}
                    and self._exclude_equal_entries
                ):
                    continue
                key = self._mutual_key
            elif dir2_entry is None:
                # Unique dir1_entry
                status = FileStatus.UNIQUE
                key = self._dir1_name
            else:
                # Not same type and dir2_entry is not None -> type mismatch
                status = FileStatus.MISMATCHED
                key = self._dir1_name
                # Add mismatched entry to dir2 side as well (if not unilateral compare)
                if not self._unilateral_compare:
                    self._add_dct_entry(
                        entry_path, self._dir2_name, dir2_entry_type, status
                    )

            # Add dir1_entry to result dict (self._dir_comparison)
            self._add_dct_entry(entry_path, key, dir1_entry_type, status)

        # Add remaining (not popped) unique entries from dir2 to the result dict,
        # if not unilateral compare
        if not self._unilateral_compare:
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
        type_dct.setdefault(file_status, set()).add(entry_path)

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
    ) -> FileStatus:
        if file_type == FileType.FILE:
            return self._get_regular_file_status(dir1_entry, dir2_entry)
        # Right now only files are compared
        return FileStatus.NOT_COMPARED

    @staticmethod
    def _get_regular_file_status(
        dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, tolerance: float = 2
    ) -> FileStatus:
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
