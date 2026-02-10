# MSPR-813 : Prévision Électorale

## Contexte
POC Electio-Analytics : prédire tendances électorales 1-3 ans via ML supervisé.
Zone : Petite Couronne (75, 92, 93, 94). Données : ~2.4 GB.

## Stack
Python 3.11, pandas 2.1.4, scikit-learn, openpyxl, Docker, Jupyter Lab, Parquet.
IMPORTANT : Sujet mentionne pandas, PAS Spark.

## Sources Données
data.gouv.fr : élections, sécurité, emploi, démographie, économie, pauvreté. INSEE : indicateurs socio-éco.

## Indicateurs
Sécurité, emploi, vie associative, population, entreprises, pauvreté, CSP, revenus, logements.

## Pipeline
1. Téléchargement (01_data_download.ipynb)
2. Exploration/corrélations (02_exploration.ipynb)
3. ETL/nettoyage (03_etl.ipynb)
4. Feature engineering (04_features.ipynb)
5. Modèle ML supervisé (05_modeling.ipynb)
6. Visualisations (matplotlib/plotly)

## Architecture
data/raw/ (CSV/Excel), data/processed/ (Parquet), data/output/ (résultats ML).
Git : data/ dans .gitignore (2.4 GB, JAMAIS commit).

## Livrables MSPR
1. Données nettoyées (Parquet)
2. Code commenté
3. Modèle ML + accuracy
4. Visualisations claires
5. Dossier synthèse : justification zone, corrélations, MCD, résultats, réponses questions (donnée la plus corrélée, définition apprentissage supervisé, calcul accuracy)

## ML Supervisé
Train/test split, prédictions 1/2/3 ans, métriques : accuracy, précision, recall, F1.

## Règles Code
- Rester minimaliste, ne pas en faire trop
- Suivre strictement ce qui est demandé dans le sujet MSPR
- Code propre, commenté en français
- Pipeline ETL automatisé et traçable
- Nommage pertinent tables/champs
- Respect RGPD si données personnelles
