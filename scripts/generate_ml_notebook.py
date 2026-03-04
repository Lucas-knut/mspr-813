#!/usr/bin/env python3
"""Generate the modeling notebook 06_modeling.ipynb"""
import json
import os

cells = []

def md(source):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    })

def code(source):
    cells.append({
        "cell_type": "code",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")],
        "outputs": [],
        "execution_count": None
    })

# ============================================================
md("""# 06 - Modélisation ML : Prédiction blocs électoraux 2025-2027

**Objectif** : Prédire le `bloc_dominant` (Gauche / Centre / Droite) par commune pour 2025-2027.

**Données** : `gold.features_communes` — ~720 lignes, ~144 communes × 5 années (2002-2022)

**Améliorations** :
- ~30 features (ajout : revenus IRCOM, emploi, insécurité, immigration, population, ratios)
- Fusion ExtremeDroite+Droite → "Droite" (seulement 2 samples ED en train)
- Walk-forward validation (2012→2017→2022)
- Random Forest + Gradient Boosting""")

# ============================================================
md("## 0. Configuration & imports")

code("""import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

PG_HOST     = os.environ.get('POSTGRES_HOST',     'postgres')
PG_PORT     = os.environ.get('POSTGRES_PORT',     '5432')
PG_DB       = os.environ.get('POSTGRES_DB',       'mspr813')
PG_USER     = os.environ.get('POSTGRES_USER',     'mspr_user')
PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'mspr_password')

DB_URL = f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
engine = create_engine(DB_URL, pool_pre_ping=True)

print('PostgreSQL OK :', engine.connect().execute(text('SELECT current_database()')).scalar())""")

# ============================================================
md("## 1. Chargement et préparation des données Gold")

code("""df = pd.read_sql('SELECT * FROM gold.features_communes ORDER BY code_commune, annee', engine)

print(f'Shape : {df.shape}')
print(f'Communes : {df["code_commune"].nunique()}')
print(f'Années   : {sorted(df["annee"].unique())}')
print(f'Blocs    : {df["bloc_dominant"].value_counts().to_dict()}')

# Fusion ExtremeDroite + Droite → Droite (trop peu de samples ED)
n_ed = (df['bloc_dominant'] == 'ExtremeDroite').sum()
print(f'\\nExtremeDroite samples : {n_ed} → fusionnés avec Droite')
df['bloc_dominant'] = df['bloc_dominant'].replace('ExtremeDroite', 'Droite')

# Fusionner aussi les % : pct_droite = pct_droite + pct_extremedroite
df['pct_droite'] = df['pct_droite'] + df['pct_extremedroite']

# Recalculer bloc_dominant après fusion
blocs_cols = ['pct_gauche', 'pct_centre', 'pct_droite']
bloc_labels = ['Gauche', 'Centre', 'Droite']
df['bloc_dominant'] = df[blocs_cols].idxmax(axis=1).map(dict(zip(blocs_cols, bloc_labels)))

print(f'\\nDistribution après fusion :')
print(df['bloc_dominant'].value_counts().to_string())""")

# ============================================================
md("## 2. Feature Engineering temporel")

code("""df = df.sort_values(['code_commune', 'annee']).reset_index(drop=True)

# Lag : résultat de l'élection précédente
for col in ['pct_gauche', 'pct_centre', 'pct_droite']:
    df[f'{col}_lag1'] = df.groupby('code_commune')[col].shift(1)

# Tendance : évolution vs t-1
for col in ['pct_gauche', 'pct_centre', 'pct_droite']:
    df[f'{col}_trend'] = df[col] - df[f'{col}_lag1']

# Bloc dominant à t-1
df['bloc_lag1'] = df.groupby('code_commune')['bloc_dominant'].shift(1)

print(f'Shape après features temporelles : {df.shape}')

# Définir les features
FEATURES = [
    # Lags électoraux
    'pct_gauche_lag1', 'pct_centre_lag1', 'pct_droite_lag1',
    # Tendances
    'pct_gauche_trend', 'pct_centre_trend', 'pct_droite_trend',
    # Démographie
    'population', 'nb_naissances', 'nb_deces', 'solde_naturel',
    'taux_natalite', 'taux_mortalite',
    # Revenus IRCOM
    'revenu_moyen_par_foyer', 'taux_imposition',
    # Emploi
    'taux_chomage',
    # CSP
    'cadres_pct', 'ouvriers_pct', 'employes_pct', 'artisans_pct',
    'ratio_cadres_ouvriers',
    # Diplômes
    'pct_bac_plus', 'pct_sans_diplome',
    # Insécurité & immigration (département)
    'taux_crimes_mille', 'pct_immigres',
    # Géographie
    'is_paris', 'is_93',
    # Temporel
    'annee',
]

# Garder uniquement les features qui existent dans le DataFrame
FEATURES = [f for f in FEATURES if f in df.columns]
print(f'Features disponibles : {len(FEATURES)}')

TARGET = 'bloc_dominant'

# Supprimer les lignes sans lag
df_ml = df[df['bloc_lag1'].notna()].copy()

# Convertir booléens en int
for col in ['is_paris', 'is_93']:
    if col in df_ml.columns:
        df_ml[col] = df_ml[col].astype(int)

print(f'Lignes avec lag : {len(df_ml)} (années : {sorted(df_ml["annee"].unique())})')""")

# ============================================================
md("""## 3. Walk-forward validation

Au lieu d'un seul split, on évalue sur chaque année de test successivement :
- Train ≤ 2012 → Test 2017
- Train ≤ 2017 → Test 2022""")

code("""def train_evaluate(df_ml, features, target, train_max_year, test_year, model_cls, model_params):
    \"\"\"Entraîne et évalue un modèle avec split temporel.\"\"\"
    df_train = df_ml[df_ml['annee'] <= train_max_year].copy()
    df_test  = df_ml[df_ml['annee'] == test_year].copy()

    if len(df_train) == 0 or len(df_test) == 0:
        return None, None, None

    X_train, y_train = df_train[features], df_train[target]
    X_test,  y_test  = df_test[features],  df_test[target]

    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('model', model_cls(**model_params))
    ])
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    return acc, pipeline, classification_report(y_test, y_pred, zero_division=0)

# Walk-forward : évaluer sur 2017 et 2022
rf_params = dict(n_estimators=200, max_depth=8, min_samples_leaf=3,
                 class_weight='balanced', random_state=42, n_jobs=-1)
gbm_params = dict(n_estimators=200, max_depth=4, learning_rate=0.05,
                  subsample=0.8, random_state=42)

print("=" * 60)
print("WALK-FORWARD VALIDATION")
print("=" * 60)

results = []
for test_year, train_max in [(2017, 2012), (2022, 2017)]:
    print(f"\\n--- Train ≤ {train_max} → Test {test_year} ---")

    acc_rf, pipe_rf, report_rf = train_evaluate(
        df_ml, FEATURES, TARGET, train_max, test_year,
        RandomForestClassifier, rf_params)
    acc_gbm, pipe_gbm, report_gbm = train_evaluate(
        df_ml, FEATURES, TARGET, train_max, test_year,
        GradientBoostingClassifier, gbm_params)

    print(f"  Random Forest:       {acc_rf:.3f}")
    print(f"  Gradient Boosting:   {acc_gbm:.3f}")
    results.append({'test_year': test_year, 'rf': acc_rf, 'gbm': acc_gbm})

df_results_wf = pd.DataFrame(results)
print(f"\\nMoyenne RF:  {df_results_wf['rf'].mean():.3f}")
print(f"Moyenne GBM: {df_results_wf['gbm'].mean():.3f}")""")

# ============================================================
md("## 4. Modèle final : entraîné sur toutes les données ≤ 2017, test = 2022")

code("""df_train = df_ml[df_ml['annee'] <= 2017].copy()
df_test  = df_ml[df_ml['annee'] == 2022].copy()

print(f'Train : {len(df_train)} lignes | années : {sorted(df_train["annee"].unique())}')
print(f'Test  : {len(df_test)} lignes | années : {sorted(df_test["annee"].unique())}')
print(f'\\nDistribution target train :')
print(df_train[TARGET].value_counts().to_string())
print(f'\\nDistribution target test :')
print(df_test[TARGET].value_counts().to_string())

X_train, y_train = df_train[FEATURES], df_train[TARGET]
X_test,  y_test  = df_test[FEATURES],  df_test[TARGET]

# Random Forest
rf_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('model', RandomForestClassifier(**rf_params))
])
rf_pipeline.fit(X_train, y_train)
y_pred_rf = rf_pipeline.predict(X_test)
acc_rf = accuracy_score(y_test, y_pred_rf)

print(f'\\nRandom Forest — Accuracy test 2022 : {acc_rf:.3f}')
print(classification_report(y_test, y_pred_rf, zero_division=0))

# Gradient Boosting
gbm_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('model', GradientBoostingClassifier(**gbm_params))
])
gbm_pipeline.fit(X_train, y_train)
y_pred_gbm = gbm_pipeline.predict(X_test)
acc_gbm = accuracy_score(y_test, y_pred_gbm)

print(f'Gradient Boosting — Accuracy test 2022 : {acc_gbm:.3f}')
print(classification_report(y_test, y_pred_gbm, zero_division=0))

# Choisir le meilleur
best_name = 'RandomForest' if acc_rf >= acc_gbm else 'GradientBoosting'
best_pipeline = rf_pipeline if acc_rf >= acc_gbm else gbm_pipeline
best_acc = max(acc_rf, acc_gbm)
print(f'\\nMeilleur modèle : {best_name} (accuracy={best_acc:.3f})')""")

# ============================================================
code("""# Feature importance
if best_name == 'RandomForest':
    imp = best_pipeline.named_steps['model'].feature_importances_
else:
    imp = best_pipeline.named_steps['model'].feature_importances_

feat_imp = pd.Series(imp, index=FEATURES).sort_values(ascending=False)
print('Top 15 features :')
print(feat_imp.head(15).round(4).to_string())""")

# ============================================================
md("""## 5. Prédictions 2025-2027

Extrapolation des tendances 2017→2022 pour chaque commune.
- Lag = valeurs 2022
- Tendance = extrapolation linéaire
- Features structurelles = constantes 2022""")

code("""df_2022 = df[df['annee'] == 2022].copy()
df_2017 = df[df['annee'] == 2017].copy().set_index('code_commune')

print(f'Communes 2022 : {len(df_2022)}')

predictions_rows = []

for target_year in [2025, 2026, 2027]:
    scale = (target_year - 2022) / 5.0

    for _, row in df_2022.iterrows():
        comm = row['code_commune']

        def get_trend(col):
            if comm in df_2017.index and pd.notna(row.get(col)) and pd.notna(df_2017.loc[comm].get(col)):
                return float(row[col]) - float(df_2017.loc[comm][col])
            return 0.0

        def extrap(col):
            val = row.get(col, np.nan)
            return float(val) + get_trend(col) * scale if pd.notna(val) else np.nan

        feat_row = {'_code_commune': comm, '_libelle': row.get('libelle', ''),
                    '_code_dep': row.get('code_dep', ''), '_target_year': target_year}

        # Lags = valeurs 2022
        for col in ['pct_gauche', 'pct_centre', 'pct_droite']:
            feat_row[f'{col}_lag1'] = row.get(col, np.nan)
            feat_row[f'{col}_trend'] = get_trend(col) * scale

        # Features statiques ou extrapolées
        for col in FEATURES:
            if col not in feat_row:
                if col == 'annee':
                    feat_row[col] = target_year
                elif col in ['population', 'nb_naissances', 'nb_deces', 'solde_naturel',
                             'taux_natalite', 'taux_mortalite']:
                    feat_row[col] = extrap(col)
                else:
                    feat_row[col] = row.get(col, np.nan)

        predictions_rows.append(feat_row)

df_pred_input = pd.DataFrame(predictions_rows)

# Convertir booléens
for col in ['is_paris', 'is_93']:
    if col in df_pred_input.columns:
        df_pred_input[col] = df_pred_input[col].astype(float)

X_pred = df_pred_input[FEATURES]
y_pred_future = best_pipeline.predict(X_pred)
y_pred_proba  = best_pipeline.predict_proba(X_pred)
classes = best_pipeline.classes_

df_preds = df_pred_input[['_code_commune','_libelle','_code_dep','_target_year']].copy()
df_preds.columns = ['code_commune','libelle','code_dep','annee']
df_preds['bloc_predit'] = y_pred_future

for i, cls in enumerate(classes):
    df_preds[f'prob_{cls.lower()}'] = y_pred_proba[:, i].round(3)

print(f'Prédictions : {len(df_preds)} lignes')
for yr in [2025, 2026, 2027]:
    sub = df_preds[df_preds['annee'] == yr]
    print(f'\\n{yr} :')
    print(sub['bloc_predit'].value_counts().to_string())""")

# ============================================================
md("## 6. Sauvegarde en base")

code("""with engine.begin() as conn:
    conn.execute(text(\"\"\"
        DROP TABLE IF EXISTS gold.predictions_2025_2027;
        CREATE TABLE gold.predictions_2025_2027 (
            code_commune    CHAR(5)      NOT NULL,
            libelle         VARCHAR(100),
            code_dep        CHAR(3),
            annee           SMALLINT     NOT NULL,
            bloc_predit     VARCHAR(20)  NOT NULL,
            prob_gauche     NUMERIC(6,4),
            prob_centre     NUMERIC(6,4),
            prob_droite     NUMERIC(6,4),
            modele          VARCHAR(30),
            created_at      TIMESTAMP DEFAULT NOW(),
            CONSTRAINT pk_pred PRIMARY KEY (code_commune, annee)
        );
    \"\"\"))

df_preds['modele'] = best_name

for col in ['prob_gauche', 'prob_centre', 'prob_droite']:
    if col not in df_preds.columns:
        df_preds[col] = np.nan

insert_cols = ['code_commune','libelle','code_dep','annee','bloc_predit',
               'prob_gauche','prob_centre','prob_droite','modele']
df_preds[insert_cols].to_sql('predictions_2025_2027', engine, schema='gold',
                              if_exists='append', index=False, method='multi', chunksize=500)

with engine.connect() as conn:
    n = conn.execute(text('SELECT COUNT(*) FROM gold.predictions_2025_2027')).scalar()
print(f'gold.predictions_2025_2027 : {n} lignes')""")

# ============================================================
md("## 7. Résultats finaux")

code("""print('=' * 65)
print('RÉSULTATS MODÉLISATION')
print('=' * 65)
print(f'  Random Forest    — accuracy test 2022 : {acc_rf:.3f}')
print(f'  Gradient Boosting — accuracy test 2022 : {acc_gbm:.3f}')
print(f'  Modèle retenu : {best_name}')
print(f'  Nombre de features : {len(FEATURES)}')
print()

for yr in [2025, 2026, 2027]:
    sub = df_preds[df_preds['annee'] == yr]
    dist = sub['bloc_predit'].value_counts()
    print(f'  {yr} — {len(sub)} communes :')
    for bloc, cnt in dist.items():
        print(f'       {bloc:15s} : {cnt} ({cnt/len(sub)*100:.1f}%)')
    print()

print('=' * 65)

# Prédictions 2027 par département
pred_2027 = df_preds[df_preds['annee'] == 2027]
print('\\nPrédictions 2027 par département :')
print(pred_2027.groupby(['code_dep', 'bloc_predit']).size().unstack(fill_value=0).to_string())""")

# ============================================================
# Build notebook
# ============================================================
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"}
    },
    "cells": cells
}

for cell in notebook["cells"]:
    if cell["source"] and cell["source"][-1].endswith("\n"):
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "notebooks", "06_modeling.ipynb")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook écrit : {output_path}")
print(f"Nombre de cellules : {len(cells)}")
