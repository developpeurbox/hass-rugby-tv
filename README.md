# Rugby TV — Intégration HACS pour Home Assistant
[![PayPal](https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&color=purple&logo=paypal&logoColor=ccc&link=https%3A%2F%2Fpaypal.me%2hlaissus/5)](https://paypal.me/hlaissus/5)
[![GitHub Release]( https://img.shields.io/github/v/release/developpeurbox/hass-rugby-tv?style=for-the-badge&color=blue)](https://github.com/developpeurbox/hass-rugby-tv/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&color=blue)](https://github.com/hacs/integration)
[![Community Forum]( https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge&color=pink)](https://forum.hacf.fr/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rugby-tv/blob/main/LICENSE)

[![HACS Action](https://github.com/developpeurbox/hass-rugby-tv/actions/workflows/hacs.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rugby-tv/actions/workflows/hacs.yml)
[![HACS Action](https://github.com/developpeurbox/hass-rugby-tv/actions/workflows/hassfest.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-rugby-tv/actions/workflows/hassfest.yml)

Intégration personnalisée pour Home Assistant permettant de suivre le **prochain match** de vos clubs de TOP 14 et PRO D2 préférés, à partir des fiches club officielles de la LNR (`top14.lnr.fr` / `prod2.lnr.fr`).

> 🎴 La carte Lovelace dédiée n'est **pas incluse** dans ce dépôt — elle vit dans son propre repo : [`ha-rugby-tv-game-card`](https://github.com/developpeurbox/ha-rugby-tv-game-card), à installer séparément.

## ✨ Caractéristiques

- 📅 Suivi multi-clubs : un sensor par club (TOP 14 + PRO D2, 29 clubs suivis par défaut).
- 🏉 Infos complètes : adversaire, domicile/extérieur, journée, date, heure, diffuseur(s) TV, logos.
- ⚙️ Configuration via l'interface Home Assistant (sélection multi-clubs, **une seule instance** de l'intégration).
- 🔗 Lien direct vers la feuille de match officielle.

## 🔧 Attributs disponibles par sensor
  <details>
    <summary> Attributs </summary>
  
  
  | Attribut          | Description                                          |
  | ------------------ | ----------------------------------------------------- |
  | `state`             | Nom du diffuseur TV principal (ex: Canal +), ou "Aucun match" |
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
  | `diffuseur1` / `logoDiffuseur1` | Nom / logo du 1er diffuseur TV              |
  | `diffuseur2` / `logoDiffuseur2` | Nom / logo du 2e diffuseur TV (s'il y en a un) |
  | `game`              | Texte "Domicile - Extérieur"                             |
  | `lien_match`        | URL de la feuille de match LNR                          |
  </details>

## 🏗️ Installation via HACS

1. Dans HACS → **Intégrations** → menu ⋮ → **Dépôts personnalisés**.
2. Ajouter l'URL `https://github.com/developpeurbox/hass-rugby-tv`, catégorie **Integration**.
3. Installer **Rugby TV (TOP 14 / PRO D2)**.
4. Redémarrer Home Assistant.
5. **Paramètres → Appareils & services → Ajouter une intégration → Rugby TV**.
6. Sélectionner les clubs à suivre.

> ℹ️ L'intégration n'autorise qu'**une seule instance**. Pour modifier la liste des clubs suivis par la suite, utilise le bouton **Configurer** sur l'intégration existante (pas "Ajouter une intégration" à nouveau).

## 🏗️ Installation manuelle

1. Copier `custom_components/rugby_tv/` dans le dossier `custom_components/` de votre instance Home Assistant.
2. Redémarrer Home Assistant.

## 🎴 Carte Lovelace

Voir [`ha-rugby-tv-game-card`](https://github.com/developpeurbox/ha-rugby-tv-game-card) pour l'installation (HACS "Frontend" ou manuelle + ressource Lovelace). Une fois installée :

```yaml
type: custom:rugby-tv-game-card
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
        type: custom:rugby-tv-game-card
      entity_id: sensor.rugby_*
      sort:
        method: attribute
        attribute: datetime
```

## 🔁 Rafraîchissement

Les données sont mises à jour automatiquement **toutes les 6 heures**. Un rafraîchissement manuel est possible depuis l'UI de l'intégration.

## 🏟️ Clubs suivis

Le fichier [`custom_components/rugby_tv/clubs.json`](custom_components/rugby_tv/clubs.json) liste les clubs TOP 14 et PRO D2 suivis.

## ⚠️ Note importante sur le scraping

Cette intégration s'appuie sur la structure HTML actuelle des pages club `top14.lnr.fr` / `prod2.lnr.fr` (repérage du bloc "Prochain match", des logos `cdn.lnr.fr/club/<slug>/photo/logo.*`, du/des diffuseur(s) `assets.lnr.fr/*` et de l'heure au format `HHhMM`). Si la LNR fait évoluer la structure de ses pages, seules les expressions régulières de `coordinator.py` sont à corriger — activez les logs `debug` du composant `rugby_tv` en cas de sensor vide ou d'erreur :

```yaml
logger:
  default: warning
  logs:
    custom_components.rugby_tv: debug
```
