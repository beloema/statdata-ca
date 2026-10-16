# Processus ETL et automatisation / ETL and automation

## Français

### Cycle des traitements

`update_all.py` crée les répertoires de travail, télécharge les gros tableaux **emploi** (`14100287`), **PIB** (`36100434`) et **population** (`17100009`) par l'API de Statistique Canada, puis exécute les six programmes, dans l'ordre : `update_cpi.py`, `update_interest_rates.py`, `update_exchange_rates.py`, `update_employment.py`, `update_gdp.py` et `update_population.py`. Les trois premiers récupèrent directement leur archive CSV officielle.

Chaque script : sélectionne les dimensions pertinentes; convertit les champs avec Pandas; rejette les lignes invalides; supprime les doublons du lot; échoue si aucun enregistrement valable n'est obtenu; enregistre un CSV de travail; puis effectue une insertion ou mise à jour PostgreSQL. Un échec arrête l'orchestrateur (code de sortie non nul).

### Clés uniques utilisées

| Table | Clé logique |
| --- | --- |
| `cpi` | `(date, region, unit)` |
| `interest_rates` | `(date, indicator)` |
| `exchange_rates` | `(date, currency)` |
| `employment` | `(date, region, indicator)` |
| `gdp` | `(date, industry)` |
| `population` | `(date, region)` |

Les commandes SQL `INSERT ... ON CONFLICT ... DO UPDATE` actualisent les valeurs révisées au besoin et empêchent l'ajout d'une deuxième ligne pour une même clé. Le contrôle `tools/check_daily_update.py` recompte les six tables, trouve leur date maximale et signale les clés répétées ou les tables vides.

### GitHub Actions

- Fichier : `.github/workflows/daily-update.yml`.
- Déclencheurs : exécution manuelle (`workflow_dispatch`) et planification quotidienne à **06 h 17, fuseau America/Toronto** (même heure civile que Montréal; gère le changement d'heure).
- Environnement : Linux, Python 3.13, installation de `requirements.txt`.
- Secret requis : `DATABASE_URL` dans **Settings → Secrets and variables → Actions**.
- Permissions minimales de la tâche : `contents: read`; groupe `concurrency` pour éviter les exécutions simultanées de ce workflow.
- Contrôles : tests hors ligne avant chargement; validation en base après chargement; tests d'intégration; résumé GitHub Actions.
- En cas d'échec : étape d'erreur et journaux consultables dans GitHub Actions; **aucune notification externe (courriel/SMS) n'est configurée**.

### Vérification de fonctionnement

1. Déclencher le workflow manuellement dans l'onglet **Actions** du dépôt.
2. Vérifier le statut de la tâche et le résumé des six tables.
3. Contrôler la somme, les dates d'observation et l'absence de doublons.
4. Le lendemain, confirmer qu'une exécution de type **schedule** a bien été déclenchée sans intervention.

**Validation observée le 16 octobre 2026 :** exécution manuelle réussie en 2 min 8 s, **127 664 enregistrements**, **0 doublon**. Le résultat ne prouve pas encore qu'une exécution planifiée a eu lieu.

### Limites à connaître

- La disponibilité de l'API et les délais de publication officiels échappent au projet.
- Les très gros CSV peuvent accroître le temps d'exécution et les ressources utilisées.
- La mise à jour s'effectue **table par table**; ce n'est pas une transaction globale unique englobant les six sources.
- Les journaux d'erreur sont conservés suivant les règles de GitHub Actions, pas dans une table d'audit dédiée.

---

## English

`update_all.py` downloads the larger labour, GDP and population files through the Statistics Canada API, then runs all six scripts sequentially. CPI, interest and exchange-rate scripts download their own official ZIP files. Each ETL script filters, normalizes, drops invalid rows and batch duplicates, fails on empty results, writes a working CSV and upserts observations to PostgreSQL.

Unique keys are `(date, region, unit)` for CPI; `(date, indicator)` for interest; `(date, currency)` for FX; `(date, region, indicator)` for labour; `(date, industry)` for GDP; and `(date, region)` for population. `ON CONFLICT` prevents duplicate logical records and permits corrections from revised official observations.

The GitHub Actions workflow `.github/workflows/daily-update.yml` runs manually or at **06:17 America/Toronto time** each day. It requires the `DATABASE_URL` repository secret, runs Python 3.13, performs an offline ETL test, loads all six sources, validates the database and runs regression tests. Failures are shown in Actions logs and job summaries; email/SMS notifications are **not configured**. Workflows can be delayed; confirm the first unattended `schedule` event.

An October 16, 2026 manual run completed successfully in **2m 8s**, reporting **127,664 observations and zero duplicate keys**. Updates are committed table by table, not as one six-table atomic transaction; official API delays, changing files and the GitHub log retention period remain limitations.
