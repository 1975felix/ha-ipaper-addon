# HA-IPaper Add-on per Home Assistant

Dashboard interattiva per display e-paper (Kobo, Kindle, ecc.) come add-on nativo di Home Assistant.

[![Installa Add-on](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/tuousername/ha-ipaper-addon)

---

## Installazione

### Metodo 1 — un click (raccomandato)
Clicca il badge qui sopra, oppure:

1. Vai su **Impostazioni → Add-on → Store add-on** (icona ⋮ in alto a destra)
2. Clicca **"Aggiungi repository"**
3. Inserisci: `https://github.com/tuousername/ha-ipaper-addon`
4. Cerca **"HA-IPaper Dashboard"** e clicca **Installa**

### Metodo 2 — manuale
```
Impostazioni → Add-on → Store add-on → ⋮ → Aggiungi repository
→ https://github.com/tuousername/ha-ipaper-addon
```

---

## Configurazione

Dopo l'installazione, vai nella tab **Configurazione** dell'add-on:

```yaml
# Token di accesso a HA (opzionale - se vuoto usa il token Supervisor automatico)
# Lascia vuoto per la maggior parte dei casi
homeassistant_token: ""

# Fuso orario per l'orario mostrato in dashboard
timezone: "Europe/Rome"

# Lista delle entità da mostrare (SOLO queste vengono scaricate da HA)
# Questo risolve il problema del crash del browser e-ink con troppe entità
entities_filter:
  - sensor.temperatura_soggiorno
  - sensor.umidita_bagno
  - light.soggiorno
  - light.cucina
  - switch.presa_ufficio
  - climate.termostato
  - cover.tapparella_soggiorno
  - weather.casa

# Configurazione menu (pagine della dashboard)
menu:
  - name: "Home"
    icon_id: "house"
    components:
      - "components/forecast.html"
      - "components/sensors.html"
  - name: "Luci"
    icon_id: "lightbulb"
    components:
      - "components/lights.html"
  - name: "Clima"
    icon_id: "air-conditioner"
    components:
      - "components/climates.html"
  - name: "Tende"
    icon_id: "shutters"
    components:
      - "components/covers.html"
  - name: "Switch"
    icon_id: "toggle-on"
    components:
      - "components/switches.html"
  - name: "Debug"
    icon_id: "bug"
    components:
      - "debug.html"

debug: false
```

### Come trovare gli entity_id
- **HA → Strumenti per sviluppatori → Stati** — cerca per nome o dominio
- **Aggiungi la pagina Debug** al menu (come nell'esempio sopra) — mostra tutti gli entity_id caricati

### Icon_id disponibili
| icon_id | Icona |
|---------|-------|
| `house` | 🏠 Casa |
| `lightbulb` | 💡 Lampadina |
| `air-conditioner` | ❄️ Aria condizionata |
| `temperature-half` | 🌡️ Temperatura |
| `shutters` | 🪟 Tapparelle |
| `toggle-on` | 🔘 Switch |
| `bug` | 🐛 Debug |

---

## Utilizzo

1. Avvia l'add-on dalla tab **Info**
2. Apri il browser del Kobo/Kindle e vai su `http://<IP-di-HA>:8081`
3. La dashboard si aggiorna ad ogni navigazione tra le pagine

### Kobo — configurazione consigliata
- Usa **NickelMenu** per aprire il browser in modalità fullscreen
- Impedisci il deep sleep mentre la pagina è aperta
- Imposta la pagina home del browser a `http://<IP>:8081`

---

## Template personalizzati

Puoi sovrascrivere i template predefiniti salvando file nella cartella `/addon_configs/ha_ipaper/html-template/`:

```
/addon_configs/ha_ipaper/
└── html-template/
    ├── components/
    │   └── sensors.html    ← sovrascrive il default
    └── style.css           ← sovrascrive il CSS
```

I file in questa cartella hanno priorità su quelli built-in.

---

## Note tecniche

- Il server gira sulla porta **8081** dentro HA
- Usa l'**API interna del Supervisor** (`http://supervisor/core`) — nessuna configurazione di rete richiesta
- Ogni entità viene richiesta individualmente con `GET /api/states/<entity_id>` in parallelo, invece di scaricare tutto lo stato di HA
- I template sono Jinja2 con accesso alla variabile `entities` (dizionario `{entity_id: state_dict}`)
