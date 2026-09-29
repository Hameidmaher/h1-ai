"""Settings management — read/write config.production.yaml."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import structlog
import yaml

logger = structlog.get_logger()


class SettingsService:
    """Manage config.production.yaml safely."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default: ../config.production.yaml from backend/
            config_path = str(Path(__file__).parent.parent.parent / "config.production.yaml")
        self.config_path = Path(config_path)
        self._cache: Optional[dict] = None

    def load(self, force: bool = False) -> dict:
        """Load config from disk."""
        if self._cache is not None and not force:
            return self._cache

        if not self.config_path.exists():
            logger.warning("settings.config_missing", path=str(self.config_path))
            self._cache = {}
            return {}

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._cache = yaml.safe_load(f) or {}
        return self._cache

    def save(self, data: dict) -> bool:
        """Save config to disk with backup."""
        try:
            # Backup existing
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(
                    f".yaml.bak.{int(__import__('time').time())}"
                )
                shutil.copy2(self.config_path, backup_path)
                logger.info("settings.backup_created", path=str(backup_path))

            # Write new
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data, f, allow_unicode=True, sort_keys=False, default_flow_style=False
                )

            self._cache = data
            logger.info("settings.saved", path=str(self.config_path))
            return True
        except Exception as e:
            logger.error("settings.save_failed", error=str(e)[:200])
            return False

    # ─── WhatsApp ───
    def get_whatsapp(self) -> dict:
        """Get WhatsApp settings."""
        data = self.load()
        wa = data.get("whatsapp", {})
        return {
            "enabled": wa.get("enabled", False),
            "phone": wa.get("phone", ""),
            "display_phone": wa.get("display_phone", ""),
            "mode": wa.get("mode", "link"),
        }

    def update_whatsapp(self, updates: dict) -> dict:
        """Update WhatsApp settings."""
        data = self.load(force=True)
        if "whatsapp" not in data:
            data["whatsapp"] = {}

        allowed = {"enabled", "phone", "display_phone", "mode"}

        for key in allowed:
            if key in updates:
                data["whatsapp"][key] = updates[key]

        self.save(data)
        return self.get_whatsapp()


# Singleton
settings_service = SettingsService()
