import json
from ..clients import OllamaBackend
from ..models import AppConfig
import os
import logging
from pathlib import Path
from rich.logging import RichHandler

# Ensure all loggers in this module use RichHandler for colored console output
root_logger = logging.getLogger()
if not any(isinstance(h, RichHandler) for h in root_logger.handlers):
    rich_handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True, show_path=False)
    rich_handler.setLevel(logging.INFO)
    root_logger.addHandler(rich_handler)

class AppConstants:
    USER_HOME_DIR: str = os.path.expanduser('~/.jobops')
    DB_NAME: str = 'jobops.db'
    CONFIG_NAME: str = 'config.json'

CONSTANTS = AppConstants()

class JSONConfigManager:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._logger = logging.getLogger(self.__class__.__name__)

    def _migrate_config(self, old_data: dict) -> dict:
        """
        Migrate old config data to the new config structure.
        - Copies all existing fields.
        - Adds new required fields with sensible defaults if missing.
        - Prompts user for new required fields if needed (optional, currently uses defaults).
        """
        # Use AppConfig imported at the module top
        new_config = AppConfig().dict()
        # Copy over existing fields
        for k, v in old_data.items():
            if k in new_config and isinstance(new_config[k], dict) and isinstance(v, dict):
                # Merge dicts
                new_config[k].update(v)
            else:
                new_config[k] = v
        # Ensure all required fields are present
        # (If you want to prompt the user for missing required fields, add logic here)
        return new_config

    def load(self) -> AppConfig:
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                # Use AppConfig imported at the module top
                needs_migration = False
                default_config = AppConfig().dict()
                for key in default_config:
                    if key not in config_data:
                        needs_migration = True
                        break
                if needs_migration:
                    # Prompt user for migration confirmation
                    try:
                        import tkinter as tk
                        from tkinter import messagebox
                        root = tk.Tk()
                        root.withdraw()
                        answer = messagebox.askyesno(
                            "Config Migration Required",
                            "Your configuration file is outdated.\nDo you want to migrate to the new version?\nA backup will be created."
                        )
                        root.destroy()
                    except Exception:
                        answer = True  # fallback: always migrate if GUI not available
                    if not answer:
                        self._logger.warning("User cancelled config migration. Using old config for this session only.")
                        return AppConfig(**config_data)
                    # Backup old config
                    backup_path = self.config_path.with_suffix('.json.bak')
                    import shutil
                    shutil.copy2(self.config_path, backup_path)
                    migrated_data = self._migrate_config(config_data)
                    with open(self.config_path, 'w') as f:
                        json.dump(migrated_data, f, indent=2)
                    self._logger.info(f"Config migrated and backup created at {backup_path}")
                    return AppConfig(**migrated_data)
                else:
                    return AppConfig(**config_data)
            else:
                config = AppConfig()
                self.save(config)
                return config
        except Exception as e:
            self._logger.warning(f"Error loading config: {e}, using defaults")
            # Fallback to default AppConfig
            return AppConfig()
    
    def save(self, config: AppConfig) -> None:
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config.dict(), f, indent=2)
        except Exception as e:
            self._logger.error(f"Error saving config: {e}")