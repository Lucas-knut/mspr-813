#!/usr/bin/env python3
"""
Script de téléchargement robuste des données historiques INSEE et data.gouv.fr
Avec retry automatique et User-Agent pour éviter les erreurs HTTP 500

Ce script télécharge automatiquement :
  - Naissances 2008-2024 (INSEE)
  - Décès 2008-2024 (INSEE)
  - CSP Actifs 1968-2022 (INSEE)
  - Secteur d'activité 1968-2022 (INSEE)
  - Diplômes 2022 (INSEE)

FICHIERS À FOURNIR MANUELLEMENT (non disponibles via URL publique) :
  - elections_agregees_1999_2024.csv   (~2.35 GB) → à placer dans data/bronze/
  - revenus_commune.csv                           → à placer dans data/bronze/
  - referentiel_communes_2024.csv                 → à placer dans data/bronze/referentiels_cog/

Usage : docker exec mspr_python python3 /app/scripts/download_robust.py
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
    """
    Télécharge un fichier avec retry automatique et User-Agent.
    
    Args:
        url: URL du fichier
        destination: Chemin de destination
        description: Description pour la barre de progression
        force: Forcer le téléchargement même si le fichier existe
        max_retries: Nombre maximum de tentatives
    
    Returns:
        bool: True si succès, False sinon
    """
    destination = Path(destination)
    
    # Vérifier si le fichier existe déjà
    if destination.exists() and not force:
        size_mb = destination.stat().st_size / 1e6
        print(f"⏭️  {destination.name} existe déjà ({size_mb:.2f} MB) - SKIP")
        return True
    
    # Headers avec User-Agent pour éviter les blocages
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    # Retry avec backoff exponentiel
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = 2 ** (attempt - 1)  # 2, 4, 8 secondes
                print(f"⏳ Tentative {attempt}/{max_retries} après {wait_time}s...")
                time.sleep(wait_time)
            
            print(f"📥 {description}... ", end='', flush=True)
            
            # Télécharger avec streaming
            response = requests.get(url, stream=True, timeout=180, headers=headers)
            response.raise_for_status()
            
            # Taille totale
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Téléchargement avec ou sans tqdm
            if HAS_TQDM:
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
                # Sans tqdm - affichage simple du pourcentage
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
                destination.unlink()  # Supprimer fichier partiel
            
            # Ne pas retry sur 404 ou 403
            if e.response.status_code in [404, 403]:
                print(f"   URL: {url}")
                return False
            
            # Retry sur 500, 502, 503, 504
            if attempt < max_retries and e.response.status_code >= 500:
                continue
            return False
            
        except Exception as e:
            print(f"\r❌ Erreur: {e}" + " " * 20)
            if destination.exists():
                destination.unlink()  # Supprimer fichier partiel
            
            if attempt < max_retries:
                continue
            return False
    
    return False


def download_and_extract_zip(url, extract_to, description="Téléchargement ZIP", force=False, max_retries=3):
    """
    Télécharge et extrait un fichier ZIP avec retry automatique.
    
    Args:
        url: URL du fichier ZIP
        extract_to: Dossier de destination
        description: Description pour la barre de progression
        force: Forcer le téléchargement même si les fichiers existent
        max_retries: Nombre maximum de tentatives
    
    Returns:
        bool: True si succès, False sinon
    """
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    
    # Vérifier si déjà extrait (au moins 1 fichier dans le dossier)
    if not force and any(extract_to.iterdir()):
        print(f"⏭️  {extract_to.name} déjà extrait - SKIP")
        return True
    
    # Headers avec User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/zip,*/*',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # Retry avec backoff exponentiel
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                wait_time = 2 ** (attempt - 1)
                print(f"⏳ Tentative {attempt}/{max_retries} après {wait_time}s...")
                time.sleep(wait_time)
            
            print(f"📥 {description}...")
            response = requests.get(url, timeout=120, headers=headers)
            response.raise_for_status()
            
            # Extraire le ZIP en mémoire
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
    """Télécharge toutes les données historiques."""
    
    print("=" * 60)
    print("📥 TÉLÉCHARGEMENT ROBUSTE DES DONNÉES HISTORIQUES")
    print("=" * 60)
    print(f"\n✅ Projet : {PROJECT_ROOT}")
    print(f"✅ Bronze : {DATA_BRONZE}\n")
    
    all_success = True
    
    # ==========================================
    # PHASE 2 - DÉMOGRAPHIE
    # ==========================================
    print("\n" + "=" * 60)
    print("👥 PHASE 2 - DÉMOGRAPHIE HISTORIQUE")
    print("=" * 60 + "\n")
    
    # 2.1 - Population 1876-2023
    print("🚀 2.1 - Population historique 1876-2023\n")
    url_population = "https://www.insee.fr/fr/statistiques/fichier/1893198/base-pop-historiques-1876-2023.xlsx"
    destination_pop = DATA_BRONZE / "population_historique_1876_2023.xlsx"
    success = download_file(url_population, destination_pop, "Population 1876-2023")
    all_success = all_success and success
    time.sleep(1)
    
    # 2.2 - Naissances 2008-2024
    print("\n🚀 2.2 - Naissances 2008-2024\n")
    url_naissances = "https://www.insee.fr/fr/statistiques/fichier/1893255/DS_ETAT_CIVIL_NAIS_COMMUNES.zip"
    destination_naissances = DATA_BRONZE / "naissances_2008_2024"
    success = download_and_extract_zip(url_naissances, destination_naissances, "Naissances 2008-2024")
    all_success = all_success and success
    time.sleep(1)
    
    # 2.3 - Décès 2008-2024
    print("\n🚀 2.3 - Décès 2008-2024\n")
    url_deces = "https://www.insee.fr/fr/statistiques/fichier/1893253/DS_ETAT_CIVIL_DECES_COMMUNES.zip"
    destination_deces = DATA_BRONZE / "deces_2008_2024"
    success = download_and_extract_zip(url_deces, destination_deces, "Décès 2008-2024")
    all_success = all_success and success
    time.sleep(1)
    
    # ==========================================
    # PHASE 3 - ÉCONOMIE
    # ==========================================
    print("\n" + "=" * 60)
    print("💼 PHASE 3 - ÉCONOMIE ET EMPLOI")
    print("=" * 60 + "\n")
    
    # 3.1 - CSP Actifs
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
    # PHASE 4 - ÉDUCATION
    # ==========================================
    print("\n" + "=" * 60)
    print("🎓 PHASE 4 - ÉDUCATION ET FORMATION")
    print("=" * 60 + "\n")
    
    # 4.1 - Diplômes
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
    
    # Calculer la taille totale
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
