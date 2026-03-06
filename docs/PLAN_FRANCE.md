# Extension — Petite Couronne → France Métropolitaine

> **Status : TERMINE.** Le pipeline France est entièrement implémenté et exécuté.
> Ce document conserve les choix d'architecture pour référence.

## Contexte

Extension du pipeline ML MSPR-813 de **144 communes** (départements 75, 92, 93, 94)
vers **~35 000 communes** de France métropolitaine (départements 01-95 + 2A/2B).

Les fichiers Bronze couvrent toute la France — aucun re-téléchargement nécessaire.
Deux schémas parallèles ont été créés dans PostgreSQL.

---

## Stratégie : Migration parallèle (2 schémas)

Les schémas existants `silver` et `gold` sont **conservés** (Petite Couronne).
Les nouveaux schémas `silver_france` et `gold_france` sont créés en parallèle.

```
PostgreSQL (mspr813)
├── silver/              → Petite Couronne (existant, 144 communes)
├── silver_france/       → France métropolitaine (nouveau, ~35k communes)
├── gold/                → Petite Couronne (existant, 620 lignes)
├── gold_france/         → France métropolitaine (nouveau, ~150k lignes)
└── metabase/            → Métadonnées Metabase
```

---

## Volumétrie estimée

| Composant | Petite Couronne | France métro | Ratio |
|-----------|----------------|--------------|-------|
| Communes | 144 | ~35 000 | ×243 |
| `silver.elections` | 1.5M lignes | ~365M lignes | ×243 |
| `silver.csp` | 143 lignes | ~35k lignes | ×245 |
| `silver.diplomes` | 123 lignes | ~30k lignes | ×244 |
| `gold.features_communes` | 620 lignes (124×5) | ~150k lignes (30k×5) | ×242 |
| `gold.predictions_2025_2027` | 372 lignes (124×3) | ~90k lignes (30k×3) | ×242 |
| Volume PostgreSQL | ~500 MB | ~12-15 GB | ×24-30 |

---

## Étapes d'implémentation

### Étape 1 — Schémas SQL France `init_db_france.sql` ✅ FAIT

**Fichier** : `scripts/init_db_france.sql`

---

### Étape 2 — ETL Bronze → Silver France ✅ FAIT

**Fichier** : `notebooks/france/04_etl_bronze_to_postgres.ipynb`

Modifications clés :

1. **Filtres départements** — France métropolitaine uniquement :
```python
DEPS_METRO = [f'{i:02d}' for i in range(1, 96)] + ['2A', '2B']
DEPS_METRO = [d for d in DEPS_METRO if d != '20']  # 20 fusionné en 2A/2B

df_ref  = df_ref[df_ref['DEP'].isin(DEPS_METRO)]
df_elec = df_elec[df_elec['code_commune'].str[:2].isin(DEPS_METRO)]
# etc. pour chaque dataset
```

2. **Schémas cibles** : `silver_france.*` (au lieu de `silver.*`)

3. **Chargement par chunks** (volumétrie élections) :
```python
df_elec.to_sql(
    'elections', engine,
    schema='silver_france',
    if_exists='append',
    index=False,
    method='multi',
    chunksize=10000
)
```

4. **Imputation manquantes** (communes rurales sans CSP/diplômes/revenus) :
```python
# Médiane départementale en priorité, médiane nationale en fallback
for col in numeric_cols:
    df[col] = df.groupby('code_dep')[col].transform(
        lambda x: x.fillna(x.median())
    )
df.fillna(df.median(numeric_only=True), inplace=True)
```

Volumétrie attendue :
- `silver_france.referentiel_communes` : ~35 000 lignes
- `silver_france.elections` : ~365M lignes (20-30 min de chargement)
- `silver_france.csp` : ~35 000 lignes
- `silver_france.diplomes` : ~30 000 lignes
- `silver_france.naissances` / `deces` : ~250 000 lignes chacune
- `silver_france.revenus` : ~34 000 lignes

Temps d'exécution estimé : **20-30 min**

---

### Étape 3 — Feature Engineering ✅ FAIT

**Fichier** : `notebooks/france/05_feature_engineering.ipynb`

Modifications clés :

1. **Schémas** : sources `silver_france.*`, cible `gold_france.features_communes`

2. **Calcul de la typologie territoire** (nouveau) :
```python
# Seuils grille densité INSEE
def get_typologie(densite):
    if densite >= 1500:
        return 'urbain'
    elif densite >= 50:
        return 'periurbain'
    else:
        return 'rural'

df_ref['densite'] = df_ref['population'] / df_ref['superficie_km2']
df_ref['typologie_territoire'] = df_ref['densite'].apply(get_typologie)
```

Distribution attendue :
- Urbain : ~10% des communes (~3 500)
- Périurbain : ~30% (~10 000)
- Rural : ~60% (~21 000)

3. **Agrégation électorale optimisée** (CTE materialized) :
```sql
WITH elections_presidentielles AS MATERIALIZED (
    SELECT code_commune, annee, nuance_liste, SUM(nb_voix) AS voix
    FROM silver_france.elections
    WHERE id_election LIKE 'PR%T1'
    GROUP BY code_commune, annee, nuance_liste
)
SELECT ...
```

Volumétrie attendue :
- `gold_france.features_communes` : ~150 000 lignes (30k communes × 5 années)
- Colonnes : 24 features + `typologie_territoire`

Temps d'exécution estimé : **15-20 min**

---

### Étape 4 — Modélisation ML ✅ FAIT

**Fichier** : `notebooks/france/06_modeling.ipynb`

Modifications clés :

1. **Schéma source** : `gold_france.features_communes`
2. **Schéma cible** : `gold_france.predictions_2025_2027`

3. **Features enrichies** (ajout typologie) :
```python
FEATURES = [
    # Lag + tendances (×8)
    'pct_gauche_lag1', 'pct_centre_lag1', 'pct_droite_lag1', 'pct_extremedroite_lag1',
    'pct_gauche_trend', 'pct_centre_trend', 'pct_droite_trend', 'pct_extremedroite_trend',
    # CSP (×4)
    'cadres_pct', 'ouvriers_pct', 'employes_pct', 'artisans_pct',
    # Diplomes (×2)
    'pct_bac_plus', 'pct_sans_diplome',
    # Demographie (×3)
    'nb_naissances', 'nb_deces', 'solde_naturel',
    # Temporel (×1)
    'annee',
    # Territoire (×1, one-hot encodé)
    'typologie_territoire',
]
```

4. **Pipeline avec one-hot encoding** :
```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), ['typologie_territoire']),
    ('num', SimpleImputer(strategy='median'), numeric_features)
])

rf_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=20,
        min_samples_leaf=10,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    ))
])
```

5. **Accuracy par typologie** (validation) :
```python
for typo in ['urbain', 'periurbain', 'rural']:
    mask = df_test['typologie_territoire'] == typo
    acc = accuracy_score(y_test[mask], y_pred[mask])
    print(f'Accuracy {typo}: {acc:.3f}')
```

Résultats attendus :
- Accuracy globale test 2022 : **55-65%** (vs 64.5% Petite Couronne)
- `typologie_territoire` dans le top 5 des feature importances
- Distribution prédictions 2027 : Gauche ~50-60%, Droite ~20-30%, Centre ~10-15%, ExtremeDroite ~5-10%

Temps d'exécution estimé : **10-20 min**

---

### Étape 5 — Visualisations Metabase

Dashboards à créer après exécution du pipeline :

1. **Dashboard comparatif Petite Couronne vs France**
   - Blocs 2022 : `gold.features_communes` vs `gold_france.features_communes`
   - Histogrammes distribution blocs côte-à-côte

2. **Dashboard France par typologie**
   - Blocs prédits 2027 par type de territoire (urbain / périurbain / rural)
   - Évolution Gauche/Droite/Centre/ExtremeDroite 2002-2027 par typologie
   - Bar chart distribution blocs × département

3. **Dashboard départemental (interactif)**
   - Sélecteur département (dropdown)
   - Table top communes par probabilité `bloc_predit`
   - Carte zoom département

4. **Dashboard ML Performance**
   - Confusion matrix (table croisée)
   - Feature importances (bar chart horizontal)
   - Accuracy par typologie

---

## Fichiers créés / modifiés

| Fichier | Action | Étape |
|---------|--------|-------|
| `docs/PLAN_FRANCE.md` | Créé | - |
| `scripts/init_db_france.sql` | Créé | Étape 1 |
| `notebooks/france/04_etl_bronze_to_postgres.ipynb` | Créé | Étape 2 |
| `notebooks/france/05_feature_engineering.ipynb` | Créé | Étape 3 |
| `notebooks/france/06_modeling.ipynb` | Créé | Étape 4 |
| Dashboards Metabase | A configurer | Étape 5 |
| `scripts/init_db.sql` | Non modifié | - |
| `docker-compose.yml` | Non modifié | - |
| `notebooks/04-06 originaux` | Non modifiés | - |

---

## Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| OOM durant chargement élections (~365M lignes) | Moyenne | Bloquant | `chunksize=10000` dans `to_sql()` |
| Temps exécution > 60 min | Haute | Mineur | Patience, exécuter hors heures de travail si nécessaire |
| Accuracy ML < 50% (diversité urbain/rural) | Moyenne | Modéré | Feature `typologie_territoire` + hyperparamètres ajustés |
| Espace disque insuffisant (~15 GB supplémentaires) | Faible | Bloquant | Vérifier `df -h` avant lancement |
| Requêtes Metabase lentes sur 365M lignes élections | Haute | Mineur | Index + vues matérialisées agrégées |

---

## Commandes utiles

```bash
# Vérifier espace disque disponible
df -h

# Suivre l'avancement du chargement PostgreSQL
docker exec mspr_postgres psql -U mspr_user -d mspr813 \
  -c "SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10;"

# Taille des schémas
docker exec mspr_postgres psql -U mspr_user -d mspr813 \
  -c "SELECT schema_name, pg_size_pretty(sum(table_size)) AS size
      FROM (SELECT table_schema AS schema_name,
                   pg_total_relation_size(quote_ident(table_schema)||'.'||quote_ident(table_name)) AS table_size
            FROM information_schema.tables) t
      GROUP BY schema_name ORDER BY sum(table_size) DESC;"
```
