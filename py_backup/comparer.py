import os
import stat
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
    # Currently only EQUAL, CHANGED is used in the application
    EQUAL = auto()
    CHANGED = auto()
    NEWER = auto()
    OLDER = auto()


class InfiniteDirTraversalLoopError(Exception):
    """
    Exception raised when an infinite loop is detected due to symlinks/junctions
    during directory traversal.
    """
    def __init__(self, path, msg="Infinite traversal loop detected while traversing directories!"):
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

        # TODO add check that dir1 != dir2 and dir1_name != dir2_name
        # Useful for testing purpuses. Will wait.
        self.dir1_name = dir1_name
        self.dir2_name = dir2_name
        self._unilateral_compare = False
        self._follow_symlinks = False
        self._visited = None # Will be a set
        self.dir_comparison = {}

    @property
    def dir1(self) -> str:
        return self._dir1

    @property
    def dir2(self) -> str:
        return self._dir2

    def get_comparison_result(self) -> str:
        keys = sorted(list(self.dir_comparison))
        result = ""

        for key in keys:
            result += f"\n{key.upper().replace('_', ' ')}:\n"
            values = "\n".join(self.dir_comparison[key])
            result += f"{values}\n"

        return f"{result}"

    def compare_directories(
        self, unilateral_compare: bool = False, follow_symlinks: bool = False
    ) -> dict[str : list[str]]:
        self._unilateral_compare = unilateral_compare
        self._follow_symlinks = follow_symlinks
        self.dir_comparison.clear()
        self._visited = set()
        self._recursive_scandir_cmpr("")
        return self.dir_comparison.copy()

    def _recursive_scandir_cmpr(self, rel_path: str) -> None:
        """Recursive function called exclusively by dir_compare.
        Works by recursing down (depth first) dirs by repeatedly calling os.scandir.
        """
        dir1_path = os.path.join(self._dir1, rel_path)
        dir2_path = os.path.join(self._dir2, rel_path)

        # TODO Measure overhead of code in if statement
        # If not to bad maybe always active for junctions?
        if self._follow_symlinks:
            try:
                # Check that dir1 is not previously visited
                stats1 = os.stat(dir1_path)
                dirkey1 = (stats1.st_dev, stats1.st_ino)
                if dirkey1 in self._visited:
                    raise InfiniteDirTraversalLoopError(path=dir1_path)
                self._visited.add(dirkey1)
                # Check that dir2 is not previously visited
                stats2 = os.stat(dir2_path)
                dirkey2 = (stats2.st_dev, stats2.st_ino)
                if dirkey2 in self._visited:
                    raise InfiniteDirTraversalLoopError(path=dir2_path)
                self._visited.add(dirkey2)
            except OSError as exc:
                print("Cannot protect against loops introduced by symlinks!")

        common_dirs = []  # Needed if _compare_dir_entries raises. Do not remove.
        try:
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
            dir1_entry_type = self.get_file_type(dir1_entry)
            dir2_entry_type = self.get_file_type(dir2_entry)

            # If dir2_entry_type is None below if statement evaluates to False
            if dir1_entry_type == dir2_entry_type and dir1_entry_type != FileType.DIR:
                status = self.get_file_status(dir1_entry, dir2_entry, dir1_entry_type)

                if status == FileStatus.CHANGED:
                    entry_rel_path = os.path.join(rel_path, dir1_entry.name)
                    key = f"changed_{dir1_entry_type.name.lower()}s"
                    self.dir_comparison.setdefault(key, []).append(entry_rel_path)
                continue

            entry_rel_path = os.path.join(rel_path, dir1_entry.name)
            if dir2_entry is None:
                # Unique dir1_entry
                key1 = f"{self.dir1_name}_unique_{dir1_entry_type.name.lower()}s"
                self.dir_comparison.setdefault(key1, []).append(entry_rel_path)
            elif dir1_entry_type != dir2_entry_type:
                # Type mismatch
                key1 = f"{self.dir1_name}_mismatched_{dir1_entry_type.name.lower()}s"
                self.dir_comparison.setdefault(key1, []).append(entry_rel_path)
                if not self._unilateral_compare:
                    key2 = (
                        f"{self.dir2_name}_mismatched_{dir2_entry_type.name.lower()}s"
                    )
                    self.dir_comparison.setdefault(key2, []).append(entry_rel_path)
            else:
                # Both entries are dirs
                common_dirs.append(entry_rel_path)

        if not self._unilateral_compare:
            for unique_entry in dir2_entries_dict.values():
                entry_type = self.get_file_type(unique_entry)
                entry_rel_path = os.path.join(rel_path, unique_entry.name)
                key = f"{self.dir2_name}_unique_{entry_type.name.lower()}s"
                self.dir_comparison.setdefault(key, []).append(entry_rel_path)

        return common_dirs

    def get_file_type(self, dir_entry: os.DirEntry | None) -> FileType | None:
        if dir_entry is None:
            return None

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
        return file_type

    def get_file_status(
        self, dir1_entry: os.DirEntry, dir2_entry: os.DirEntry, file_type: FileType
    ) -> FileType:
        if file_type == FileType.FILE:
            return self.get_regular_file_status(dir1_entry, dir2_entry)
        # Right now only files are compared all other types will compare as equal.
        return FileStatus.EQUAL

    @staticmethod
    def get_regular_file_status(
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

    def expand_nested_unique_dirs() -> None:
        # TODO should go through all unique dirs on both sides (in not unilateral_compare)
        # and add the nested items to the dir_comparison dict
        pass
