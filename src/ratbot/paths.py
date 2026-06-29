from pathlib import Path

from platformdirs import user_config_dir

CONFIG_DIRECTORY = Path(user_config_dir("ratbot", ensure_exists=True))
