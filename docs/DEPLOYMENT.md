# Déploiement et exploitation / Deployment and operations

## Français

### Services

| Service | Responsabilité | Donnée sensible |
| --- | --- | --- |
| GitHub (dépôt privé) | Code, historique et GitHub Actions | Secret `DATABASE_URL` dans les secrets Actions |
| Neon | Base PostgreSQL de production | Utilisateur et mot de passe dans l'URL de connexion |
| Render | Exécution de l'application Flask | Variable d'environnement `DATABASE_URL` configurée séparément |
| WHC | Enregistrement et gestion du nom de domaine | Accès au compte et paramètres DNS |

Le site public est `https://statdata.ca`. La connexion Render → Neon est indépendante de la connexion GitHub Actions → Neon : les deux services doivent recevoir leur variable `DATABASE_URL` via leur propre gestionnaire de secrets.

### Vérifications sur Render

1. Vérifier le dépôt et la branche actuellement connectés au service Web.
2. Vérifier les commandes de création et de démarrage **dans Render**, avant toute modification. Pour l'application Flask fournie, `gunicorn app:app` est une **commande possible**; la commande réellement déployée n'était pas présente dans les fichiers transmis.
3. Vérifier les variables d'environnement dans les paramètres protégés, sans les publier.
4. Vérifier `/health` et les pages du site après chaque déploiement.
5. Tester les filtres, le changement de langue et les exportations CSV.

La planification quotidienne est exécutée **dans GitHub Actions**, et non dans Render. Une mise à jour de données dans Neon est visible depuis le site au prochain chargement des requêtes correspondantes, sous réserve des mécanismes de cache éventuels.

### Procédure simple de maintenance

```bash
cd ~/Desktop/statdata-ca
source .venv/bin/activate
python -m pytest -q tests/test_daily_update.py
git status --short
```

Dans GitHub Actions, observer la prochaine exécution quotidienne et son résumé. En cas d'échec : identifier l'étape, consulter le message d'erreur, vérifier la disponibilité de Statistique Canada ou de Neon, corriger le code dans une branche puis relancer manuellement. Ne jamais coller une URL de connexion complète dans un ticket, un journal ou un courriel.

### Sauvegardes et reprise

L'historique Git conserve le code, **pas une sauvegarde complète des données PostgreSQL**. L'ETL permet de reconstruire les observations à partir des fichiers officiels lorsque les sources demeurent disponibles, mais ne remplace pas une politique de sauvegarde de base. Les options de sauvegarde/restauration Neon et les limites Render dépendent du plan retenu et doivent être vérifiées dans les consoles respectives.

---

## English

GitHub stores private source code and runs the daily ETL; Neon hosts PostgreSQL; Render serves Flask; WHC manages the domain. Set `DATABASE_URL` **separately** in GitHub Actions secrets and Render environment settings. Never put a live connection string in tracked source files.

To verify Render, inspect the service's current build/start commands and environment values, then test `/health`, the main dashboard, language switching and CSV downloads. `gunicorn app:app` is compatible with the provided Flask import path but the exact deployed Render start command was not included in the supplied files and should not be assumed.

GitHub Actions handles scheduling, independently of Render. For incidents, inspect the failed Actions step, check upstream availability and Neon connectivity, make an appropriately reviewed fix and rerun manually. Git history is **not** a database backup; verify the backup and recovery capabilities of your Neon plan.
