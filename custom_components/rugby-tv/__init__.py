"""Intégration Rugby LNR (TOP 14 / PRO D2) pour Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RugbyLnrCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CARD_FILENAME = "rugby-lnr-game-card.js"
CARD_URL_PATH = f"/{DOMAIN}_card"
CARD_VERSION = "0.1.0"


async def _async_register_card(hass: HomeAssistant) -> None:
    """Enregistre la carte Lovelace fournie avec l'intégration (une seule fois)."""
    if hass.data.get(f"{DOMAIN}_card_registered"):
        return

    card_path = Path(__file__).parent / "www" / CARD_FILENAME
    url = f"{CARD_URL_PATH}/{CARD_FILENAME}"

    try:
        # HA récent (>= 2024.7)
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(url, str(card_path), cache_headers=False)]
        )
    except ImportError:
        # HA plus ancien
        hass.http.register_static_path(url, str(card_path), cache_headers=False)

    add_extra_js_url(hass, f"{url}?v={CARD_VERSION}")
    hass.data[f"{DOMAIN}_card_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialisation de l'intégration."""
    selected: dict = entry.data.get("selected", {})

    coordinator = RugbyLnrCoordinator(hass, selected)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    try:
        await _async_register_card(hass)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Impossible d'enregistrer rugby-lnr-game-card automatiquement : %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge l'entrée quand ses clubs suivis ont été modifiés."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
