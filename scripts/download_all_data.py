#!/usr/bin/env python3
"""
Script de téléchargement automatique de toutes les données historiques.
Option B - Téléchargement COMPLET (~3.5 GB)
"""

from pathlib import Path
import requests
from zipfile import ZipFile
from io import BytesIO
import time
import shutil
import sys

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_BRONZE = PROJECT_ROOT / 'data' / 'bronze'
DATA_BRONZE.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("🚀 TÉLÉCHARGEMENT ÉTENDU DES DONNÉES HISTORIQUES")
print("=" * 60)
print(f"\n📁 Projet : {PROJECT_ROOT}")
print(f"📁 Bronze : {DATA_BRONZE}\n")


def download_file(url, destination, description="Téléchargement", force=False):
    """Télécharge un fichier avec gestion d'erreurs."""
    destination = Path(destination)
    
    if destination.exists() and not force:
        size_mb = destination.stat().st_size / 1e6
        print(f"⏭️  {destination.name} existe déjà ({size_mb:.2f} MB) - SKIP")
        return True
    
    try:
        print(f"📥 {description}... ", end='', flush=True)
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📥 {description}... {percent:.1f}%", end='', flush=True)
        
        size_mb = destination.stat().st_size / 1e6
        print(f"\r✅ {destination.name} téléchargé ({size_mb:.2f} MB)" + " " * 20)
        return True
        
    except Exception as e:
        print(f"\r❌ Erreur: {e}" + " " * 20)
        if destination.exists():
            destination.unlink()
        return False


def download_and_extract_zip(url, extract_to, description="Téléchargement ZIP", force=False):
    """Télécharge et extrait un ZIP."""
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    
    if not force and any(extract_to.iterdir()):
        print(f"⏭️  {extract_to.name} déjà extrait - SKIP")
        return True
    
    try:
        print(f"📥 {description}... ", end='', flush=True)
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        with ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(extract_to)
        
        files_count = len(list(extract_to.rglob('*')))
        print(f"\r✅ {files_count} fichiers extraits dans {extract_to.name}" + " " * 20)
        return True
        
    except Exception as e:
        print(f"\r❌ Erreur: {e}" + " " * 20)
        return False


def download_cog_millesimes(years, destination_folder, force=False):
    """Télécharge les référentiels COG pour plusieurs millésimes."""
    destination_folder = Path(destination_folder)
    destination_folder.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # URLs par année
    url_configs = {
        2024: ("https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv", "csv"),
        2023: ("https://www.insee.fr/fr/statistiques/fichier/6800675/v_commune_2023.csv", "csv"),
        2022: ("https://www.insee.fr/fr/statistiques/fichier/6051727/v_commune_2022.csv", "csv"),
        2021: ("https://www.insee.fr/fr/statistiques/fichier/5057840/v_commune_2021.csv", "csv"),
        2020: ("https://www.insee.fr/fr/statistiques/fichier/4316069/v_commune_2020.csv", "csv"),
        2019: ("https://www.insee.fr/fr/statistiques/fichier/3720946/v_commune_2019.csv", "csv"),
        2018: ("https://www.insee.fr/fr/statistiques/fichier/3363419/comsimp2018.zip", "zip"),
        2017: ("https://www.insee.fr/fr/statistiques/fichier/2666684/comsimp2017.zip", "zip"),
        2016: ("https://www.insee.fr/fr/statistiques/fichier/2114819/comsimp2016.zip", "zip"),
        2015: ("https://www.insee.fr/fr/statistiques/fichier/2560698/comsimp2015.zip", "zip"),
        2014: ("https://www.insee.fr/fr/statistiques/fichier/2560563/comsimp2014.zip", "zip"),
        2013: ("https://www.insee.fr/fr/statistiques/fichier/2560615/comsimp2013.zip", "zip"),
        2012: ("https://www.insee.fr/fr/statistiques/fichier/2560620/comsimp2012.zip", "zip"),
        2011: ("https://www.insee.fr/fr/statistiques/fichier/2560625/comsimp2011.zip", "zip"),
        2010: ("https://www.insee.fr/fr/statistiques/fichier/2560630/comsimp2010.zip", "zip"),
        2009: ("https://www.insee.fr/fr/statistiques/fichier/2560635/comsimp2009.zip", "zip"),
        2008: ("https://www.insee.fr/fr/statistiques/fichier/2560640/comsimp2008.zip", "zip"),
        2007: ("https://www.insee.fr/fr/statistiques/fichier/2560646/comsimp2007.zip", "zip"),
        2006: ("https://www.insee.fr/fr/statistiques/fichier/2560651/comsimp2006.zip", "zip"),
        2005: ("https://www.insee.fr/fr/statistiques/fichier/2560656/comsimp2005.zip", "zip"),
        2004: ("https://www.insee.fr/fr/statistiques/fichier/2560661/comsimp2004.zip", "zip"),
        2003: ("https://www.insee.fr/fr/statistiques/fichier/2560666/comsimp2003.zip", "zip"),
        2002: ("https://www.insee.fr/fr/statistiques/fichier/2560671/comsimp2002.zip", "zip"),
        2001: ("https://www.insee.fr/fr/statistiques/fichier/2560676/comsimp2001.zip", "zip"),
        2000: ("https://www.insee.fr/fr/statistiques/fichier/2560681/comsimp2000.zip", "zip"),
        1999: ("https://www.insee.fr/fr/statistiques/fichier/2560686/comsimp1999.zip", "zip"),
    }
    
    for year in years:
        if year not in url_configs:
            print(f"❌ Année {year} non supportée")
            results[year] = False
            continue
        
        url, file_type = url_configs[year]
        destination = destination_folder / f"referentiel_communes_{year}.csv"
        
        if file_type == "csv":
            results[year] = download_file(url, destination, f"COG {year}", force)
        else:  # ZIP
            temp_folder = destination_folder / f"temp_cog_{year}"
            if download_and_extract_zip(url, temp_folder, f"COG {year}", force):
                csv_files = list(temp_folder.glob('*.csv'))
                if csv_files:
                    csv_files[0].rename(destination)
                    shutil.rmtree(temp_folder)
                    results[year] = True
                else:
                    print(f"❌ Aucun CSV trouvé dans le ZIP {year}")
                    results[year] = False
            else:
                results[year] = False
        
        time.sleep(0.5)
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n📊 Résumé COG : {success_count}/{len(results)} millésimes téléchargés\n")
    
    return results


# ================== PHASE 1 - RÉFÉRENTIELS COG ==================
print("\n" + "=" * 60)
print("📋 PHASE 1 - RÉFÉRENTIELS COG (1999-2024)")
print("=" * 60 + "\n")

cog_folder = DATA_BRONZE / 'referentiels_cog'
cog_results = download_cog_millesimes(range(1999, 2025), cog_folder)

# ================== PHASE 2 - DÉMOGRAPHIE ==================
print("\n" + "=" * 60)
print("👥 PHASE 2 - DÉMOGRAPHIE HISTORIQUE")
print("=" * 60 + "\n")

# 2.1 - Population 1876-2023
print("📥 Phase 2.1 - Population historique\n")
download_file(
    "https://www.insee.fr/fr/statistiques/fichier/1893198/base-pop-historiques-1876-2023.xlsx",
    DATA_BRONZE / "population_historique_1876_2023.xlsx",
    "Population 1876-2023"
)

# 2.2 - Naissances
print("\n📥 Phase 2.2 - Naissances\n")
download_and_extract_zip(
    "https://www.insee.fr/fr/statistiques/fichier/1893255/DS_ETAT_CIVIL_NAIS_COMMUNES.zip",
    DATA_BRONZE / "naissances_2008_2024",
    "Naissances 2008-2024"
)

# 2.3 - Décès
print("\n📥 Phase 2.3 - Décès\n")
download_and_extract_zip(
    "https://www.insee.fr/fr/statistiques/fichier/1893253/DS_ETAT_CIVIL_DECES_COMMUNES.zip",
    DATA_BRONZE / "deces_2008_2024",
    "Décès 2008-2024"
)

# ================== PHASE 3 - ÉCONOMIE ==================
print("\n" + "=" * 60)
print("💼 PHASE 3 - ÉCONOMIE ET EMPLOI")
print("=" * 60 + "\n")

# 3.1 - CSP Actifs
print("📥 Phase 3.1 - CSP Actifs\n")
csp_folder = DATA_BRONZE / "csp_actifs_2554"
if csp_folder.exists() and any(csp_folder.iterdir()):
    print("⏭️  CSP Actifs déjà téléchargé - SKIP\n")
else:
    download_and_extract_zip(
        "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-cd-6822.zip",
        csp_folder,
        "CSP Actifs 1968-2022"
    )

# 3.2 - Secteur activité
print("\n📥 Phase 3.2 - Secteur d'activité\n")
download_and_extract_zip(
    "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-empl-sa-sexe-cd-6822.zip",
    DATA_BRONZE / "secteur_activite_1968_2022",
    "Secteur activité 1968-2022"
)

# 3.3 - Comptes communes
print("\n📥 Phase 3.3 - Comptes communes (GROS FICHIERS)\n")
print("⚠️  Téléchargement priorité 1 et 2 uniquement (2011-2022)")
print("    Modifier MAX_PRIORITY pour télécharger 2000-2010\n")

comptes_folder = DATA_BRONZE / "comptes_communes"
comptes_folder.mkdir(parents=True, exist_ok=True)

comptes_tranches = [
    (1, "2022", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202022", "comptes_communes_2022.csv"),
    (1, "2021", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202021", "comptes_communes_2021.csv"),
    (1, "2020", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202020", "comptes_communes_2020.csv"),
    (1, "2019", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202019", "comptes_communes_2019.csv"),
    (1, "2018", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202018", "comptes_communes_2018.csv"),
    (1, "2017", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202017", "comptes_communes_2017.csv"),
    (2, "2011-2015", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202011%20and%20exer%20%3C%3D%202015", "comptes_communes_2011_2015.csv"),
    (2, "2016", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202016", "comptes_communes_2016.csv"),
    (3, "2000-2008", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202000%20and%20exer%20%3C%3D%202008", "comptes_communes_2000_2008.csv"),
    (3, "2009-2010", "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202009%20and%20exer%20%3C%3D%202010", "comptes_communes_2009_2010.csv"),
]

MAX_PRIORITY = 2

for priority, years, url, filename in comptes_tranches:
    if priority > MAX_PRIORITY:
        print(f"⏭️  {years} - Priorité {priority} - SKIP")
        continue
    
    destination = comptes_folder / filename
    download_file(url, destination, f"Comptes {years}")
    time.sleep(2)

# ================== PHASE 4 - ÉDUCATION ==================
print("\n" + "=" * 60)
print("🎓 PHASE 4 - ÉDUCATION ET FORMATION")
print("=" * 60 + "\n")

# 4.1 - Diplômes
print("📥 Phase 4.1 - Diplômes\n")
diplomes_folder = DATA_BRONZE / "diplomes_formation_2022"
if diplomes_folder.exists() and any(diplomes_folder.iterdir()):
    print("⏭️  Diplômes 2022 déjà téléchargé - SKIP\n")
else:
    download_and_extract_zip(
        "https://www.insee.fr/fr/statistiques/fichier/8581488/base-cc-diplomes-formation-2022.zip",
        diplomes_folder,
        "Diplômes 2022"
    )

# 4.2 - CSP × Diplôme
print("\n📥 Phase 4.2 - CSP × Diplôme\n")
download_and_extract_zip(
    "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-dipl-cd-6822.zip",
    DATA_BRONZE / "csp_diplome_1968_2022",
    "CSP × Diplôme 1968-2022"
)

# ================== RÉCAPITULATIF ==================
print("\n" + "=" * 60)
print("📊 RÉCAPITULATIF FINAL")
print("=" * 60 + "\n")

def get_folder_size(folder):
    """Calcule la taille d'un dossier en GB."""
    total = 0
    for dirpath, dirnames, filenames in folder.walk():
        for f in filenames:
            fp = dirpath / f
            if fp.exists():
                total += fp.stat().st_size
    return total / 1e9

bronze_size = get_folder_size(DATA_BRONZE)

print(f"📁 Dossier Bronze : {DATA_BRONZE}")
print(f"💾 Taille totale : {bronze_size:.2f} GB\n")

categories = {
    "Référentiels COG": DATA_BRONZE / "referentiels_cog",
    "Population historique": DATA_BRONZE / "population_historique_1876_2023.xlsx",
    "Naissances": DATA_BRONZE / "naissances_2008_2024",
    "Décès": DATA_BRONZE / "deces_2008_2024",
    "CSP Actifs": DATA_BRONZE / "csp_actifs_2554",
    "Secteur activité": DATA_BRONZE / "secteur_activite_1968_2022",
    "Comptes communes": DATA_BRONZE / "comptes_communes",
    "Diplômes": DATA_BRONZE / "diplomes_formation_2022",
    "CSP × Diplôme": DATA_BRONZE / "csp_diplome_1968_2022",
}

print("📦 Données téléchargées :\n")
for name, path in categories.items():
    if path.exists():
        if path.is_dir():
            files_count = len(list(path.rglob('*')))
            size = get_folder_size(path)
            print(f"  ✅ {name:<25} {files_count:>3} fichiers - {size:.2f} GB")
        else:
            size = path.stat().st_size / 1e9
            print(f"  ✅ {name:<25} 1 fichier - {size:.2f} GB")
    else:
        print(f"  ❌ {name:<25} Non téléchargé")

print("\n" + "=" * 60)
print("🎉 TÉLÉCHARGEMENT TERMINÉ !")
print("=" * 60)
print("\n📌 Prochaines étapes :")
print("  1. Exécuter notebooks/02_exploration.ipynb")
print("  2. Créer notebooks/03_etl.ipynb (Bronze → Silver)")
print("  3. Feature engineering (Silver → Gold)")
print("  4. Modélisation ML\n")
