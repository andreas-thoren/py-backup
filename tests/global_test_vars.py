from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent / "test_dirs"
assert TEST_DATA_DIR.is_dir()

DESTINATION = TEST_DATA_DIR / "destination"
SOURCE = TEST_DATA_DIR / "source"
NON_EXISTING_DIR = TEST_DATA_DIR / "not_exist_dir"
assert DESTINATION.is_dir()
assert SOURCE.is_dir()
assert not NON_EXISTING_DIR.exists()