from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class GeneralConfig:
    homeassistant_url: str = "http://homeassistant.local:8123"
    homeassistant_token: str = ""
    timezone: str = "Europe/Rome"
    html_templates: list[str] = field(default_factory=lambda: [
        "/addon_configs/ha_ipaper/html-template",  # template utente (addon HA)
        "/data/html-template",                      # template utente (fallback)
    ])
    # Lista di entity_id da mostrare. Se vuota/None => carica TUTTO (comportamento originale).
    entities_filter: list[str] = field(default_factory=list)


@dataclass
class GraphConfig:
    days: int = 5


@dataclass
class ServerConfig:
    bind_addr: str = "0.0.0.0"
    bind_port: int = 8081
    debug: bool = False


@dataclass
class MenuItem:
    name: str
    icon: str
    components: list[str] = field(default_factory=list)

    @property
    def icon_id(self) -> str:
        """Estrae l'id dall'URL icona es. 'webfonts/regular.svg?id=house' → 'house'."""
        if "?id=" in self.icon:
            return self.icon.split("?id=", 1)[1]
        # fallback: usa il filename senza estensione
        return Path(self.icon).stem


@dataclass
class AppConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    menu: list[MenuItem] = field(default_factory=list)
    loggercfg: dict = field(default_factory=dict)


def _override_from_env(cfg: AppConfig) -> None:
    """Sovrascrive i campi con le variabili d'ambiente HA_IPAPER_GENERAL__*"""
    prefix = "HA_IPAPER_GENERAL__"
    mapping = {
        "homeassistant_url": str,
        "homeassistant_token": str,
        "timezone": str,
    }
    for key, cast in mapping.items():
        env_var = prefix + key
        val = os.environ.get(env_var)
        if val is not None:
            setattr(cfg.general, key, cast(val))
            logger.debug("Config override from env %s=%s", env_var, val)

    # entities_filter da env: lista separata da virgole
    ef_env = os.environ.get("HA_IPAPER_GENERAL__entities_filter")
    if ef_env:
        cfg.general.entities_filter = [e.strip() for e in ef_env.split(",") if e.strip()]


def load_config(path: str) -> AppConfig:
    cfg = AppConfig()

    try:
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Config file '%s' not found, using defaults", path)
        raw = {}

    # --- general ---
    g = raw.get("general", {})
    cfg.general.homeassistant_url = g.get("homeassistant_url", cfg.general.homeassistant_url)
    cfg.general.homeassistant_token = g.get("homeassistant_token", cfg.general.homeassistant_token)
    cfg.general.timezone = g.get("timezone", cfg.general.timezone)
    cfg.general.html_templates = g.get("html_templates", cfg.general.html_templates)
    cfg.general.entities_filter = g.get("entities_filter", cfg.general.entities_filter) or []

    # --- graph ---
    gr = raw.get("graph", {})
    cfg.graph.days = gr.get("days", cfg.graph.days)

    # --- server ---
    s = raw.get("server", {})
    cfg.server.bind_addr = s.get("bind_addr", cfg.server.bind_addr)
    cfg.server.bind_port = s.get("bind_port", cfg.server.bind_port)
    cfg.server.debug = s.get("debug", cfg.server.debug)

    # --- menu ---
    for item in raw.get("menu", []):
        cfg.menu.append(
            MenuItem(
                name=item.get("name", ""),
                icon=item.get("icon", ""),
                components=item.get("components", []),
            )
        )

    # --- logging ---
    cfg.loggercfg = raw.get("loggercfg", {})

    # Sovrascritture da variabili d'ambiente
    _override_from_env(cfg)

    # Normalizza: entities_filter vuota = nessun filtro
    if cfg.general.entities_filter == []:
        cfg.general.entities_filter = None

    logger.info(
        "Config loaded: HA=%s  entities_filter=%s",
        cfg.general.homeassistant_url,
        f"{len(cfg.general.entities_filter)} entities"
        if cfg.general.entities_filter
        else "ALL (no filter)",
    )
    return cfg
