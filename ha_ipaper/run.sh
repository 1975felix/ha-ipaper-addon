#!/usr/bin/with-contenv bashio
# ==============================================================================
# HA-IPaper Add-on - Script di avvio
#
# bashio è il framework shell degli add-on HA.
# Legge /data/options.json e lo converte in variabili d'ambiente.
# L'URL di Home Assistant e il token Supervisor sono già disponibili
# tramite le variabili SUPERVISOR_TOKEN e l'API interna.
# ==============================================================================

set -e

bashio::log.info "Avvio HA-IPaper Dashboard..."

# ---------------------------------------------------------
# Leggi le opzioni dal pannello HA (da /data/options.json)
# ---------------------------------------------------------

# Token per le chiamate REST API a HA.
# Se l'utente non ne ha fornito uno custom, usa il Supervisor token
# che ha accesso completo all'API interna di HA.
if bashio::config.has_value "homeassistant_token"; then
    HA_TOKEN=$(bashio::config "homeassistant_token")
    bashio::log.info "Uso token personalizzato dall'utente"
else
    # Il Supervisor token funziona con http://supervisor/core/api
    HA_TOKEN="${SUPERVISOR_TOKEN}"
    bashio::log.info "Uso Supervisor token automatico"
fi

TIMEZONE=$(bashio::config "timezone")
DEBUG=$(bashio::config "debug")

bashio::log.info "Timezone: ${TIMEZONE}"
bashio::log.info "Debug: ${DEBUG}"

# ---------------------------------------------------------
# Costruisci il config.yaml per il server Python
# leggendo tutte le opzioni da /data/options.json
# ---------------------------------------------------------

# Determina l'URL di HA: dentro il container HA usa l'API del Supervisor
HA_URL="http://supervisor/core"

CONFIG_FILE="/data/server_config.yaml"

bashio::log.info "Generazione config in ${CONFIG_FILE}..."

python3 - << PYEOF
import json, yaml, os

with open("/data/options.json") as f:
    opts = json.load(f)

# Token: custom o Supervisor
token = opts.get("homeassistant_token", "").strip()
if not token:
    token = os.environ.get("SUPERVISOR_TOKEN", "")

entities_filter = opts.get("entities_filter", [])
# Rimuovi eventuali stringhe vuote o placeholder
entities_filter = [e.strip() for e in entities_filter
                   if e.strip() and e.strip() != "sensor.example_temperature"]

menu_raw = opts.get("menu", [])
menu = []
for item in menu_raw:
    menu.append({
        "name": item.get("name", ""),
        # Converte icon_id nel formato compatibile col template
        "icon": f"webfonts/regular.svg?id={item.get('icon_id', 'house')}",
        "components": item.get("components", []),
    })

config = {
    "general": {
        "homeassistant_url": "http://supervisor/core",
        "homeassistant_token": token,
        "timezone": opts.get("timezone", "Europe/Rome"),
        "html_templates": ["/data/html-template"],
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

print(f"Config scritto. Entità filtrate: {len(entities_filter) if entities_filter else 'TUTTE'}")
print(f"Menu: {[m['name'] for m in menu]}")
PYEOF

bashio::log.info "Avvio server Python sulla porta 8081..."

exec python3 -m ha_ipaper -config "${CONFIG_FILE}"
