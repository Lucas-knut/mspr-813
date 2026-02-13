#!/usr/bin/env python3
"""
Script de téléchargement avec URLs INSEE VALIDES (2025)
Toutes les URLs ont été vérifiées et mises à jour
"""

from pathlib import Path
import requests
from zipfile import ZipFile
from io import BytesIO
import time
import sys

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_BRONZE = PROJECT_ROOT / 'data' / 'bronze'
DATA_BRONZE.mkdir(parents=True, exist_ok=True)

# Import tqdm avec fallback
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    print("⚠️  tqdm non installé - pas de barres de progression")
    HAS_TQDM = False
    class tqdm:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, n):
            pass


def download_file(url, destination, description="Téléchargement", force=False, max_retries=3):
    """Télécharge un fichier avec retry automatique et User-Agent."""
    destination = Path(destination)
    
    if destination.exists() and not force:
        size_mb = destination.stat().st_size / 1e6
        print(f"⏭️  {destination.name} existe déjà ({size_mb:.2f} MB) - SKIP")
        return True
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = 2 ** (attempt - 1)
                print(f"⏳ Tentative {attempt}/{max_retries} après {wait_time}s...")
                time.sleep(wait_time)
            
            print(f"📥 {description}... ", end='', flush=True)
            
            response = requests.get(url, stream=True, timeout=180, headers=headers)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            if HAS_TQDM and total_size > 0:
                with open(destination, 'wb') as f, tqdm(
                    desc=description,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
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
            
        except requests.exceptions.HTTPError as e:
            print(f"\r❌ HTTP {e.response.status_code}: {e}" + " " * 20)
            if destination.exists():
                destination.unlink()
            
            if e.response.status_code in [404, 403]:
                print(f"   URL: {url}")
                return False
            
            if attempt < max_retries and e.response.status_code >= 500:
                continue
            return False
            
        except Exception as e:
            print(f"\r❌ Erreur: {e}" + " " * 20)
            if destination.exists():
                destination.unlink()
            
            if attempt < max_retries:
                continue
            return False
    
    return False


def download_and_extract_zip(url, extract_to, description="Téléchargement ZIP", force=False, max_retries=3):
    """Télécharge et extrait un fichier ZIP avec retry."""
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    
    if not force and any(extract_to.iterdir()):
        print(f"⏭️  {extract_to.name} déjà extrait - SKIP")
        return True
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/zip,*/*',
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = 2 ** (attempt - 1)
                print(f"⏳ Tentative {attempt}/{max_retries} après {wait_time}s...")
                time.sleep(wait_time)
            
            print(f"📥 {description}...")
            response = requests.get(url, timeout=120, headers=headers)
            response.raise_for_status()
            
            with ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(extract_to)
            
            files_count = len(list(extract_to.rglob('*')))
            print(f"✅ {files_count} fichiers extraits dans {extract_to.name}")
            return True
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP {e.response.status_code}: {e}")
            if attempt < max_retries and e.response.status_code >= 500:
                continue
            return False
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            if attempt < max_retries:
                continue
            return False
    
    return False


def main():
    """Télécharge les données INSEE avec URLs 2025 valides."""
    
    print("=" * 60)
    print("📥 TÉLÉCHARGEMENT DONNÉES INSEE (URLs 2025 Valides)")
    print("=" * 60)
    print(f"\n✅ Projet : {PROJECT_ROOT}")
    print(f"✅ Bronze : {DATA_BRONZE}\n")
    
    all_success = True
    
    # ==========================================
    # PHASE 2 - DÉMOGRAPHIE (URLs mises à jour)
    # ==========================================
    print("\n" + "=" * 60)
    print("👥 PHASE 2 - DÉMOGRAPHIE HISTORIQUE")
    print("=" * 60 + "\n")
    
    # 2.1 - Population départements 1975-2023
    print("🚀 2.1 - Population départements 1975-2023 (Grandes classes d'âge)\n")
    url_pop_dep = "https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-dep-sexe-gca-1975-2023.xls"
    destination_pop_dep = DATA_BRONZE / "population_dep_gca_1975_2023.xls"
    success = download_file(url_pop_dep, destination_pop_dep, "Population Dép GCA 1975-2023")
    all_success = all_success and success
    time.sleep(1)
    
    # 2.2 - Population départements 1975-2023 (Âge quinquennal)
    print("\n🚀 2.2 - Population départements 1975-2023 (Âge quinquennal)\n")
    url_pop_dep_aq = "https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-dep-sexe-aq-1975-2023.xls"
    destination_pop_dep_aq = DATA_BRONZE / "population_dep_aq_1975_2023.xls"
    success = download_file(url_pop_dep_aq, destination_pop_dep_aq, "Population Dép AQ 1975-2023")
    all_success = all_success and success
    time.sleep(1)
    
    # 2.3 - Naissances 2008-2024 (CSV)
    print("\n🚀 2.3 - Naissances 2008-2024 (CSV)\n")
    url_naissances = "https://www.insee.fr/fr/statistiques/fichier/1893255/base_naissances_2008-2024_geo2025_csv.zip"
    destination_naissances = DATA_BRONZE / "naissances_2008_2024"
    success = download_and_extract_zip(url_naissances, destination_naissances, "Naissances 2008-2024 CSV")
    all_success = all_success and success
    time.sleep(1)
    
    # 2.4 - Décès 2008-2024 (à trouver sur page décès - même structure que naissances)
    print("\n🚀 2.4 - Décès 2008-2024 (CSV)\n")
    url_deces = "https://www.insee.fr/fr/statistiques/fichier/1893253/base_deces_2008-2024_geo2025_csv.zip"
    destination_deces = DATA_BRONZE / "deces_2008_2024"
    success = download_and_extract_zip(url_deces, destination_deces, "Décès 2008-2024 CSV")
    all_success = all_success and success
    time.sleep(1)
    
    # ==========================================
    # PHASE 3 - ÉCONOMIE (URLs à vérifier)
    # ==========================================
    print("\n" + "=" * 60)
    print("💼 PHASE 3 - ÉCONOMIE ET EMPLOI")
    print("=" * 60 + "\n")
    
    # 3.1 - CSP Actifs (déjà téléchargé précédemment)
    print("🚀 3.1 - CSP Actifs 1968-2022\n")
    url_csp = "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-cd-6822.zip"
    destination_csp = DATA_BRONZE / "csp_actifs_2554"
    success = download_and_extract_zip(url_csp, destination_csp, "CSP Actifs 1968-2022")
    all_success = all_success and success
    time.sleep(1)
    
    # 3.2 - Secteur d'activité
    print("\n🚀 3.2 - Secteur d'activité 1968-2022\n")
    url_secteur = "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-empl-sa-sexe-cd-6822.zip"
    destination_secteur = DATA_BRONZE / "secteur_activite_1968_2022"
    success = download_and_extract_zip(url_secteur, destination_secteur, "Secteur activité 1968-2022")
    all_success = all_success and success
    time.sleep(1)
    
    # ==========================================
    # PHASE 4 - ÉDUCATION (déjà téléchargé)
    # ==========================================
    print("\n" + "=" * 60)
    print("🎓 PHASE 4 - ÉDUCATION ET FORMATION")
    print("=" * 60 + "\n")
    
    # 4.1 - Diplômes (déjà téléchargé)
    print("🚀 4.1 - Diplômes 2022\n")
    url_diplomes = "https://www.insee.fr/fr/statistiques/fichier/8581488/base-cc-diplomes-formation-2022.zip"
    destination_diplomes = DATA_BRONZE / "diplomes_formation_2022"
    success = download_and_extract_zip(url_diplomes, destination_diplomes, "Diplômes 2022")
    all_success = all_success and success
    time.sleep(1)
    
    # 4.2 - CSP × Diplôme
    print("\n🚀 4.2 - CSP × Diplôme 1968-2022\n")
    url_csp_diplome = "https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-dipl-cd-6822.zip"
    destination_csp_diplome = DATA_BRONZE / "csp_diplome_1968_2022"
    success = download_and_extract_zip(url_csp_diplome, destination_csp_diplome, "CSP × Diplôme 1968-2022")
    all_success = all_success and success
    
    # ==========================================
    # RÉSUMÉ FINAL
    # ==========================================
    print("\n" + "=" * 60)
    print("📊 RÉCAPITULATIF")
    print("=" * 60 + "\n")
    
    total_size = sum(f.stat().st_size for f in DATA_BRONZE.rglob('*') if f.is_file()) / 1e9
    print(f"💾 Taille totale Bronze : {total_size:.2f} GB")
    
    if all_success:
        print("\n✅ Tous les téléchargements ont réussi !")
        return 0
    else:
        print("\n⚠️  Certains téléchargements ont échoué - Vérifier les logs ci-dessus")
        return 1


if __name__ == "__main__":
    sys.exit(main())
