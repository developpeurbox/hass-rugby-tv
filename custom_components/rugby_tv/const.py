"""Constantes pour l'intégration Rugby TV (TOP 14 / PRO D2)."""

DOMAIN = "rugby_tv"
SCAN_INTERVAL_HOURS = 6

# Domaines LNR par compétition
COMPETITIONS = {
    "top14": {
        "label": "TOP 14",
        "domain": "https://top14.lnr.fr",
    },
    "prod2": {
        "label": "PRO D2",
        "domain": "https://prod2.lnr.fr",
    },
}

# Cache des fiches club (nom complet / logo / short) résolues par scraping.
CLUB_INFO_CACHE_TTL = 6 * 3600  # secondes

# URL distante du fichier clubs.json (liste des clubs suivis par compétition).
# À adapter une fois le dépôt publié sur GitHub (même logique que hass-footao).
CLUBS_JSON_URL = (
    "https://raw.githubusercontent.com/developpeurbox/hass-rugby-tv/"
    "refs/heads/main/custom_components/rugby_tv/clubs.json"
)
CLUBS_CACHE_TTL = 3600  # secondes — rechargement max 1x/heure
