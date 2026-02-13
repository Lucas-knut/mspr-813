"""
Configuration centralisée - Projet MSPR Big Data TPRE813
Architecture Bronze/Silver/Gold (Medallion Architecture)
"""
from pathlib import Path
import os

# Racine du projet (détecté automatiquement)
PROJECT_ROOT = Path(__file__).parent.absolute()

# === CHEMINS - MEDALLION ARCHITECTURE ===
# Bronze: Données brutes, immuables, format source
DATA_BRONZE = PROJECT_ROOT / "data" / "bronze"

# Silver: Données nettoyées, validées, format Parquet
DATA_SILVER = PROJECT_ROOT / "data" / "silver"

# Gold: Données agrégées, features ML, résultats finaux
DATA_GOLD = PROJECT_ROOT / "data" / "gold"

# === PARAMÈTRES MÉTIER ===
DEPARTEMENTS_PETITE_COURONNE = ['75', '92', '93', '94']
COMMUNES_PETITE_COURONNE_COUNT = 144  # Validé depuis données INSEE 2024

# === FORMATS & OPTIMISATION ===
PARQUET_ENGINE = 'pyarrow'
PARQUET_COMPRESSION = 'snappy'
CSV_ENCODING = 'utf-8'

# === SOURCES DE DONNÉES ===
DATA_SOURCES = {
    'elections': 'elections_agregees_1999_2024.csv',
    'revenus': 'revenus_commune.csv',
    'referentiel': 'referentiel_communes.csv',
    'population': 'population_historique_1968_2022/pop-16ans-dipl6822.xlsx',
    'diplomes': 'diplomes_formation_2022/base-cc-diplomes-formation-2022.xlsx',
    'csp': 'csp_actifs_2554/pop-act2554-csp-cd-6822.xlsx'
}

# === HELPERS ===
def create_data_dirs():
    """Créer structure de dossiers si nécessaire"""
    for path in [DATA_BRONZE, DATA_SILVER, DATA_GOLD]:
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {path}")

if __name__ == "__main__":
    print("📁 Structure de données - Medallion Architecture")
    print("=" * 60)
    create_data_dirs()
