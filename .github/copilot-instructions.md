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

## Étapes Projet (Pipeline Notebooks)
1. `01_data_download.ipynb` : Téléchargement → Bronze
2. `02_exploration.ipynb` : EDA + corrélations (Bronze → Silver)
3. `03_etl.ipynb` : Nettoyage + transformation (Bronze → Silver)
4. `04_features.ipynb` : Feature engineering (Silver → Gold)
5. `05_modeling.ipynb` : ML supervisé (Gold)
6. `06_predictions.ipynb` : Prédictions finales (Gold)
7. Visualisations : matplotlib/plotly/seaborn

## Architecture Données - Medallion (Bronze/Silver/Gold)

```
data/
  bronze/    # 🥉 Données brutes (CSV/Excel) - Immuables, format source
  silver/    # 🥈 Données nettoyées (Parquet) - Validées, typées
  gold/      # 🥇 Résultats ML (Parquet/JSON) - Business-ready

config.py    # Configuration centralisée (chemins, paramètres)
```

**Documentation complète** : `docs/DATA_ARCHITECTURE.md`

### Import Obligatoire (Notebooks)

```python
# En début de notebook (après imports pandas/numpy)
import sys
sys.path.append('..')
from config import DATA_BRONZE, DATA_SILVER, DATA_GOLD
```

**RÈGLES** :
- ❌ Ne JAMAIS écrire chemins en dur : `Path("/app/data/raw")` → INTERDIT
- ✅ Toujours utiliser `config.py` : `DATA_BRONZE`, `DATA_SILVER`, `DATA_GOLD`
- ✅ Bronze : Données immuables (read-only après téléchargement)
- ✅ Silver : Peut être régénéré depuis Bronze (idempotence)
- ✅ Gold : Tables finales ML, versionner modèles

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
