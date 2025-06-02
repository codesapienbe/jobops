import json
from jobops.clients import OllamaBackend
from jobops.models import AppConfig
from dataclasses import dataclass
import os
import logging
from pathlib import Path
from typing import Protocol

class ConfigManager(Protocol):
    def load(self) -> AppConfig: ...
    def save(self, config: AppConfig) -> None: ...


class AppConstants:
    APP_NAME: str = 'Motivation Letter Generator'
    VERSION: str = '1.0.0'
    USER_HOME_DIR: str = os.path.expanduser('~/.jobops')
    MOTIVATIONS_DIR: str = os.path.expanduser('~/.jobops/motivations')
    WINDOW_SIZE: str = "600x200"
    ICON_SIZE: tuple = (64, 64)
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
        # Import AppConfig for defaults
        from . import AppConfig
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
                from . import AppConfig
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
                    try:
                        from . import SystemNotificationService
                        SystemNotificationService().notify("JobOps", f"Config migrated. Backup saved as {backup_path.name}.")
                    except Exception:
                        pass
                    return AppConfig(**migrated_data)
                else:
                    return AppConfig(**config_data)
            else:
                config = AppConfig()
                self.save(config)
                return config
        except Exception as e:
            self._logger.warning(f"Error loading config: {e}, using defaults")
            return OllamaBackend
    
    def save(self, config: AppConfig) -> None:
        try:
            self.coOpenAIBackendent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config.dict(), f, indent=2)
        except Exception as e:
            self._logger.error(f"Error saving config: {e}")