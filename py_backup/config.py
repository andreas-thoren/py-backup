import json
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_PATH / "config.json"

def get_config(path): 
    return json.loads(str(path))

#CONFIG = json.loads(str(CONFIG_PATH))
#RSYNC_DEFAULTS = CONFIG["rsync"]["defaults"]
#ROBOCOPY_DEFAULTS = CONFIG["robocopy"]["defaults"]