import unittest
from unittest.mock import Mock
from py_backup.core import folder_backup


def get_mock_func() -> callable:
    mock_backup_func = Mock(name='MockedFunction')
    mock_backup_func.__name__ = 'MockedFunction'
    return mock_backup_func


class TestCore(unittest.TestCase):
    def test_folder_backup_valid(self):
        mock_func = get_mock_func()
        source = "tests/folder1"
        destination = "tests/folder2"
        folder_backup(mock_func, source, destination)
        mock_func.assert_called_once()

    def test_folder_backup_invalid_source(self):
        mock_func = get_mock_func()
        source = "tests/non_existent_folder"
        destination = "tests/folder2"
        with self.assertRaises(ValueError):
            folder_backup(mock_func, source, destination)

    def test_folder_backup_invalid_destination(self):
        mock_func = get_mock_func()
        source = "tests/folder1"
        destination = "tests/non_existent_folder"
        with self.assertRaises(ValueError):
            folder_backup(mock_func, source, destination)
