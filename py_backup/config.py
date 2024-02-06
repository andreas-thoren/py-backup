import tomllib
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_PATH / "config.toml"

with CONFIG_PATH.open("rb") as f:
    CONFIG = tomllib.load(f)

RSYNC_DEFAULTS = CONFIG["defaults"]["rsync"]
ROBOCOPY_DEFAULTS = CONFIG["defaults"]["robocopy"]
