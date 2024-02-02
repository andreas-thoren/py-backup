# py-backup

## Overview
This Python project provides a common interface for file synchronization and backup across different platforms. Designed to be cross-platform by leveraging `rsync` for UNIX/Linux and `robocopy` for Windows. It's developed with Python 3.10+, ensuring compatibility with the latest language features and improvements.

## Disclaimer
Please note that this project is currently in early alpha stage. It is under active development, and while it is functional, bugs and issues are to be expected. I welcome bug reports and contributions to help improve the project. Use it at your own risk.

## Features
- Cross-platform file synchronization using `rsync` and `robocopy`.
- Customizable through a straightforward JSON configuration.
- Includes both a functional interface and a class-based interface for flexibility in usage.

### Prerequisites
- Python 3.10+
- `rsync` on UNIX/Linux or `robocopy` on Windows.

### Installation
Clone the repository and install the package using pip. There are no external dependencies, making it straightforward to set up and use.

### Configuration
Adjust `config.json` to fine-tune synchronization settings for your needs, with detailed options for both `rsync` and `robocopy`.

## Usage
- For simple tasks, use the functional interface provided by `utils.py`, accessible directly through the package's `__init__.py`.
- For more complex synchronization needs, the class-based interface in `syncers.py` offers detailed control.

### Examples
```python
# Functional interface
from py_backup import folder_backup

folder_backup("src_folder", "dst_folder", delete=False, backup="backup_folder")

# Object oriented interface
from py_backup.syncers import Rsync
 
syncer = Rsync("src_folder", "dst_folder")
opts = ["-a", "-P"]
kwargs = {"text": True, "capture_output": True}
syncer.sync(
    delete=False, dry_run=False, backup=backup_dir, options=opts, subprocess_kwargs=kwargs
)
```

## Extending the Program
To extend the program by adding another concrete class implementation of `SyncABC`:
1. Define your class in `syncers.py`, ensuring it inherits from `SyncABC`.
2. Implement the required methods, providing functionality specific to the new synchronization method or platform.
3. Add any necessary configuration options to `config.json`.

## Contributing
Contributions are welcome. Please follow standard coding practices and submit pull requests for any enhancements.

## License
This project is licensed under the MIT License. For license terms, see the LICENSE file in the project root folder.
