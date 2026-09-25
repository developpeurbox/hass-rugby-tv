"""Config flow Rugby LNR — sélection multi-clubs (TOP 14 + PRO D2)."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
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
    return await load_clubs_async(session, force=True)


def _build_options(clubs: dict) -> tuple[list[dict], dict[str, dict]]:
    """Retourne (options pour le sélecteur, dict slug -> config club)."""
    flat = flatten_clubs(clubs)
    options = [
        {"value": slug, "label": f"{cfg['league']} — {slug.replace('-', ' ').title()}"}
        for slug, cfg in flat.items()
    ]
    options.sort(key=lambda o: o["label"])
    return options, flat


def _add_missing_current(options: list[dict], flat: dict, current: dict) -> None:
    """Ne jamais perdre un club coché même s'il a disparu du dataset."""
    known = {opt["value"] for opt in options}
    for slug, cfg in current.items():
        if slug not in known:
            league = cfg.get("league", "?")
            options.append(
                {"value": slug, "label": f"(retiré du dataset) {league} — {slug}"}
            )
            flat[slug] = cfg
    options.sort(key=lambda o: o["label"])


class RugbyLnrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Choisir les clubs TOP 14 / PRO D2 à suivre, en une étape."""

    VERSION = 1

    def __init__(self):
        self._clubs: dict = {}

    async def async_step_user(self, user_input=None):
        errors = {}

        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)

        options, flat = _build_options(self._clubs)

        if user_input is not None:
            chosen = user_input.get("clubs", [])
            if not chosen:
                errors["clubs"] = "no_club"
            else:
                selected = {s: flat[s] for s in chosen if s in flat}
                title = ", ".join(sorted(s.replace("-", " ").title() for s in selected))
                return self.async_create_entry(title=title, data={"selected": selected})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("clubs"): SelectSelector(
                        SelectSelectorConfig(
                            options=options, multiple=True, mode=SelectSelectorMode.LIST
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RugbyLnrOptionsFlow(config_entry)


class RugbyLnrOptionsFlow(config_entries.OptionsFlow):
    """Modifier les clubs suivis d'une entrée existante."""

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._clubs: dict = {}

    async def async_step_init(self, user_input=None):
        errors = {}
        current = dict(self.config_entry.data.get("selected", {}))

        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)

        options, flat = _build_options(self._clubs)
        _add_missing_current(options, flat, current)

        default_chosen = list(current.keys())

        if user_input is not None:
            chosen = user_input.get("clubs", [])
            if not chosen:
                errors["clubs"] = "no_club"
            else:
                selected = {s: flat[s] for s in chosen if s in flat}
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=", ".join(sorted(s.replace("-", " ").title() for s in selected)),
                    data={**self.config_entry.data, "selected": selected},
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("clubs", default=default_chosen): SelectSelector(
                        SelectSelectorConfig(
                            options=options, multiple=True, mode=SelectSelectorMode.LIST
                        )
                    ),
                }
            ),
            errors=errors,
        )
