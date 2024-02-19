import platform
import doctest
import py_backup.syncers
import py_backup.utils

if __name__ == "__main__":
    if not platform.system() == "Linux":
        raise NotImplementedError("Doctests are written to be run from linux systems.")
    doctest.testmod(py_backup.syncers)
    doctest.testmod(py_backup.utils)
    # py_backup.comparer is not made for doctests
