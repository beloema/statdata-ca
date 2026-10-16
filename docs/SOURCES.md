# Sources de données / Data sources

## Français

**Producteur de toutes les données : Statistique Canada.** Les six sources sont des tableaux officiels, et non des jeux de données reconstitués à partir de sites tiers. Les identifiants ci-dessous correspondent aux scripts Python examinés.

| Domaine | Tableau | Fichier CSV / identifiant API | Sélection documentée |
| --- | --- | --- | --- |
| IPC | [18-10-0004-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=18100004) | `18100004` | `GEO=Canada`, groupe « All-items », séries non terminées |
| Taux d'intérêt | [10-10-0139-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=10100139) | `10100139` | Canada; taux directeur, taux bancaire, obligations 2/5/10 ans et bons du Trésor 3 mois |
| Devises | [33-10-0036-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=33100036) | `33100036` | Canada; USD, EUR, GBP, JPY, CHF, AUD |
| Emploi | [14-10-0287-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=14100287) | `14100287` | 5 caractéristiques, tous genres, 15 ans et plus, estimations désaisonnalisées |
| PIB | [36-10-0434-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=36100434) | `36100434` | Canada; ensemble, biens, services; données désaisonnalisées, dollars enchaînés de 2017 |
| Population | [17-10-0009-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=17100009) | `17100009` | Canada, dix provinces et trois territoires; unité « Persons » |

### Périmètre et transformation

1. Télécharger la source officielle au format CSV (directement ou par le service Web de Statistique Canada).
2. Filtrer les dimensions et exclure les observations terminées (`TERMINATED`).
3. Conserver les dates (`REF_DATE`), valeurs (`VALUE`), régions et unités pertinentes.
4. Convertir dates et nombres, éliminer les observations invalides et les doublons **dans le lot** selon la clé définie.
5. Charger les observations dans PostgreSQL; les modifications de valeurs publiées peuvent remplacer les valeurs précédentes pour la même clé.

**Fréquences des données :** IPC, emploi et PIB mensuels; population trimestrielle; taux d'intérêt et devises quotidiens. Une exécution ETL quotidienne ne crée pas artificiellement une observation chaque jour : elle recherche les nouvelles données **lorsqu'elles sont publiées**.

### Définition particulière de l'inflation annuelle

Le taux d'inflation annuel affiché est une **variation sur douze mois de l'IPC d'ensemble pour le Canada** :

`(IPC du mois / IPC du même mois un an avant - 1) × 100`, arrondi à **une décimale**. La vue SQL `inflation_yoy` calcule cette série à partir de la table `cpi`; elle ne constitue pas une septième source officielle.

### Réserves d'interprétation

Les dates de référence ne sont pas les dates du téléchargement. Les séries officielles peuvent être révisées et n'ont pas toutes la même fréquence; certaines unités diffèrent. Les filtres du projet rendent les comparaisons plus claires, sans prétendre remplacer l'ensemble des tableaux statistiques publiés.

---

## English

All six datasets originate from **Statistics Canada**. The table IDs are `18-10-0004-01` (all-items CPI for Canada), `10-10-0139-01` (six Canadian interest-rate series), `33-10-0036-01` (six currency series), `14-10-0287-01` (five seasonally adjusted labour indicators), `36-10-0434-01` (all/goods/services real GDP in chained 2017 dollars), and `17-10-0009-01` (population across Canada, provinces and territories). Source links and precise filters are listed above.

Each ETL step selects relevant dimensions, excludes terminated observations, converts dates and numeric values, removes invalid or repeated keys within the downloaded batch and upserts the results into PostgreSQL. A daily refresh checks for new official releases; it does not invent observations between release dates.

The year-over-year inflation series is **derived** from Canadian all-items CPI as `(current / same month last year - 1) × 100` rounded to **one decimal**, through the `inflation_yoy` SQL view; it is not a seventh independent Statistics Canada table. Different publication frequencies, units and data revisions are important limitations.
