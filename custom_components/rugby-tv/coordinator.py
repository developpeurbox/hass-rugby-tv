"""DataUpdateCoordinator Rugby LNR (TOP 14 / PRO D2).

Stratégie de scraping par club :
 1. GET https://{domaine}/club/{slug}  (domaine = top14.lnr.fr ou prod2.lnr.fr)
 2. On repère le bloc "Prochain match" dans le HTML brut et on en extrait,
    par regex (indépendant des classes CSS, qui peuvent changer) :
      - la date (JJ/MM/AAAA) et l'heure (HHhMM)
      - la journée (Jx)
      - les deux logos clubs (domicile puis extérieur, dans cet ordre,
        quel que soit le club dont on consulte la fiche)
      - le diffuseur TV (logo + nom), s'il y en a un
      - le lien vers la feuille de match
 3. Le nom complet de chaque club (celui suivi + son adversaire) est résolu
    via le <title> de sa propre fiche club, avec un petit cache mémoire
    (évite de re-télécharger la fiche d'un adversaire déjà croisé/suivi
    dans le même cycle de rafraîchissement).

Le HTML de top14.lnr.fr / prod2.lnr.fr n'expose pas d'API publique connue :
ce parsing repose sur la structure observée du site à la date d'écriture.
Si la LNR modifie sa page, seules les regex ci-dessous sont à ajuster.
"""
from __future__ import annotations

import json
import logging
import re
import ssl
import time
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CLUB_INFO_CACHE_TTL,
    CLUBS_CACHE_TTL,
    CLUBS_JSON_URL,
    COMPETITIONS,
    DOMAIN,
    SCAN_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

_RE_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_RE_SRC = re.compile(r"""src=["']([^"']+)["']""", re.IGNORECASE)
_RE_ALT = re.compile(r"""alt=["']([^"']*)["']""", re.IGNORECASE)
_RE_CLUB_LOGO = re.compile(r"cdn\.lnr\.fr/club/([a-z0-9\-]+)/photo/logo\.[0-9a-f]+")
_RE_TITLE = re.compile(r"<title[^>]*>([^<]*)</title>", re.IGNORECASE)
_RE_DATE = re.compile(r"(\d{2}/\d{2}/\d{4})")
_RE_HEURE = re.compile(r"(\d{1,2})h(\d{2})")
_RE_JOURNEE = re.compile(r">\s*J\s*0*(\d{1,2})\s*<")
_RE_JOURNEE_LOOSE = re.compile(r"\bJ\s*0*(\d{1,2})\b")
_RE_MATCH_LINK = re.compile(
    r"""href=["'](https?://[^"']*feuille-de-match/[^"']+)["']""", re.IGNORECASE
)
_RE_PROCHAIN_MATCH = re.compile(r"Prochain\s*match", re.IGNORECASE)

# ─── Cache clubs.json (liste des clubs suivis) ───────────────────────────────
_clubs_cache: dict | None = None
_clubs_cache_ts: float = 0.0
_clubs_last_updated: str = ""
_clubs_source: str = ""


async def load_clubs_async(session: aiohttp.ClientSession, force: bool = False, ssl_ctx=None) -> dict:
    """Charge clubs.json (liste des clubs TOP 14 / PRO D2 suivis).

    Tente d'abord la version distante sur GitHub (cache 1h), puis se replie
    sur le fichier embarqué dans l'intégration.
    """
    global _clubs_cache, _clubs_cache_ts, _clubs_last_updated, _clubs_source

    now = time.monotonic()
    if not force and _clubs_cache and (now - _clubs_cache_ts) < CLUBS_CACHE_TTL:
        return _clubs_cache

    try:
        async with session.get(
            CLUBS_JSON_URL, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                _clubs_cache = data
                _clubs_cache_ts = now
                _clubs_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                _clubs_source = "github"
                return data
            _LOGGER.debug("clubs.json GitHub → HTTP %s, fallback local", resp.status)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("clubs.json GitHub inaccessible : %s — fallback local", err)

    local = Path(__file__).parent / "clubs.json"
    with open(local, encoding="utf-8") as f:
        data = json.load(f)
    if not _clubs_cache:
        _clubs_cache = data
        _clubs_cache_ts = now
        _clubs_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _clubs_source = "local"
    return data


def flatten_clubs(clubs: dict) -> dict[str, dict]:
    """{"TOP 14": {"toulouse": {"comp":"top14"}, ...}, ...} -> {"toulouse": {"comp":"top14","league":"TOP 14"}}."""
    flat: dict[str, dict] = {}
    for league, teams in clubs.items():
        for slug, cfg in teams.items():
            flat[slug] = {**cfg, "league": league}
    return flat


# ─── Helpers HTML ─────────────────────────────────────────────────────────────
def _attr(tag: str, pattern: re.Pattern) -> str:
    m = pattern.search(tag)
    return m.group(1) if m else ""


def extract_title_name(html: str) -> tuple[str, str]:
    """Extrait (nom_complet, code_court) depuis le <title> de la page club.

    Formats observés :
      "Stade Toulousain - ST | Top 14 - Site Officiel" -> ("Stade Toulousain", "ST")
      "CA Brive | Pro D2 - Site Officiel"               -> ("CA Brive", "")
    """
    m = _RE_TITLE.search(html)
    if not m:
        return "", ""
    head = m.group(1).split("|")[0].strip()
    m2 = re.match(r"^(.*)\s-\s([A-Za-z0-9]{2,6})$", head)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    return head, ""


def extract_header_logo(html: str, slug: str) -> str:
    """Premier logo du club (bandeau d'en-tête) trouvé dans la page."""
    m = re.search(rf"(https://cdn\.lnr\.fr/club/{re.escape(slug)}/photo/logo\.[0-9a-f]+)", html)
    return m.group(1) if m else ""


def parse_prochain_match(html: str) -> dict | None:
    """Extrait les infos du bloc "Prochain match" de la page club.

    Retourne None si aucun prochain match n'est trouvé sur la page.
    """
    m = _RE_PROCHAIN_MATCH.search(html)
    if not m:
        return None

    start = m.end()
    idx_link = html.find("feuille-de-match", start)
    end = (idx_link + 400) if idx_link != -1 else (start + 6000)
    block = html[start:end]

    date_m = _RE_DATE.search(block)
    heure_m = _RE_HEURE.search(block)
    journee_m = _RE_JOURNEE.search(block) or _RE_JOURNEE_LOOSE.search(block)
    link_m = _RE_MATCH_LINK.search(block)

    club_imgs: list[dict] = []
    broadcasters: list[dict] = []

    for tag_m in _RE_IMG.finditer(block):
        tag = tag_m.group(0)
        src = _attr(tag, _RE_SRC)
        if not src:
            continue
        alt = _attr(tag, _RE_ALT)

        club_m = _RE_CLUB_LOGO.search(src)
        if club_m:
            club_imgs.append({"slug": club_m.group(1), "alt": alt, "logo": src})
            if len(club_imgs) == 2:
                break
            continue

        if "assets.lnr.fr" in src and len(club_imgs) >= 1:
           broadcasters.append(
               {
               "logo": src,
               "nom": alt,
               }
           )

    if len(club_imgs) < 2 or not date_m:
        return None

    home, away = club_imgs[0], club_imgs[1]

    heure_str = f"{heure_m.group(1).zfill(2)}:{heure_m.group(2)}" if heure_m else ""
    journee = f"J{journee_m.group(1)}" if journee_m else ""

    return {
        "date": date_m.group(1),
        "heure": heure_str,
        "journee": journee,
        "home_slug": home["slug"],
        "home_short": home["alt"],
        "home_logo": home["logo"],
        "away_slug": away["slug"],
        "away_short": away["alt"],
        "away_logo": away["logo"],
        "diffuseur1": broadcasters[0]["nom"] if len(broadcasters) > 0 else "",
        "logoDiffuseur1": broadcasters[0]["logo"] if len(broadcasters) > 0 else "",
        "diffuseur2": broadcasters[1]["nom"] if len(broadcasters) > 1 else "",
        "logoDiffuseur2": broadcasters[1]["logo"] if len(broadcasters) > 1 else "",
        "match_link": link_m.group(1) if link_m else "",
    }


def _format_date_fr(dt: datetime) -> str:
    return f"{JOURS_FR[dt.weekday()]} {dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"


# ─── Coordinator ─────────────────────────────────────────────────────────────
class RugbyLnrCoordinator(DataUpdateCoordinator):
    """selected = {"toulouse": {"comp": "top14", "league": "TOP 14"}, ...}."""

    def __init__(self, hass: HomeAssistant, selected: dict) -> None:
        self.selected = selected
        self._club_info_cache: dict[str, tuple[float, dict]] = {}
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(hours=SCAN_INTERVAL_HOURS)
        )

    async def _fetch_html(self, session: aiohttp.ClientSession, ssl_ctx, url: str) -> str | None:
        try:
            async with session.get(
                url, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("rugbytv %s → HTTP %s", url, resp.status)
                    return None
                return await resp.text()
        except aiohttp.ClientError as err:
            _LOGGER.warning("Erreur rugbytv %s : %s", url, err)
            return None

    async def _get_club_info(
        self, session: aiohttp.ClientSession, ssl_ctx, domain: str, slug: str
    ) -> dict:
        """Nom complet + logo d'un club, avec cache mémoire (TTL)."""
        now = time.monotonic()
        cached = self._club_info_cache.get(slug)
        if cached and (now - cached[0]) < CLUB_INFO_CACHE_TTL:
            return cached[1]

        html = await self._fetch_html(session, ssl_ctx, f"{domain}/club/{slug}")
        if not html:
            info = {"name": slug.replace("-", " ").title(), "short": "", "logo": "", "html": ""}
        else:
            name, short = extract_title_name(html)
            logo = extract_header_logo(html, slug)
            info = {
                "name": name or slug.replace("-", " ").title(),
                "short": short,
                "logo": logo,
                "html": html,
            }
        self._club_info_cache[slug] = (now, info)
        return info

    async def _async_update_data(self) -> dict:
        data: dict = {}
        ssl_ctx = await self.hass.async_add_executor_job(ssl.create_default_context)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                for slug, cfg in self.selected.items():
                    comp_key = cfg.get("comp", "top14")
                    comp = COMPETITIONS.get(comp_key, COMPETITIONS["top14"])
                    domain = comp["domain"]
                    comp_label = comp["label"]

                    club_info = await self._get_club_info(session, ssl_ctx, domain, slug)
                    team_name = club_info["name"]
                    team_logo = club_info["logo"]
                    html = club_info.get("html") or await self._fetch_html(
                        session, ssl_ctx, f"{domain}/club/{slug}"
                    )

                    match = parse_prochain_match(html) if html else None

                    if not match:
                        data[slug] = {
                            "state": "Aucun match",
                            "attributes": {
                                "team": team_name,
                                "logoTeam": team_logo,
                                "competition": comp_label,
                                "slug": slug,
                            },
                        }
                        continue

                    situation = "dom" if match["home_slug"] == slug else "ext"

                    if match["home_slug"] == slug:
                        home_info = club_info
                    else:
                        home_info = await self._get_club_info(session, ssl_ctx, domain, match["home_slug"])

                    if match["away_slug"] == slug:
                        away_info = club_info
                    else:
                        away_info = await self._get_club_info(session, ssl_ctx, domain, match["away_slug"])

                    try:
                        jj, mm, aaaa = match["date"].split("/")
                        hh, mn = (match["heure"].split(":") if match["heure"] else ("0", "0"))
                        dt_debut = datetime(int(aaaa), int(mm), int(jj), int(hh), int(mn))
                        dt_fin = dt_debut + timedelta(hours=2)
                        dt_iso = dt_debut.strftime("%Y-%m-%d %H:%M:%S")
                        dt_fin_iso = dt_fin.strftime("%Y-%m-%d %H:%M:%S")
                        display = dt_fin > datetime.now()
                        date_fr = _format_date_fr(dt_debut)
                    except (ValueError, KeyError):
                        dt_iso = ""
                        dt_fin_iso = ""
                        display = True
                        date_fr = match["date"]

                    domicile_nom = home_info["name"] or match["home_short"]
                    exterieur_nom = away_info["name"] or match["away_short"]

                    data[slug] = {
                        "state": match["diffuseur1"] or "Non renseigné",
                        "attributes": {
                            "team": team_name,
                            "logoTeam": team_logo,
                            "competition": comp_label,
                            "journee": match["journee"],
                            "domicile": domicile_nom,
                            "logoDomicile": home_info["logo"] or match["home_logo"],
                            "shortDomicile": match["home_short"],
                            "exterieur": exterieur_nom,
                            "logoExterieur": away_info["logo"] or match["away_logo"],
                            "shortExterieur": match["away_short"],
                            "situation": situation,
                            "date": match["date"],
                            "date_fr": date_fr,
                            "datetime": dt_iso,
                            "datetime_fin": dt_fin_iso,
                            "display": display,
                            "heure": match["heure"],
                            "diffuseur1": match["diffuseur1"],
                            "logoDiffuseur1": match["logoDiffuseur1"],
                            "diffuseur2": match["diffuseur2"],
                            "logoDiffuseur2": match["logoDiffuseur2"],
                            "game": f"{domicile_nom} - {exterieur_nom}",
                            "lien_match": match["match_link"],
                            "slug": slug,
                        },
                    }
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Erreur scraping Rugby TV : {err}") from err

        return data
