# MSPR Big Data - Prédiction Électorale

**Projet EPSI - BLOC 3 RNCP35584**  
Machine Learning pour prédire les tendances électorales à partir d'indicateurs socio-économiques

## Objectif

Développer un modèle de Machine Learning supervisé capable de prédire les résultats électoraux sur un horizon de 1 à 3 ans en analysant des variables socio-économiques : sécurité, emploi, démographie, pauvreté, activité économique, logements.

## Contexte

Proof-of-Concept (POC) pour Electio-Analytics, start-up spécialisée dans le conseil stratégique pour campagnes électorales. Le projet utilise exclusivement des données publiques (data.gouv.fr, INSEE) pour créer un avantage concurrentiel via l'analyse prédictive.

## Stack Technique

- Python 3.11, pandas 2.1.4, scikit-learn
- Docker + Jupyter Lab
- Format Parquet pour données optimisées
- Visualisations : matplotlib, plotly, seaborn

## Structure du Projet

```
data/
  raw/       # Données sources (CSV/Excel)
  processed/ # Données nettoyées (Parquet)
  output/    # Résultats ML

notebooks/   # Pipeline de notebooks Jupyter
  00_setup.ipynb              # Validation environnement
  01_data_download.ipynb      # Téléchargement datasets
  02_exploration.ipynb        # Analyse exploratoire
  03_etl.ipynb                # Nettoyage et transformation
  04_features.ipynb           # Feature engineering
  05_modeling.ipynb           # Entraînement modèles ML

docs/        # Documentation détaillée
  CAHIER_DES_CHARGES.md       # Cahier des charges complet MSPR
  ARCHITECTURE.md             # Architecture technique
  DATASETS.md                 # Catalogue des datasets
```

## Démarrage

```bash
# Lancer l'environnement Docker
docker-compose up -d

# Accéder à Jupyter Lab
# http://localhost:8888
```

## Pipeline d'Exécution

Exécuter les notebooks dans l'ordre numérique :
1. `00_setup.ipynb` - Validation environnement
2. `01_data_download.ipynb` - Téléchargement données
3. `02_exploration.ipynb` - EDA et corrélations
4. `03_etl.ipynb` - Nettoyage et transformation
5. `04_features.ipynb` - Feature engineering
6. `05_modeling.ipynb` - ML supervisé + métriques

## Livrables

1. Données Parquet nettoyées et optimisées
2. Code commenté et reproductible
3. Modèle ML avec métriques (accuracy, précision, recall, F1)
4. Visualisations claires
5. Dossier de synthèse avec MCD et résultats

## Documentation

- [CAHIER_DES_CHARGES.md](docs/CAHIER_DES_CHARGES.md) - Cahier des charges complet
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture et choix techniques
- [DATASETS.md](docs/DATASETS.md) - Liste exhaustive des datasets

## Équipe

Projet MSPR TPRE813 - EPSI 2026
