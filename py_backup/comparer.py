"""
This module provides functionality to compare two directories, identifying files and
subdirectories that are equal, unique, mismatched in type, or have content changes.

It defines:
- `FileType` Enum: Represents different types of file system objects.
- `FileStatus` Flag: Describes the comparison result between corresponding entries
    in the two directories. Since this is a subclass of Flag it support bitwise operations.
- `InfiniteDirTraversalLoopError` Exception: Custom exception for infinite traversal loops.
- `DirComparator` Class: Main class for comparing directories.

Example usage is provided in the `DirComparator` class docstring.
"""
import fnmatch
import os
import re
import stat
from copy import deepcopy
from enum import Enum, Flag, auto
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


class FileStatus(Flag):
    NOT_COMPARED = auto()
    # UNKNOWN means FileStatus could not be determined (due to OSError)
    UNKNOWN = auto()
    EQUAL = auto()
    MISMATCHED = auto()
    UNIQUE = auto()
    CHANGED = auto()
    NEWER = auto()
    OLDER = auto()
    # If necessary add flags for permission owner, group or permission changes


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
            dir1 (str | Path): The first directory to compare. Path should
                not contain symlinks since path is later normalised and this can
                lead to the meaning of the path changing.
            dir2 (str | Path): The second directory to compare. Path should
                not contain symlinks since path is later normalised and this can
                lead to the meaning of the path changing.
            dir1_name (str): Optional. A name to represent the first directory
                in comparison results.
            dir2_name (str): Optional. A name to represent the second directory
                in comparison results.

        Raises:
            ValueError: If either directory does not exist,
                if the same directory is provided for both,
                or if the names are identical.
        """
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

        # Initial instance variables
        self._dir1_name = dir1_name
        self._dir2_name = dir2_name

        # Follow symlinks always start as false. Can be set using obj.follow_symlinks = True
        self._follow_symlinks = False

        # Initiate variables used in compare_directories method
        self._unilateral_compare = False
        self._include_equal_entries = False
        self._visited = set()
        self._exclude_objects = set()
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

    @property
    def follow_symlinks(self) -> bool:
        return self._follow_symlinks

    @follow_symlinks.setter
    def follow_symlinks(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("follow_symlinks can only be set to a boolean value!")

        self._follow_symlinks = value

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
        for dct_name, ftype, fstatus, entries in self._iter_result():
            headline = (
                f"{dct_name.upper()} {fstatus.name.replace('_', ' ')} "
                + f"{ftype.name}s:\n"
            )
            result += headline
            for entry in entries:
                result += f"{entry}\n"
            result += "\n"
        return result

    def get_entries(
        self,
        base_dirs: Iterable[str] | None = None,
        entry_types: Iterable[FileType] | None = None,
        target_statuses: Iterable[FileStatus] | None = None,
    ) -> list[str]:
        """
        Retrieves a list of entries filtered by specified directories, types, and statuses.
        This method filters entries based on the provided criteria and supports
        nuanced status matching thanks to FileStatus being a Flag enum.

        Entry will be included in the result list if:
        - Entry is in any of the provided base_dirs (if provided otherwise any base_dir)
            AND
        - Entry is of any of the provided FileType:s (if provided otherwise any FileType)
            AND
        # Final criteria is easiest explained in code.
        - any(target_status in entry_status for target_status in target_statuses) == True
            If target_statuses is None all statuses is included if first 2 criteria are met.

        Args:
            base_dirs (Iterable[str] | None): Optional. Directories to include (dir1, dir2, mutual).
                None for all.
            entry_types (Iterable[FileType] | None): Optional. Types of entries to include.
                None for all.
            target_statuses (Iterable[FileStatus] | None): Optional. Statuses to include.
                None for all.

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
        'path/to/dir1/unique_dir1_file.txt']

        Note: Mutual files gets included on both sides if 'mutual' is included in base_dirs.
        """
        result = []
        base_to_root_path_map = {
            self._dir1_name: (self._dir1,),
            self._dir2_name: (self._dir2,),
            self._mutual_key: (self._dir1, self._dir2),
        }

        for dct_name, _, _, entries in self._iter_result(
            base_dirs, entry_types, target_statuses
        ):
            root_paths = base_to_root_path_map[dct_name]
            for root_path in root_paths:
                paths = [os.path.join(root_path, entry) for entry in entries]
                result.extend(paths)

        return result

    def _iter_result(
        self,
        base_dirs: Iterable[str] | None = None,
        entry_types: Iterable[FileType] | None = None,
        target_statuses: Iterable[FileStatus] | None = None,
    ) -> Iterator[tuple[str, FileType, FileStatus, set[str]]]:
        """
        Filters and retrieves the entries for the get_entries and
        get_comparison_result methods. Supports nuanced status matching
        , bitmask style, thanks to FileStatus being a Flag enum. If any of the
        args are None that means no filtering will take place for that arg, ex
        target_statuses = None means all FileStatus will be acceptable as long
        as filters for base_dirs and entry_types match (if any).
        See get_entries for args description.
        """

        if base_dirs:
            subst_map = {"dir1": self._dir1_name, "dir2": self._dir2_name}
            base_dirs = {subst_map.get(base_dir, base_dir) for base_dir in base_dirs}
        else:
            base_dirs = set()

        ftypes = set(entry_types) if entry_types else set()
        fstatuses = set(target_statuses) if target_statuses else set()

        for dct_name, main_dct in self._dir_comparison.items():
            if base_dirs and dct_name not in base_dirs:
                continue

            for ftype, type_dct in main_dct.items():
                if ftypes and ftype not in ftypes:
                    continue

                for entry_status, entry_set in type_dct.items():
                    if fstatuses and not any(
                        target_status in entry_status for target_status in fstatuses
                    ):
                        continue

                    yield dct_name, ftype, entry_status, entry_set

    def compare_directories(
        self,
        unilateral_compare: bool = False,
        include_equal_entries: bool = False,
        excludes: Iterable[str] | None = None,
    ) -> None:
        """
        Key method of the DirComparator class. Almost all use cases will call this
        method at least once. Performs the directory comparison based on the
        provided args. After calling this method you can optionally call expand_dirs
        method to include items nested in exclusive dirs in the outcome.
        Then continue with one/several of the following actions:
        - get the results dict with the dir_comparison property
        - get filtered result entries with the get_entries method
        - get a formatted result string with the get_comparison_result method.

        Args:
            unilateral_compare (bool): Optional. If True, compares in one direction only.
            include_equal_entries (bool): Optional. If False, equal entries
                are not listed in the comparison result.
            excludes (Iterable[str] | None): Optional. List of unix style patterns
                representing paths to ignore during the comparison. If a
                pattern matches a dir the dir and all its content will be
                excluded.

        Example:
        >>> from py_backup.comparer import DirComparator
        >>> comparator = DirComparator("/path/to/dir1", "/path/to/dir2")
        >>> excl = ["*.txt", ".git"]
        >>> comparator.compare_directories(
            include_equal_entries=True, excludes= excl
        )
        # Initially, only top-level unique dirs are included.
        # For consistent results use same exludes for the expand_dirs call.
        >>> comparator.expand_dirs(exludes=excl)
        >>> result = comparator.dir_comparison
        """
        # Set initial state. These method variables is set as instance attributes
        # to minimize size of stack frames which might be important due to recursion.
        self._unilateral_compare = unilateral_compare
        self._include_equal_entries = include_equal_entries
        self._dir_comparison = {}
        self._visited = set()
        self._set_exclude_objects(excludes)

        # Call self._recursive_scandir_cmpr which is recursive function
        self._recursive_scandir_cmpr("")

    def _set_exclude_objects(self, excludes: Iterable[str] | None) -> None:
        """
        Used by compare_directories and expand_dirs to create regex_objects
        for exluding unwanted paths.
        """
        exclude_patterns = set(excludes) if excludes else set()
        self._exclude_objects = [
            re.compile(fnmatch.translate(exclude)) for exclude in exclude_patterns
        ]

    def expand_dirs(self, excludes: Iterable[str] | None = None) -> None:
        """
        Expands all unique directories found in the comparison results
        to include all nested items.

        This method iterates over unique directories in the comparison result.
        It recursively scans these directories, adding all nested files and
        subdirectories to the comparison results with their respective statuses
        set to UNIQUE. This provides a complete inventory of all items
        that do not have a counterpart in the other directory.

        Args:
            excludes (Iterable[str] | None): Optional. List of unix style patterns
                representing paths to ignore during dir expansion.

        Note:
            - This method should be called after `compare_directories` to ensure that there are
              comparison results to expand.
            - The method modifies the internal comparison results dictionary to include entries
              for all nested items within unique directories.
            - For most use cases you will want to use same excludes when
              calling this method as for the previous compare_directories call.
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

        # 2. Set initial state. These method variables is set as instance attributes
        # to minimize size of stack frames which might be important due to recursion.
        self._visited = set()
        self._set_exclude_objects(excludes)  # -> set self_exclude_objects

        # 3. Call _expand dir for all unique/mismatched dirs on both sides
        for dir1_dir in dir1_dirs:
            self._expand_dir(self._dir1, self._dir1_name, dir1_dir)

        for dir2_dir in dir2_dirs:
            self._expand_dir(self._dir2, self._dir2_name, dir2_dir)

    def _expand_dir(
        self,
        base_dir: str,
        base_dir_name: str,
        dir_rel_path: str,
    ) -> None:
        """
        This private method is utilized by `expand_dirs` to traverse unique
        directories identified in the initial comparison results.
        Recursively scans a specified directory, adding all nested files and subdirectories
        to the self._dir_comparison dict with their statuses set to UNIQUE.

        Args:
            base_dir (str): The base directory path from which the relative path starts.
            base_dir_name (str): The name used to represent the base directory in the
                                 self._dir_comparison dict.
            dir_rel_path (str): The relative path from the base directory to the directory
                                being expanded.

        Note:
            - This method directly modifies the internal comparison results structure,
              self._dir_comparison, adding entries under the provided `base_dir_name`.
            - It's designed to handle unique directories after an initial comparison,
              thus it does not perform any comparison itself but rather records all
              encountered items as UNIQUE within the context of their base directory.
        """
        dir_path = os.path.join(base_dir, dir_rel_path)
        dirs = []

        try:
            self._check_visited(dir_path)
            with os.scandir(dir_path) as dir_iterator:
                for dir_entry in dir_iterator:
                    entry_path = os.path.join(dir_rel_path, dir_entry.name)

                    # Check if entry_path is excluded by self._exclude_objects
                    if any(
                        re_obj.match(entry_path) for re_obj in self._exclude_objects
                    ):
                        continue

                    ftype = self._get_file_type(dir_entry)
                    self._add_dct_entry(
                        entry_path, base_dir_name, ftype, FileStatus.UNIQUE
                    )
                    if ftype == FileType.DIR:
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
        """
        Called by the compare_directories method. Recursively calls os.scandir for
        common dirs in self._dir1 and self._dir2. The actual dir comparison and
        the modification of the internal result dict, self._dir_comparison, is
        delegated to the _compare_dir_entries method. Nested common dirs
        where further recursive calls of this method are necessary are identified in
        the _compare_dir_entries method and returned to this method.

        Args:
            rel_path (str):
                The relative path from the base directories (self._dir1 and self._dir2).
                In the first call of this method this value will be "" but the
                value will be updated for each recursive call.

        Note:
            - Permission errors or inaccessible directories/files are skipped with a warning,
              and the method continues with the next items.
            - Infinite recursion due to symbolic links or circular references is prevented
              by maintaining a visited directory set (see _check_visited method).
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

        # Recursive relation.
        for common_dir in common_dirs:
            self._recursive_scandir_cmpr(common_dir)

    def _check_visited(self, dir_path: str) -> None:
        """
        Checks if a directory has already been visited to prevent infinite recursion
        during directory traversal. This method updates the `self._visited` set with
        the directory's unique identifier. On POSIX systems, this identifier is a combination
        of device and inode numbers. On Windows, it uses the file index number,
        as inode numbers are not available. If the directory has already been visited,
        it raises an InfiniteDirTraversalLoopError to halt the recursion.

        Args:
            dir_path (str): The path to the directory being checked.

        Raises:
            InfiniteDirTraversalLoopError: If the directory at `dir_path` has already
                                           been visited, indicating a potential infinite
                                           recursion in directory traversal.

        Note:
            The method utilizes os.stat() to retrieve the filesystem's unique identifiers.
            The specific attributes returned by os.stat(path).st_ino is different between
            linux and windows (platform specific).
        """
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
        """
        Called repeatedly by _recursive_scandir_cmpr, once for each directory pair
        that exists mutually in self._dir1 and self._dir2.

        Each call to this method:
        - Compares the files and subdirectories of a that directory pair.
            Delegates determination of file type to _get_file_type.
            Delegates determination of file status to _get_file_status.
        - Updates/modifies the internal comparison results dict, self._dir_comparison.
            The actual in place modification is delegated to _add_dct_entry method.
        - Returns new mutual directory pairs found up to _recursive_scandir_cmpr
            which will in turn call this method again until all
            mutual directory pairs are exhausted.

        Args:
            rel_path (str): The relative path from the base directories being compared.
                This is used to keep track of the current position in the directory tree.
            dir1_iterator (Iterator[os.DirEntry]): An iterator over the DirEntry:s in self._dir1.
            dir2_iterator (Iterator[os.DirEntry]): An iterator over the DirEntry:s in self._dir2.

        Returns:
            list[str]: A list of relative paths to common directories inside
                the 2 directories being compared.
        """
        # Set initial vars
        common_dirs = []
        dir2_entries_dict = {entry.name: entry for entry in dir2_iterator}

        # Iterate over and compare each dir1_entry
        # with the corresponding dir2_entry (if any)
        for dir1_entry in dir1_iterator:
            # Get corresponding dir2_entry
            dir2_entry = dir2_entries_dict.pop(dir1_entry.name, None)

            # Get rel path of DirEntry:s
            entry_path = os.path.join(rel_path, dir1_entry.name)

            # Check if entry_path is excluded by self._exclude_objects
            if any(re_obj.match(entry_path) for re_obj in self._exclude_objects):
                continue

            # Get FileType:s of DirEntry:s
            dir1_entry_type = self._get_file_type(dir1_entry)
            dir2_entry_type = self._get_file_type(dir2_entry)

            # Below if block evaluates and handles logic for different
            # type alignments between dir1_entry and dir2_entry
            if dir1_entry_type == dir2_entry_type:
                if dir1_entry_type == FileType.DIR:
                    # Both entries are dirs
                    common_dirs.append(entry_path)

                fstatus = self._get_file_status(dir1_entry, dir2_entry, dir1_entry_type)
                if (
                    FileStatus.EQUAL in fstatus or FileStatus.NOT_COMPARED in fstatus
                ) and not self._include_equal_entries:
                    continue
                key = self._mutual_key
            elif dir2_entry is None:
                # Unique dir1_entry
                fstatus = FileStatus.UNIQUE
                key = self._dir1_name
            else:
                # Not same type and dir2_entry is not None -> type mismatch
                fstatus = FileStatus.MISMATCHED
                key = self._dir1_name
                # Add mismatched entry to dir2 side as well (if not unilateral compare)
                if not self._unilateral_compare:
                    self._add_dct_entry(
                        entry_path, self._dir2_name, dir2_entry_type, fstatus
                    )

            # Add dir1_entry to result dict (self._dir_comparison)
            self._add_dct_entry(entry_path, key, dir1_entry_type, fstatus)

        # Add remaining (not popped) unique entries from dir2 to the result dict,
        # if not unilateral compare
        if not self._unilateral_compare:
            for unique_entry in dir2_entries_dict.values():
                # Check if entry_path is excluded by self._exclude_objects
                entry_path = os.path.join(rel_path, unique_entry.name)
                if any(re_obj.match(entry_path) for re_obj in self._exclude_objects):
                    continue

                ftype = self._get_file_type(unique_entry)
                self._add_dct_entry(
                    entry_path, self._dir2_name, ftype, FileStatus.UNIQUE
                )

        return common_dirs

    def _add_dct_entry(
        self,
        entry_path: str,
        dct_name: str,
        file_type: FileType,
        file_status: FileStatus,
    ) -> None:
        """
        This method adds an entry to the internal comparison results dict,
        self._dir_comparison. The position in the dict is determined by
        by the directory name, file type, and comparison status according to
        the following dict structure:

        {
            'dir1': {
                'file_typ1': {
                    # Note that a set is used as the innermost path container.
                    'file_status1': {rel_path1, rel_path2, etc},
                    'file_status2': {rel_path3, rel_path4, etc},
                },
                'file_typ2': {...}
            },
            'dir2': {...},
            'mutual': {...}
        }

        The keys for dir1 and dir2 defaults to 'dir1' and 'dir2' if not explicitly
        set by user on DirCompare instance creation (through __init__ method).
        Key order above is not guaranteed, can vary.

        Args:
            entry_path (str): The relative path of the entry.
            dct_name (str): The dictionary key representing the dir name (see above).
            file_type (FileType): The type of the file (e.g., FileType.FILE, FileType.DIR).
            file_status (FileStatus): The comparison status
                of the entry (e.g., FileStatus.UNIQUE, FileStatus.CHANGED).
        """
        main_dct = self._dir_comparison.setdefault(dct_name, {})
        type_dct = main_dct.setdefault(file_type, {})
        type_dct.setdefault(file_status, set()).add(entry_path)

    def _get_file_type(self, dir_entry: os.DirEntry | None) -> FileType | None:
        """
        This method examines a directory entry (such as a file, directory, or symlink)
        and returns its type as a member of the FileType enum. It leverages os.DirEntry's
        properties and in the case of special files additional system calls
        to accurately identify the file type.

        Args:
            dir_entry (os.DirEntry): The directory entry to examine.

        Returns:
            FileType: The type of the directory entry, as defined in the FileType enum.

        Note:
            - This method only follow symlinks if self._follow_symlinks == True.
                Otherwise returns FileType.SYMLINK.
            - If an OSError is encountered when performing a stat call it is caught,
                a warning is printed to the cli and FileType.UNKNOWN is returned.
        """
        if dir_entry is None:
            return None

        try:
            # Exhaust is_* methods first to avoid unneccessary system calls.
            if dir_entry.is_file(follow_symlinks=self._follow_symlinks):
                return FileType.FILE
            if not self._follow_symlinks:
                # Unfortunately follow_symlinks=False doesnt keep python from following junctions.
                # This therefore has to come before is_dir check.
                # Can only check for junctions in python 3.12 and above
                if (
                    hasattr(dir_entry, "is_junction")
                    and getattr(dir_entry, "is_junction")()
                ):
                    return FileType.JUNCTION
            if dir_entry.is_dir(follow_symlinks=self._follow_symlinks):
                return FileType.DIR
            if dir_entry.is_symlink():
                return FileType.SYMLINK

            stats = dir_entry.stat(follow_symlinks=self._follow_symlinks)
            mode = stat.S_IFMT(stats.st_mode)
            ftype = self.mode_to_filetype_map.get(mode, FileType.UNKNOWN)
        except OSError as exc:
            print(
                f"Error while trying to decide file type for {dir_entry}:\n"
                + f"{exc}\n"
                + "FileType set to UNKNOWN"
            )
            ftype = FileType.UNKNOWN

        return ftype

    def _get_file_status(
        self, dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, file_type: FileType
    ) -> FileStatus:
        """
        Determines the comparison status of two directory entries of equal type.
        This method delegates the comparison to a type-specific method based on the file_type.
        Currently, it only compares regular files and returns FileStatus.NOT_COMPARED
        for other types.

        Args:
            dir1_entry (os.DirEntry): The directory entry from the first directory.
            dir2_entry (os.DirEntry): The directory entry from the second directory.
            file_type (FileType): The type of the files to be compared.

        Returns:
            FileStatus: The comparison result.
        """
        if file_type == FileType.FILE:
            return self._get_regular_file_status(dir1_entry, dir2_entry)
        # Right now only files are compared
        return FileStatus.NOT_COMPARED

    @staticmethod
    def _get_regular_file_status(
        dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, tolerance: float = 2
    ) -> FileStatus:
        """
        Compares two regular files to determine if they are equal or have changed.
        The comparison is based on the modification times and sizes of the files.
        Files are considered equal if their sizes are identical
        and their modification times differ by no more than the specified tolerance.

        Args:
            dir1_entry (os.DirEntry): The directory entry representing the first file.
            dir2_entry (os.DirEntry): The directory entry representing the second file.
            tolerance (float): The maximum allowed difference in modification times (in seconds)
                               for the files to be considered equal.

        Returns:
            FileStatus: FileStatus.EQUAL if the files are deemed equal 
otherwise the FileStatus corresponding to the file changes, 
ex FileStatus.CHANGED | FileStatus.NEWER

        Note:
            - If an OSError occurs during the comparison (e.g., due to an inability to access
              file metadata), FileStatus.UNKNOWN is returned.
        """
        fstatus = FileStatus.CHANGED

        try:
            dir1_stats = dir1_entry.stat()
            dir2_stats = dir2_entry.stat()
            time_diff = abs(dir1_stats.st_mtime - dir2_stats.st_mtime)
            size_equal = dir1_stats.st_size == dir2_stats.st_size

            if time_diff <= tolerance:
                if size_equal:
                    return FileStatus.EQUAL
                # If not size_equal fstatus (which is == FileStatus.CHANGED)
                # will be returned further down
            elif dir1_stats.st_mtime > dir2_stats.st_mtime:
                fstatus |= FileStatus.NEWER
            else:
                fstatus |= FileStatus.OLDER

        except OSError:
            print(
                f"When comparing {dir1_entry.path} with {dir2_entry.path} "
                + "an OSError occured. Returning 'FileStatus.UNKNOWN'"
            )
            return FileStatus.UNKNOWN

        return fstatus
