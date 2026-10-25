"""Intégration Rugby TV (TOP 14 / PRO D2) pour Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import RugbyTvCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CARD_FILE = "rugby-tv-game-card.js"
CARD_URL = f"/{DOMAIN}_static/{CARD_FILE}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Expose la carte Lovelace embarquée et l'enregistre comme ressource."""
    www = Path(__file__).parent / "www" / CARD_FILE
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(www), cache_headers=False)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    await _async_register_card(hass, f"{CARD_URL}?v={integration.version}")
    return True


async def _async_register_card(hass: HomeAssistant, url: str) -> None:
    """Enregistre la carte comme ressource de tableau de bord (module JS).

    En mode « storage », la ressource est créée ou mise à jour dans la liste
    des ressources Lovelace. En mode YAML (liste non modifiable), on retombe
    sur le chargement par le frontend.
    """
    try:
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None)
        if resources is None and isinstance(lovelace, dict):
            resources = lovelace.get("resources")

        if resources is None or not hasattr(resources, "async_create_item"):
            add_extra_js_url(hass, url)
            return

        if not getattr(resources, "loaded", True):
            await resources.async_load()

        for item in resources.async_items():
            if item["url"].split("?")[0] == CARD_URL:
                if item["url"] != url:
                    await resources.async_update_item(
                        item["id"], {"res_type": "module", "url": url}
                    )
                return

        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception:  # noqa: BLE001
        _LOGGER.exception("rugby_tv : enregistrement de la carte impossible")
        add_extra_js_url(hass, url)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialisation d'une entrée (= un club)."""
    selected: dict = entry.data.get("selected", {})

    coordinator = RugbyTvCoordinator(hass, selected)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression d'une entrée."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """v1 (une entrée, plusieurs clubs) -> v2 (une entrée par club).

    - la 1re entrée garde le 1er club (ordre alphabetique) ;
    - les autres clubs sont retirés de cette entrée (entités supprimées du
      registre) puis recréés dans de nouvelles entrées, avec le même
      unique_id d'entité, donc les mêmes entity_id (sensor.rugby_<club>).
    """
    if entry.version == 1:
        selected: dict = dict(entry.data.get("selected", {}))
        if not selected:
            return False

        slugs = sorted(selected)
        keep, others = slugs[0], slugs[1:]

        ent_reg = er.async_get(hass)
        for slug in others:
            unique_id = f"rugbytv_{slug.replace('-', '_')}"
            entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
            if entity_id:
                ent_reg.async_remove(entity_id)

        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "selected": {keep: selected[keep]}},
            title=keep.replace("-", " ").title(),
            unique_id=keep,
            version=2,
        )

        for slug in others:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data={"slug": slug, "cfg": selected[slug]},
                )
            )

        _LOGGER.info("rugby_tv : migration v1 -> v2 (%d club(s) séparé(s))", len(others))

    return True
