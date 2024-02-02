import json
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_PATH / "config.json"

with CONFIG_PATH.open("r") as f:
    CONFIG = json.load(f)

RSYNC_DEFAULTS = CONFIG["defaults"]["rsync"]
ROBOCOPY_DEFAULTS = CONFIG["defaults"]["robocopy"]
