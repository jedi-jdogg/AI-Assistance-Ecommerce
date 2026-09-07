"""Configuration loading. Everything tunable lives in config/agent.yaml + config/vendors.yaml."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class VendorRule:
    name: str
    lead_time_days: int
    moq_units: int = 1
    case_pack: int = 1
    preorder_ok: bool = False
    dropship: bool = False
    notes: str = ""


@dataclass
class Settings:
    raw: dict[str, Any]
    vendors: dict[str, VendorRule] = field(default_factory=dict)

    # --- convenience accessors -------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.raw
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def vendor(self, name: str | None) -> VendorRule:
        default_lt = int(self.get("purchasing.default_lead_time_days", 21))
        if name and name in self.vendors:
            return self.vendors[name]
        return VendorRule(name=name or "unknown", lead_time_days=default_lt)

    # --- environment ---------------------------------------------------------
    @property
    def shopify_shop(self) -> str:
        return os.environ.get("SHOPIFY_SHOP", self.get("store.myshopify", ""))

    @property
    def shopify_token(self) -> str:
        return os.environ.get("SHOPIFY_ACCESS_TOKEN", "")

    @property
    def shopify_api_version(self) -> str:
        return os.environ.get("SHOPIFY_API_VERSION", "2025-07")

    @property
    def klaviyo_key(self) -> str:
        return os.environ.get("KLAVIYO_API_KEY", "")

    @property
    def db_path(self) -> Path:
        return Path(os.environ.get("LINDAS_AGENT_DB", ROOT / "state" / "lindas_agent.sqlite"))


def load_settings(config_dir: Path | None = None) -> Settings:
    cfg_dir = config_dir or CONFIG_DIR
    raw = _load_yaml(cfg_dir / "agent.yaml")
    vendors_raw = _load_yaml(cfg_dir / "vendors.yaml").get("vendors", {})
    vendors = {
        name: VendorRule(
            name=name,
            lead_time_days=int(v.get("lead_time_days", raw.get("purchasing", {}).get("default_lead_time_days", 21))),
            moq_units=int(v.get("moq_units", 1)),
            case_pack=int(v.get("case_pack", 1)),
            preorder_ok=bool(v.get("preorder_ok", False)),
            dropship=bool(v.get("dropship", False)),
            notes=str(v.get("notes", "")),
        )
        for name, v in (vendors_raw or {}).items()
    }
    return Settings(raw=raw, vendors=vendors)
