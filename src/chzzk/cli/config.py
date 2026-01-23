"""Configuration management for CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manages CLI configuration and cookies.

    Configuration is stored in ~/.chzzk/ directory.
    - config.json: General settings
    - cookies.json: Naver authentication cookies
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".chzzk"
    CONFIG_FILE = "config.json"
    COOKIES_FILE = "cookies.json"

    # Environment variable names
    ENV_NID_AUT = "CHZZK_NID_AUT"
    ENV_NID_SES = "CHZZK_NID_SES"
    ENV_LOG_LEVEL = "CHZZK_LOG_LEVEL"

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Custom configuration directory. Defaults to ~/.chzzk/
        """
        self._config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self._config_file = self._config_dir / self.CONFIG_FILE
        self._cookies_file = self._config_dir / self.COOKIES_FILE

    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict[str, Any]:
        """Read JSON file, return empty dict if not exists."""
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        """Write data to JSON file."""
        self._ensure_config_dir()
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_config(self) -> dict[str, Any]:
        """Get general configuration."""
        return self._read_json(self._config_file)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        config = self.get_config()
        config[key] = value
        self._write_json(self._config_file, config)

    def get_cookies(self) -> dict[str, str]:
        """Get stored cookies."""
        return self._read_json(self._cookies_file)

    def save_cookies(self, nid_aut: str, nid_ses: str) -> None:
        """Save authentication cookies.

        Args:
            nid_aut: NID_AUT cookie value.
            nid_ses: NID_SES cookie value.
        """
        cookies = {
            "NID_AUT": nid_aut,
            "NID_SES": nid_ses,
        }
        self._write_json(self._cookies_file, cookies)

    def delete_cookies(self) -> None:
        """Delete stored cookies."""
        if self._cookies_file.exists():
            self._cookies_file.unlink()

    def get_auth_cookies(
        self,
        cli_nid_aut: str | None = None,
        cli_nid_ses: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Get authentication cookies with priority.

        Priority order:
        1. CLI options (cli_nid_aut, cli_nid_ses)
        2. Environment variables (CHZZK_NID_AUT, CHZZK_NID_SES)
        3. Stored cookies (cookies.json)

        Args:
            cli_nid_aut: NID_AUT from CLI option.
            cli_nid_ses: NID_SES from CLI option.

        Returns:
            Tuple of (nid_aut, nid_ses) values.
        """
        # Priority 1: CLI options
        nid_aut = cli_nid_aut
        nid_ses = cli_nid_ses

        # Priority 2: Environment variables
        if not nid_aut:
            nid_aut = os.environ.get(self.ENV_NID_AUT)
        if not nid_ses:
            nid_ses = os.environ.get(self.ENV_NID_SES)

        # Priority 3: Stored cookies
        if not nid_aut or not nid_ses:
            stored = self.get_cookies()
            if not nid_aut:
                nid_aut = stored.get("NID_AUT")
            if not nid_ses:
                nid_ses = stored.get("NID_SES")

        return nid_aut, nid_ses

    def get_log_level(self, cli_log_level: str | None = None) -> str:
        """Get log level with priority.

        Priority order:
        1. CLI option
        2. Environment variable (CHZZK_LOG_LEVEL)
        3. Default (WARNING)

        Args:
            cli_log_level: Log level from CLI option.

        Returns:
            Log level string.
        """
        if cli_log_level:
            return cli_log_level.upper()

        env_level = os.environ.get(self.ENV_LOG_LEVEL)
        if env_level:
            return env_level.upper()

        return "WARNING"

    def has_stored_cookies(self) -> bool:
        """Check if cookies are stored."""
        cookies = self.get_cookies()
        return bool(cookies.get("NID_AUT") and cookies.get("NID_SES"))
