"""Entités sensor Rugby TV."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RugbyTvCoordinator

EMPTY_ATTRS = {
    "team": "", "competition": "", "journee": "",
    "domicile": "", "logoDomicile": "", "shortDomicile": "",
    "exterieur": "", "logoExterieur": "", "shortExterieur": "",
    "situation": "", "date": "", "date_fr": "",
    "datetime": "", "datetime_fin": "", "display": False,
    "heure": "",
    "diffuseur1": "", "logoDiffuseur1": "",
    "diffuseur2": "", "logoDiffuseur2": "",
    "game": "", "lien_match": "",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RugbyTvCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [RugbyTvSensor(coordinator, slug) for slug in coordinator.selected],
        update_before_add=True,
    )


class RugbyTvSensor(CoordinatorEntity, SensorEntity):
    """Un sensor = un club suivi (TOP 14 ou PRO D2)."""

    def __init__(self, coordinator: RugbyTvCoordinator, slug: str) -> None:
        super().__init__(coordinator)
        self._slug = slug
        display_name = slug.replace("-", " ").title()
        self._attr_name = f"Rugby {display_name}"
        self._attr_unique_id = f"rugbytv_{slug.replace('-', '_')}"
        self._attr_icon = "mdi:rugby"

    @property
    def _data(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._slug)

    @property
    def native_value(self) -> str:
        d = self._data
        return d["state"] if d else "Aucun match"

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data
        if d is None:
            return {**EMPTY_ATTRS, "team": self._slug.replace("-", " ").title(), "slug": self._slug}
        return d.get("attributes", {})

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "rugbytv_device")},
            "name": "Rugby TV",
            "model": "Match Sensor",
            "manufacturer": "developpeurbox",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
