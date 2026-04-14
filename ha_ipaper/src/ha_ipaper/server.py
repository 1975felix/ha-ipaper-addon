from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response as FResponse
from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from .config import AppConfig
from .homeassistant import HomeAssistantClient

logger = logging.getLogger(__name__)

# Cartella dei template inclusi nel package
_BUILTIN_TEMPLATES = Path(__file__).parent / "html-template"


def create_app(cfg: AppConfig) -> FastAPI:
    app = FastAPI(title="HA-IPaper (filtered fork)")

    # -----------------------------------------------------------------
    # Jinja2: priorità template utente > builtin
    # -----------------------------------------------------------------
    loaders = []
    for tmpl_dir in cfg.general.html_templates:
        p = Path(tmpl_dir)
        if p.is_dir():
            loaders.append(FileSystemLoader(str(p)))
            logger.debug("Template dir (user): %s", p)
        else:
            logger.warning("Template dir not found, skipping: %s", p)
    loaders.append(FileSystemLoader(str(_BUILTIN_TEMPLATES)))
    logger.debug("Template dir (builtin): %s", _BUILTIN_TEMPLATES)

    jinja_env = Environment(
        loader=ChoiceLoader(loaders),
        autoescape=True,
        auto_reload=cfg.server.debug,
    )
    # Rendi enumerate disponibile nei template
    jinja_env.globals["enumerate"] = enumerate

    # -----------------------------------------------------------------
    # Static files: CSS, webfonts, icone SVG
    # Route custom con fallback: user template dir → builtin
    # -----------------------------------------------------------------

    async def _serve_static(filepath: str):
        """Cerca il file prima nelle cartelle utente, poi nel builtin."""
        # Sanitizza path traversal
        safe = filepath.lstrip("/").replace("..", "")

        search_dirs = []
        for tmpl_dir in cfg.general.html_templates:
            p = Path(tmpl_dir)
            if p.is_dir():
                search_dirs.append(p)
        search_dirs.append(_BUILTIN_TEMPLATES)

        for d in search_dirs:
            candidate = d / safe
            if candidate.is_file():
                return FileResponse(str(candidate))

        return FResponse(status_code=404, content=b"Not found")

    @app.get("/static/{filepath:path}")
    async def static_files(filepath: str, request: Request):
        # Compatibilita col formato originale: webfonts/regular.svg?id=house
        icon_id = request.query_params.get("id")
        if icon_id and "regular.svg" in filepath:
            return await _serve_static(f"webfonts/{icon_id}.svg")
        return await _serve_static(filepath)

    # -----------------------------------------------------------------
    # Helper: costruisce il contesto comune per i template
    # -----------------------------------------------------------------
    async def _build_context(request: Request) -> dict:
        entities_filter = cfg.general.entities_filter

        async with HomeAssistantClient(
            cfg.general.homeassistant_url,
            cfg.general.homeassistant_token,
        ) as ha:
            entities = await ha.get_states(entities_filter=entities_filter)

        try:
            tz = ZoneInfo(cfg.general.timezone)
        except Exception:
            tz = ZoneInfo("UTC")

        now = datetime.now(tz).strftime("%d/%m/%Y %H:%M")

        return {
            "request": request,
            "entities": entities,
            "menu": cfg.menu,
            "config": cfg,
            "now": now,
        }

    # -----------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------

    @app.get("/", response_class=RedirectResponse)
    async def root():
        return RedirectResponse(url="/page/0")

    @app.get("/page/{page_index}", response_class=HTMLResponse)
    async def render_page(request: Request, page_index: int = 0):
        try:
            ctx = await _build_context(request)
        except Exception as exc:
            logger.error("Failed to fetch HA states: %s", exc)
            return HTMLResponse(
                content=f"<h1>Errore connessione Home Assistant</h1><pre>{exc}</pre>",
                status_code=503,
            )

        # Determina quale pagina del menu renderizzare
        menu = cfg.menu
        if not menu:
            return HTMLResponse("<h1>Nessun menu configurato nel config.yaml</h1>")

        page_index = max(0, min(page_index, len(menu) - 1))
        ctx["current_page"] = page_index
        ctx["current_menu"] = menu[page_index]

        # Renderizza i component della pagina
        components_html = []
        for component_path in menu[page_index].components:
            try:
                tmpl = jinja_env.get_template(component_path)
                components_html.append(tmpl.render(**ctx))
            except Exception as exc:
                logger.error("Error rendering component '%s': %s", component_path, exc)
                components_html.append(
                    f"<p class='error'>Errore componente {component_path}: {exc}</p>"
                )

        ctx["components_html"] = "\n".join(components_html)

        try:
            tmpl = jinja_env.get_template("index.html")
            html = tmpl.render(**ctx)
        except Exception as exc:
            logger.error("Error rendering index.html: %s", exc)
            return HTMLResponse(
                content=f"<h1>Errore rendering</h1><pre>{exc}</pre>",
                status_code=500,
            )

        return HTMLResponse(content=html)

    @app.post("/service", response_class=RedirectResponse)
    async def call_service(request: Request):
        """
        Gestisce i form HTML per chiamare servizi HA.
        Atteso: service=domain.service_name + altri campi = parametri servizio.
        Dopo la chiamata reindirizza alla pagina corrente.
        """
        form = await request.form()
        data = dict(form)

        service_full = data.pop("service", None)
        entity_id = data.pop("entity_id", None)
        redirect_page = data.pop("_page", "0")

        if not service_full or "." not in service_full:
            logger.warning("Invalid service call: %s", service_full)
            return RedirectResponse(url=f"/page/{redirect_page}", status_code=303)

        domain, service_name = service_full.split(".", 1)
        payload: dict = {}
        if entity_id:
            payload["entity_id"] = entity_id
        payload.update(data)  # temperatura, brightness, ecc.

        try:
            async with HomeAssistantClient(
                cfg.general.homeassistant_url,
                cfg.general.homeassistant_token,
            ) as ha:
                await ha.call_service(domain, service_name, payload)
            logger.info("Service %s called successfully", service_full)
        except Exception as exc:
            logger.error("Service call failed: %s", exc)

        return RedirectResponse(url=f"/page/{redirect_page}", status_code=303)

    return app
