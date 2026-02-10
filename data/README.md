# Données du Projet

## 📂 Structure

```
data/
├── raw/           # Données brutes téléchargées (non versionnées)
├── processed/     # Données nettoyées et transformées (non versionnées)
└── output/        # Résultats finaux (non versionnés)
```

## ⚠️ Important : Données non versionnées

Les fichiers de données **ne sont PAS inclus** dans le dépôt Git pour les raisons suivantes :
- **Taille** : ~2.4 GB pour Phase 1 (trop volumineux pour GitHub)
- **Reproductibilité** : Les données sources sont publiques et téléchargeables
- **Évolutivité** : Permet de regénérer avec données à jour

## 📥 Téléchargement des Données

### Option 1 : Notebook automatique (Recommandé)

1. Démarrer l'environnement Docker :
   ```bash
   docker-compose up -d
   ```

2. Ouvrir Jupyter Lab : http://127.0.0.1:8888/lab

3. Exécuter le notebook : `notebooks/01_data_download.ipynb`
   - Télécharge automatiquement tous les datasets Phase 1
   - Extrait les fichiers ZIP
   - Vérifie l'intégrité des données

### Option 2 : Téléchargement manuel

Consulter la documentation : `docs/DATASETS.md` pour les URLs complètes.

**Datasets Phase 1 (POC Petite Couronne) :**

1. **Élections agrégées 1999-2024** (2.2 GB)
   - Source : data.gouv.fr
   - Placer dans `data/raw/elections_agregees_1999_2024.csv`

2. **Revenus par commune** (4.8 MB)
   - Source : data.gouv.fr
   - Placer dans `data/raw/revenus_commune.csv`

3. **Référentiel communes** (3 MB)
   - Source : INSEE
   - Placer dans `data/raw/referentiel_communes.csv`

4. **Population historique** (40 MB, ZIP)
   - Source : INSEE
   - Extraire dans `data/raw/population_historique_1968_2022/`

5. **Diplômes et formation** (81 MB, ZIP)
   - Source : INSEE
   - Extraire dans `data/raw/diplomes_formation_2022/`

6. **CSP actifs 25-54 ans** (28.5 MB, ZIP)
   - Source : INSEE
   - Extraire dans `data/raw/csp_actifs_2554/`

## 📊 Formats

- **Entrée (raw/)** : CSV, Excel (XLSX)
- **Traité (processed/)** : Parquet (compression + performance)
- **Sortie (output/)** : Parquet, CSV

## 🔒 Sécurité

- Les données sont **publiques** (open data)
- Aucune donnée personnelle ou sensible
- Sources officielles : INSEE, data.gouv.fr

## 📝 Documentation

- **URLs complètes** : `docs/DATASETS.md`
- **Priorités de téléchargement** : `docs/DOWNLOAD_PRIORITY.md`
- **Architecture** : `docs/ARCHITECTURE.md`
