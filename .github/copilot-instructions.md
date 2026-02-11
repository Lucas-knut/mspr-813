# MSPR-813 : ML Électoral

## Objectif
Modèle ML supervisé pour prédire tendances électorales (1-3 ans).

## Stack
Python 3.11, pandas 2.1.4, scikit-learn, openpyxl, matplotlib, plotly, seaborn.
Docker + Jupyter Lab. Parquet pour données traitées.
**IMPORTANT : pandas uniquement, PAS Spark.**

## Sources Données
- data.gouv.fr : élections, sécurité, emploi, démographie, économie, pauvreté
- INSEE : indicateurs socio-économiques

## Features/Indicateurs
Sécurité, emploi, vie associative, population, entreprises, pauvreté, CSP, revenus, logements.

## Étapes Projet
1. `01_data_download.ipynb` : Téléchargement datasets
2. `02_exploration.ipynb` : EDA + corrélations
3. `03_etl.ipynb` : Nettoyage + transformation
4. `04_features.ipynb` : Feature engineering
5. `05_modeling.ipynb` : ML supervisé (train/test split, accuracy, précision, recall, F1)
6. Visualisations : matplotlib/plotly/seaborn

## Architecture Fichiers
```
data/
  raw/       # CSV/Excel bruts (gitignore)
  processed/ # Parquet nettoyés (gitignore)
  output/    # Résultats ML (gitignore)
notebooks/   # Jupyter notebooks
```

## ML Approche
- Apprentissage supervisé
- Train/test split
- Prédictions 1/2/3 ans
- Métriques : accuracy, précision, recall, F1

## Règles Code
- **Minimaliste** : ne pas en faire trop, rester sur le strict nécessaire
- Code propre, commenté en français
- Pipeline ETL automatisé et traçable
- Nommage pertinent (tables/champs/variables)
- **Scalable** : code extensible pour ajout futur de communes/départements
- Pas d'icônes/emojis dans docs et commentaires
- Respect RGPD si données personnelles

## Livrables
1. Données Parquet nettoyées
2. Code commenté
3. Modèle ML + métriques
4. Visualisations claires
5. Questions réponses : donnée la plus corrélée, définition apprentissage supervisé, calcul accuracy
