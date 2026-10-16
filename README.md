# STATDATA.CA

**Plateforme bilingue d'exploration et de visualisation de données canadiennes**  
**Bilingual Canadian open-data dashboard — [English README](README.en.md)**

[Application Web](https://statdata.ca) · [Documentation technique](docs/ARCHITECTURE.md) · [Sources](docs/SOURCES.md)

Projet réalisé par **Emanuel Belony** dans le cadre de **SCI 1402 — Projet en science des données**, Université TÉLUQ, Certificat en science des données (4865).

## Présentation

Statistique Canada publie des tableaux riches, mais leur consultation conjointe exige souvent plusieurs extractions et transformations. STATDATA.CA regroupe **six tableaux officiels** dans une interface bilingue (français/anglais) pour faciliter la consultation de séries historiques, les comparaisons régionales et l'exportation des résultats. L'application conserve les dates de référence et les unités des sources.

## Fonctionnalités

- Tableaux de bord interactifs, graphiques temporels et filtres de période.
- Comparaisons entre le Canada et les régions disponibles selon l'indicateur.
- Résultats descriptifs et endpoints JSON pour les graphiques et statistiques.
- Téléchargement de données au format CSV en français ou en anglais.
- Interface FR/EN et mode clair/sombre.
- Mise à jour quotidienne déclenchée par GitHub Actions, avec validation des clés uniques.

## Indicateurs et sources

| Domaine | Tableau Statistique Canada | Granularité retenue |
| --- | --- | --- |
| Indice des prix à la consommation (IPC) | `18-10-0004-01` | Canada, IPC d'ensemble, mensuel |
| Taux d'intérêt | `10-10-0139-01` | Canada, six indicateurs, quotidien |
| Taux de change | `33-10-0036-01` | Canada, six devises, quotidien |
| Marché du travail | `14-10-0287-01` | Canada et régions disponibles, cinq indicateurs, mensuel |
| Produit intérieur brut réel | `36-10-0434-01` | Canada, trois groupes d'industries, mensuel |
| Population | `17-10-0009-01` | Canada, provinces et territoires, trimestriel |

Détails des filtres, des unités et des sources : [docs/SOURCES.md](docs/SOURCES.md).

## Technologies

Python, Pandas, Flask, PostgreSQL (Neon), SQL, HTML/CSS/JavaScript, Chart.js, GitHub Actions et Render.

```text
Statistique Canada (CSV / API)
           ↓
       Python / Pandas
    extraction et nettoyage
           ↓
PostgreSQL — Neon (INSERT ... ON CONFLICT)
           ↓
        Flask / JSON API
           ↓
STATDATA.CA — graphiques / tableaux / CSV
```

## État vérifié du projet

- **16 octobre 2026 :** exécution manuelle GitHub Actions réussie en **2 min 8 s**.
- **127 664 observations** dans les six tables après mise à jour ; **aucune clé dupliquée** signalée.
- La planification quotidienne est configurée ; son exécution autonome doit être confirmée à la prochaine échéance.

Ces chiffres décrivent une **validation datée**, non un compteur permanent.

## Installation et exécution

Les prérequis, la préparation d'une base indépendante, l'utilisation de `DATABASE_URL` et les tests sont détaillés dans [docs/INSTALLATION.md](docs/INSTALLATION.md). Ne commitez jamais votre fichier `.env`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests/test_daily_update.py
```

La validation complète et l'ETL nécessitent une base PostgreSQL accessible et initialisée. Voir le guide avant de lancer `python update_all.py`.

## Documentation

- [Installation et tests](docs/INSTALLATION.md)
- [Architecture et API](docs/ARCHITECTURE.md)
- [Sources et sélection des observations](docs/SOURCES.md)
- [ETL, mises à jour et contrôles](docs/ETL.md)
- [Déploiement et exploitation](docs/DEPLOYMENT.md)
- [Sécurité et accès pour l'évaluation](docs/ACCESS.md)

## Usage académique et provenance

STATDATA.CA est un projet d'étude indépendant. Les données proviennent de **Statistique Canada** ; la sélection, la transformation et la présentation constituent le travail du projet. Les valeurs publiées ne sont pas des prévisions et doivent être interprétées en tenant compte de leur date de référence et des révisions de la source.
