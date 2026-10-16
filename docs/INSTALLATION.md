# Installation et tests / Installation and tests

## Français

### Prérequis

- Python **3.13**, Git et un terminal (commandes présentées pour macOS).
- PostgreSQL local **ou** une base PostgreSQL de développement séparée (par exemple une branche de développement Neon).
- Accès Internet pour récupérer les CSV officiels.
- **Ne pas utiliser la base de production pour une expérimentation ou une création de schéma.**

### Récupérer le code et les dépendances

```bash
git clone https://github.com/beloema/statdata-ca.git
cd statdata-ca
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Le clonage du dépôt privé nécessite un accès GitHub autorisé. Si vous avez déjà cloné le dépôt, utilisez le répertoire existant.

### Base de données

Si vous utilisez une base PostgreSQL indépendante, préparez son schéma avec :

```bash
# Après avoir configuré la variable DATABASE_URL dans votre terminal :
psql "$DATABASE_URL" -f sql/schema.sql
```

Le fichier `sql/schema.sql` est un **schéma de démarrage pour une base neuve**. Il correspond aux colonnes et contraintes utilisées par les scripts ETL fournis; ce n'est pas une migration de la base de production existante.

Configurer un fichier `.env` **local et non versionné** à partir de `.env.example` :

```bash
cp .env.example .env
# Modifier .env localement avec son éditeur; ne jamais partager sa valeur.
```

Clé reconnue : `DATABASE_URL`. La connexion contient normalement `?sslmode=require` pour Neon. Hors GitHub Actions, le code permet également le PostgreSQL local `dbname=statdata` si `DATABASE_URL` est absent; cela ne remplace pas l'initialisation des tables.

### Exécuter

```bash
# Premier test sans réseau et sans accès à la base
python -m pytest -q tests/test_daily_update.py

# Chargement initial dans votre base de développement (avec DATABASE_URL)
python update_all.py

# Comptages, dernières observations et contrôle des doublons
python tools/check_daily_update.py

# Tests d'intégration (demandent données + application complètes)
python -m pytest -q

# Application Flask, dans un second terminal, avec .venv activé
flask --app app run --debug
```

Consulter ensuite `http://127.0.0.1:5000/` et `http://127.0.0.1:5000/health`. L'ETL peut télécharger de très gros fichiers. `tools/validate_official.py` utilise encore une connexion PostgreSQL **locale** codée dans sa propre implémentation; il n'est pas inclus dans la chaîne quotidienne et nécessite une adaptation avant une validation directement contre Neon.

### Données et secrets

Ne jamais versionner `.env`, les archives brutes téléchargées, les CSV de travail contenant des données volumineuses, les fichiers de cache ou les identifiants. Vérifier `git status` et `git diff --cached` avant toute publication.

---

## English

### Requirements

Use Python **3.13**, Git and a PostgreSQL **development** database, plus Internet connectivity for official CSV downloads. Do not initialize or experiment against your live production database.

```bash
git clone https://github.com/beloema/statdata-ca.git
cd statdata-ca
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env locally with a development DATABASE_URL; never commit it.
```

For a **new, separate database**, initialize using `psql "$DATABASE_URL" -f sql/schema.sql`. This creates compatible tables and the derived inflation view; it is not intended as a production migration. For Neon, the URL typically requires `sslmode=require`. The code can fall back to local PostgreSQL `dbname=statdata` outside GitHub Actions.

```bash
python -m pytest -q tests/test_daily_update.py  # offline tests
python update_all.py                             # downloads + upserts
python tools/check_daily_update.py               # database validation
python -m pytest -q                              # full integration tests
flask --app app run --debug                      # local website
```

Open `http://127.0.0.1:5000/`. Some raw downloads are large. `tools/validate_official.py` currently assumes local PostgreSQL and is not part of the daily CI job. Keep `.env`, generated data and credentials out of Git commits.
