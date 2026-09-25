# Rugby TV — Intégration HACS pour Home Assistant
[![PayPal](https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&color=purple&logo=paypal&logoColor=ccc&link=https%3A%2F%2Fpaypal.me%2hlaissus/5)](https://paypal.me/hlaissus/5)
[![GitHub Release]( https://img.shields.io/github/v/release/developpeurbox/hass-rubgy-tv?style=for-the-badge&color=blue)](https://github.com/developpeurbox/hass-rubgy-tv/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&color=blue)](https://github.com/hacs/integration)
[![Community Forum]( https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge&color=pink)](https://forum.hacf.fr/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rubgy-tv/blob/main/LICENSE)

[![HACS Action](https://github.com/developpeurbox/hass-rubgy-tv/actions/workflows/hacs.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rubgy-tv/actions/workflows/hacs.yml)
[![HACS Action](https://github.com/developpeurbox/hass-rubgy-tv/actions/workflows/hassfest.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rubgy-tv/actions/workflows/hassfest.yml)

Intégration personnalisée pour Home Assistant permettant de suivre le **prochain match** de vos clubs de TOP 14 et PRO D2 préférés, à partir des fiches club officielles de la LNR (`top14.lnr.fr` / `prod2.lnr.fr`), avec sa carte Lovelace dédiée **incluse** (`rugby-lnr-game-card`).


## ✨ Caractéristiques

- 📅 Suivi multi-clubs : un sensor par club (TOP 14 + PRO D2, 29 clubs suivis par défaut).
- 🏉 Infos complètes : adversaire, domicile/extérieur, journée, date, heure, diffuseur TV, logos.
- ⚙️ Configuration via l'interface Home Assistant (sélection multi-clubs).
- 🎴 Carte Lovelace intégrée, enregistrée automatiquement au démarrage.
- 🔗 Lien direct vers la feuille de match officielle.

## 🔧 Attributs disponibles par sensor

| Attribut          | Description                                          |
| ------------------ | ----------------------------------------------------- |
| `state`             | Nom du diffuseur TV (ex: Canal +), ou "Aucun match"   |
| `team`              | Nom complet du club suivi                              |
| `logoTeam`          | URL du logo du club suivi                              |
| `competition`       | "TOP 14" ou "PRO D2"                                   |
| `journee`           | Journée du championnat (ex: J4)                        |
| `domicile`          | Équipe à domicile                                       |
| `logoDomicile`      | Logo de l'équipe à domicile                             |
| `exterieur`         | Équipe à l'extérieur                                    |
| `logoExterieur`     | Logo de l'équipe à l'extérieur                          |
| `situation`         | `dom` ou `ext` selon le rôle du club suivi              |
| `date` / `date_fr`  | Date brute (JJ/MM/AAAA) / date en français              |
| `datetime` / `datetime_fin` | Horodatage ISO du coup d'envoi / fin estimée   |
| `display`           | `true` si le match est dans le futur                    |
| `heure`             | Heure du coup d'envoi (HH:MM)                           |
| `diffuseur`         | Nom du diffuseur TV                                     |
| `logoDiffuseur`     | Logo du diffuseur TV                                    |
| `game`              | Texte "Domicile - Extérieur"                             |
| `lien_match`        | URL de la feuille de match LNR                          |

## 🏗️ Installation via HACS

1. Dans HACS → **Intégrations** → menu ⋮ → **Dépôts personnalisés**.
2. Ajouter l'URL de ce dépôt, catégorie **Integration**.
3. Installer **Rugby TV LNR (TOP 14 / PRO D2)**.
4. Redémarrer Home Assistant.
5. **Paramètres → Appareils & services → Ajouter une intégration → Rugby LNR**.

## 🏗️ Installation manuelle

1. Copier `custom_components/rugby_lnr/` dans le dossier `custom_components/` de votre instance Home Assistant.
2. Redémarrer Home Assistant.

## 🎨 Carte `rugby-lnr-game-card`

Fournie avec l'intégration (dossier `www/`), enregistrée automatiquement au démarrage — pas besoin d'ajouter une ressource Lovelace manuellement.

```yaml
type: custom:rugby-lnr-game-card
entity: sensor.rugby_toulouse
footer_bg: "rgba(0,0,0,0.6)"
footer_color: "#e63946"
```

Pour afficher tous vos matchs :

```yaml
type: custom:auto-entities
card:
  type: entities
filter:
  include:
    - options:
        type: custom:rugby-lnr-game-card
      entity_id: sensor.rugby_*
      sort:
        method: attribute
        attribute: datetime
```

## 🔁 Rafraîchissement

Les données sont mises à jour automatiquement **toutes les 6 heures**. Un rafraîchissement manuel est possible depuis l'UI de l'intégration.

## 🏟️ Clubs suivis

Le fichier [`custom_components/rugbytv/clubs.json`](custom_components/rugbytv/clubs.json) liste les clubs TOP 14 et PRO D2 suivis (slug LNR + compétition). Pour ajouter/retirer un club, il suffit d'éditer ce fichier avec le slug tel qu'il apparaît dans l'URL de sa fiche (`https://top14.lnr.fr/club/<slug>` ou `https://prod2.lnr.fr/club/<slug>`) — les noms complets et logos sont résolus automatiquement par scraping, pas besoin de les renseigner à la main.

## ⚠️ Note importante sur le scraping

Cette intégration s'appuie sur la structure HTML actuelle des pages club `top14.lnr.fr` / `prod2.lnr.fr` (repérage du bloc "Prochain match", des logos `cdn.lnr.fr/club/<slug>/photo/logo.*`, du diffuseur `assets.lnr.fr/*` et de l'heure au format `HHhMM`). Le parsing (`coordinator.py`) a été écrit et testé sur des extraits de page reconstitués à partir du rendu du site, mais **n'a pas encore été validé contre le HTML brut en conditions réelles** — à tester et ajuster une fois déployé (activez les logs `debug` du composant `rugby_lnr` en cas de sensor vide ou d'erreur). Si la LNR fait évoluer la structure de ses pages, seules les expressions régulières de `coordinator.py` sont à corriger.
