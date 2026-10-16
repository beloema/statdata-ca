# Sécurité et accès à l'évaluation / Security and evaluation access

## Français

### Accès recommandé pour la personne tutrice

Le dépôt actuel `beloema/statdata-ca` est **privé et appartient à un compte GitHub personnel**. GitHub permet l'invitation de collaborateurs par **Settings → Collaborators → Add people**, mais un collaborateur de dépôt personnel dispose de **droits d'écriture**, même si l'intention est seulement de consulter le code.

Deux options :

1. **Simplicité :** inviter votre professeur avec son identifiant GitHub (ou son adresse courriel associée à GitHub) au dépôt personnel. L'invitation doit être acceptée. **Cela donne des droits d'écriture**; retirer l'accès après la correction du projet si nécessaire.
2. **Lecture seule :** utiliser une **organisation GitHub** avec un dépôt privé de remise et un rôle **Read** pour le professeur. Préférer une **copie assainie** du code à transférer plutôt que déplacer aveuglément le dépôt de production : le déplacement peut modifier les intégrations et l'automatisation existantes. Ne pas mettre de secrets de production dans la copie.

Documentation officielle : [inviter un collaborateur](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository) · [droits des dépôts personnels](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository).

### Liste de sécurité avant la remise

- Ne jamais communiquer `.env`, `DATABASE_URL`, mots de passe Neon, jetons API, identifiants Render ou paramètres secrets WHC.
- Vérifier que les identifiants n'ont pas été committés **dans l'historique Git**, pas uniquement dans l'état actuel des fichiers.
- Vérifier `.gitignore` (au minimum : `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, fichiers temporaires et téléchargements locaux non destinés au dépôt).
- Laisser les secrets GitHub Actions dans **Settings → Secrets and variables → Actions**.
- Fournir pour l'évaluation le lien du site, le lien du dépôt et la référence de l'exécution GitHub Actions réussie.
- N'accorder aucun accès direct à la base Neon ni aux comptes Render/WHC pour la simple lecture du code.

### Révocation

Après l'évaluation, l'accès GitHub peut être retiré dans **Settings → Collaborators**. Le retrait ne révoque pas d'éventuelles copies du dépôt faites durant la période d'accès.

---

## English

The current private repository belongs to a **personal GitHub account**. Inviting the professor via **Settings → Collaborators → Add people** allows access after acceptance, but **personal-repository collaborators have write access**, not read-only access.

For true read-only review, use a private repository inside a **GitHub organization** and grant the professor the **Read** role. Prefer a scrubbed submission copy over transferring the live production repository, which may affect Render and Actions integrations. Never copy `.env`, connection strings, secrets or credentials.

Before sharing, inspect both current files **and Git history** for accidentally committed secrets; verify `.gitignore`; keep GitHub, Neon and Render secrets in their respective protected settings. The professor needs the application URL, repository URL and run evidence, not database console access. Remove access after grading if appropriate; previously cloned copies cannot be recalled.
