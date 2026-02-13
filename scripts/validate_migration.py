"""
Script de validation post-migration Bronze/Silver/Gold
Vérifie que la structure Medallion Architecture est correcte
"""
from pathlib import Path
import sys
import os

# Ajouter racine projet au path (que le script soit lancé depuis racine ou scripts/)
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

try:
    from config import DATA_BRONZE, DATA_SILVER, DATA_GOLD, create_data_dirs
    config_imported = True
except ImportError as e:
    config_imported = False
    import_error = str(e)
    # Fallback si config.py pas trouvé
    DATA_BRONZE = Path("data/bronze")
    DATA_SILVER = Path("data/silver")
    DATA_GOLD = Path("data/gold")


def validate_structure():
    """Valider que structure Bronze/Silver/Gold est correcte"""
    print("=" * 70)
    print("🔍 VALIDATION MIGRATION - ARCHITECTURE MEDALLION (BRONZE/SILVER/GOLD)")
    print("=" * 70)
    print()
    
    issues = []
    warnings = []
    
    # Test 1: Import config.py
    if not config_imported:
        issues.append("❌ Impossible d'importer config.py")
        print("❌ Test 1/6 : Import config.py - ÉCHEC\n")
    else:
        print("✅ Test 1/6 : Import config.py - OK\n")
    
    # Test 2: Vérifier dossiers existent
    print("📂 Test 2/6 : Vérification structure dossiers\n")
    for layer_name, layer_path in [
        ("Bronze", DATA_BRONZE),
        ("Silver", DATA_SILVER),
        ("Gold", DATA_GOLD)
    ]:
        if not layer_path.exists():
            issues.append(f"❌ {layer_name}: {layer_path} n'existe pas")
            print(f"  ❌ {layer_name:8} : {layer_path} - MANQUANT")
        else:
            files = list(layer_path.glob("*"))
            file_count = len([f for f in files if f.name != '.gitkeep'])
            print(f"  ✅ {layer_name:8} : {layer_path} ({file_count} fichiers)")
    
    print()
    
    # Test 3: Vérifier fichiers critiques Bronze
    print("🥉 Test 3/6 : Vérification fichiers Bronze (données sources)\n")
    critical_bronze = [
        "elections_agregees_1999_2024.csv",
        "revenus_commune.csv",
        "referentiel_communes.csv"
    ]
    
    for filename in critical_bronze:
        filepath = DATA_BRONZE / filename
        if not filepath.exists():
            warnings.append(f"⚠️  Fichier critique manquant: {filename}")
            print(f"  ⚠️  {filename} - MANQUANT (à télécharger)")
        else:
            size_mb = filepath.stat().st_size / (1024*1024)
            print(f"  ✅ {filename:<40} ({size_mb:>6.1f} MB)")
    
    print()
    
    # Test 4: Vérifier .gitkeep présents
    print("📌 Test 4/6 : Vérification .gitkeep (Git tracking)\n")
    for layer_name, layer_path in [
        ("Bronze", DATA_BRONZE),
        ("Silver", DATA_SILVER),
        ("Gold", DATA_GOLD)
    ]:
        gitkeep = layer_path / ".gitkeep"
        if not gitkeep.exists():
            warnings.append(f"⚠️  .gitkeep manquant dans {layer_name}")
            print(f"  ⚠️  {layer_name}: .gitkeep manquant")
        else:
            print(f"  ✅ {layer_name}: .gitkeep présent")
    
    print()
    
    # Test 5: Vérifier anciens dossiers supprimés
    print("🗑️  Test 5/6 : Vérification suppression anciens dossiers\n")
    old_paths = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/output")
    ]
    
    old_found = False
    for old_path in old_paths:
        if old_path.exists():
            warnings.append(f"⚠️  Ancien dossier existe encore: {old_path} (à supprimer)")
            print(f"  ⚠️  {old_path} existe encore (migration incomplète)")
            old_found = True
    
    if not old_found:
        print("  ✅ Anciens dossiers (raw/processed/output) supprimés")
    
    print()
    
    # Test 6: Taille totale des données
    print("💾 Test 6/6 : Calcul volumétrie des données\n")
    for layer_name, layer_path in [
        ("Bronze", DATA_BRONZE),
        ("Silver", DATA_SILVER),
        ("Gold", DATA_GOLD)
    ]:
        if layer_path.exists():
            total_size = 0
            for file in layer_path.rglob("*"):
                if file.is_file() and file.name != '.gitkeep':
                    total_size += file.stat().st_size
            
            size_gb = total_size / (1024**3)
            size_mb = total_size / (1024**2)
            
            if size_gb > 0.1:
                print(f"  📊 {layer_name:8} : {size_gb:.2f} GB")
            else:
                print(f"  📊 {layer_name:8} : {size_mb:.1f} MB")
    
    print()
    
    # Résumé final
    print("=" * 70)
    print("📋 RÉSUMÉ DE LA VALIDATION")
    print("=" * 70)
    print()
    
    if issues:
        print("❌ ÉCHECS CRITIQUES :")
        for issue in issues:
            print(f"  {issue}")
        print()
    
    if warnings:
        print("⚠️  AVERTISSEMENTS :")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ VALIDATION RÉUSSIE - Structure Bronze/Silver/Gold OK !")
        print()
        print("🎉 Migration terminée avec succès :")
        print("   • Architecture Medallion en place")
        print("   • config.py importable")
        print("   • Structure Bronze/Silver/Gold conforme")
        print()
        print("📝 Prochaines étapes :")
        print("   1. Tester import config.py dans notebook")
        print("   2. Re-exécuter 01_data_download.ipynb")
        print("   3. Re-exécuter 02_exploration.ipynb")
        print()
        return True
    elif not issues:
        print("⚠️  VALIDATION PARTIELLE - Quelques avertissements")
        print("   La structure est correcte mais nécessite ajustements mineurs")
        print()
        return True
    else:
        print("❌ VALIDATION ÉCHOUÉE - Corrections nécessaires")
        print()
        return False


if __name__ == "__main__":
    success = validate_structure()
    sys.exit(0 if success else 1)
