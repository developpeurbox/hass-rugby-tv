"""Intégration Rugby TV (TOP 14 / PRO D2) pour Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import RugbyTvCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


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
