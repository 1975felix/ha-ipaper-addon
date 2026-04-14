#!/bin/bash
set -e

echo "Avvio HA-IPaper Dashboard..."

# Leggi options.json scritto da HA
python3 - << 'PYEOF'
import json, yaml, os

with open("/data/options.json") as f:
    opts = json.load(f)

token = opts.get("homeassistant_token", "").strip()
if not token:
    token = os.environ.get("SUPERVISOR_TOKEN", "")

entities_filter = [
    e.strip() for e in opts.get("entities_filter", [])
    if e.strip() and e.strip() != "sensor.example_temperature"
]

MENU_FILE = "/addon_configs/ha_ipaper/menu.yaml"
DEFAULT_MENU = [
    {"name": "Home",   "icon": "webfonts/regular.svg?id=house",
     "components": ["components/forecast.html", "components/sensors.html"]},
    {"name": "Luci",   "icon": "webfonts/regular.svg?id=lightbulb",
     "components": ["components/lights.html"]},
    {"name": "Clima",  "icon": "webfonts/regular.svg?id=air-conditioner",
     "components": ["components/climates.html"]},
    {"name": "Tende",  "icon": "webfonts/regular.svg?id=shutters",
     "components": ["components/covers.html"]},
    {"name": "Switch", "icon": "webfonts/regular.svg?id=toggle-on",
     "components": ["components/switches.html"]},
    {"name": "Debug",  "icon": "webfonts/regular.svg?id=bug",
     "components": ["debug.html"]},
]

if os.path.exists(MENU_FILE):
    with open(MENU_FILE) as f:
        menu = yaml.safe_load(f) or DEFAULT_MENU
else:
    menu = DEFAULT_MENU

config = {
    "general": {
        "homeassistant_url": "http://supervisor/core",
        "homeassistant_token": token,
        "timezone": opts.get("timezone", "Europe/Rome"),
        "html_templates": ["/addon_configs/ha_ipaper/html-template"],
        "entities_filter": entities_filter if entities_filter else None,
    },
    "server": {
        "bind_addr": "0.0.0.0",
        "bind_port": 8081,
        "debug": opts.get("debug", False),
    },
    "menu": menu,
}

with open("/data/server_config.yaml", "w") as f:
    yaml.dump(config, f, allow_unicode=True)

n = len(entities_filter) if entities_filter else "TUTTE"
print(f"Config scritto. Entita: {n}  Menu: {[m['name'] for m in menu]}")
PYEOF

echo "Server in avvio sulla porta 8081..."
exec python3 -m ha_ipaper -config /data/server_config.yaml
