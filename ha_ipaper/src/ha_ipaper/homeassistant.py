import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    def __init__(self, url: str, token: str):
        self._url = url.rstrip("/")
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    # ------------------------------------------------------------------
    # States
    # ------------------------------------------------------------------

    async def get_states(self, entities_filter: list[str] | None = None) -> dict:
        """
        Ritorna un dizionario {entity_id: state_dict}.

        Se entities_filter è specificato, recupera ogni entità
        individualmente con GET /api/states/<entity_id>  (molto più
        leggero per browser e-ink con tante entità).

        Se entities_filter è None o vuota, usa il comportamento originale
        GET /api/states  (carica TUTTO).
        """
        assert self._session is not None, "Usare come context manager (async with)"

        if entities_filter:
            return await self._get_states_filtered(entities_filter)
        else:
            return await self._get_states_all()

    async def _get_states_all(self) -> dict:
        """Carica tutte le entità - comportamento originale."""
        logger.debug("Fetching ALL states from Home Assistant")
        async with self._session.get(
            f"{self._url}/api/states",
            headers=self._headers,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            states = {s["entity_id"]: s for s in data}
            logger.info("Loaded %d entities from Home Assistant", len(states))
            return states

    async def _get_states_filtered(self, entity_ids: list[str]) -> dict:
        """
        Carica solo le entità specificate, una richiesta per entità,
        eseguite in parallelo con asyncio.gather per velocità.
        """
        logger.debug(
            "Fetching %d filtered entities from Home Assistant", len(entity_ids)
        )

        async def fetch_one(entity_id: str) -> tuple[str, dict | None]:
            try:
                async with self._session.get(
                    f"{self._url}/api/states/{entity_id}",
                    headers=self._headers,
                ) as resp:
                    if resp.status == 200:
                        state = await resp.json()
                        return entity_id, state
                    else:
                        logger.warning(
                            "Entity '%s' not found (HTTP %d)", entity_id, resp.status
                        )
                        return entity_id, None
            except Exception as exc:
                logger.error("Error fetching entity '%s': %s", entity_id, exc)
                return entity_id, None

        results = await asyncio.gather(*[fetch_one(eid) for eid in entity_ids])
        states = {eid: state for eid, state in results if state is not None}
        logger.info(
            "Loaded %d/%d filtered entities from Home Assistant",
            len(states),
            len(entity_ids),
        )
        return states

    # ------------------------------------------------------------------
    # Services (call / POST)
    # ------------------------------------------------------------------

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict | None = None,
    ) -> list[dict]:
        """Chiama un servizio Home Assistant e ritorna gli stati cambiati."""
        assert self._session is not None

        url = f"{self._url}/api/services/{domain}/{service}"
        payload = data or {}
        logger.debug("Calling service %s.%s with %s", domain, service, payload)

        async with self._session.post(
            url, headers=self._headers, json=payload
        ) as resp:
            resp.raise_for_status()
            changed = await resp.json()
            logger.debug("Service %s.%s changed %d states", domain, service, len(changed))
            return changed

    # ------------------------------------------------------------------
    # Forecast / weather (helper usato dal componente forecast.html)
    # ------------------------------------------------------------------

    async def get_weather_forecast(
        self, entity_id: str, forecast_type: str = "daily"
    ) -> list[dict]:
        """
        Ottiene le previsioni meteo tramite il servizio
        weather.get_forecasts (HA >= 2023.9).
        """
        assert self._session is not None

        try:
            changed = await self.call_service(
                "weather",
                "get_forecasts",
                {"entity_id": entity_id, "type": forecast_type},
            )
            # La risposta è una lista di stati; il primo dovrebbe essere weather
            for state in changed:
                if state.get("entity_id") == entity_id:
                    return (
                        state.get("attributes", {})
                        .get("forecast", [])
                    )
        except Exception as exc:
            logger.error("Error fetching weather forecast: %s", exc)
        return []
