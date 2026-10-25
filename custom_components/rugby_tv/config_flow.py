"""Config flow Rugby LNR — un club (TOP 14 ou PRO D2) par entrée."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN
from .coordinator import flatten_clubs, load_clubs_async


async def _load_clubs(hass: HomeAssistant) -> dict:
    session = async_get_clientsession(hass)
    return await load_clubs_async(hass, session, force=True)


def _title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _build_options(clubs: dict) -> tuple[list[dict], dict[str, dict]]:
    """Retourne (options pour le sélecteur, dict slug -> config club)."""
    flat = flatten_clubs(clubs)
    options = [
        {"value": slug, "label": f"{cfg['league']} — {_title(slug)}"}
        for slug, cfg in flat.items()
    ]
    options.sort(key=lambda o: o["label"])
    return options, flat


class RugbyTvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Choisir UN club à suivre. Ajouter l'intégration plusieurs fois pour plusieurs clubs."""

    VERSION = 2

    def __init__(self):
        self._clubs: dict = {}

    async def async_step_user(self, user_input=None):
        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)

        options, flat = _build_options(self._clubs)

        # On ne propose pas les clubs déjà configurés
        configured = self._async_current_ids()
        options = [o for o in options if o["value"] not in configured]
        if not options:
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            slug = user_input["club"]
            await self.async_set_unique_id(slug)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_title(slug),
                data={"selected": {slug: flat[slug]}},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("club"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_import(self, import_data):
        """Utilisé par la migration v1 -> v2 (une entrée créée par club)."""
        slug = import_data["slug"]
        await self.async_set_unique_id(slug)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=_title(slug),
            data={"selected": {slug: import_data["cfg"]}},
        )
