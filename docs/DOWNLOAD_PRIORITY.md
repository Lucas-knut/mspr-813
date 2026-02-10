# 🎯 URLs Prioritaires - Téléchargement Rapide

## Phase 1 - PRIORITAIRE (Modèle de base)

### 1. Élections agrégées 1999-2024 ✨ CRITIQUE
```
https://www.data.gouv.fr/fr/datasets/r/ecbbe4b5-82b2-42a5-ada7-689e63f3f3b2
Fichier: candidats_results.txt (2.1 GB)
```

### 2. Revenus par commune
```
https://www.data.gouv.fr/fr/datasets/r/4f0e574c-6147-4dbb-a218-2d5f2c71cbc9
Fichier: revenu-des-francais-a-la-commune-*.csv (4.8 MB)
```

### 3. Référentiel communes INSEE
```
https://www.insee.fr/fr/statistiques/fichier/6800675/v_commune_2023.csv
Fichier: v_commune_2023.csv
```

### 4. Population historique 1876-2023
```
https://www.insee.fr/fr/statistiques/fichier/7739497/base-pop-historiques-1876-2023.xlsx
Fichier: base-pop-historiques-1876-2023.xlsx (6.7 MB)
```

---

## Phase 2 - IMPORTANT (Enrichissement)

### 5. Diplômes et formation 2022
```
https://www.insee.fr/fr/statistiques/fichier/8581488/base-cc-diplomes-formation-2022.zip
Fichier: base-cc-diplomes-formation-2022.CSV (81 MB dans ZIP)
```

### 6. CSP des actifs 25-54 ans
```
https://www.insee.fr/fr/statistiques/fichier/2012713/pop-act2554-csp-cd-6822.zip
Fichier: pop-act2554-csp-cd-6822.xlsx (28.5 MB dans ZIP)
```

### 7. Crimes et délits communaux
```
https://www.data.gouv.fr/fr/datasets/r/fa8312df-213b-4ba2-b82c-1bbd44cedd8f
Fichier: crimes_delits_communes.csv
```

### 8. Comptes communaux 2022
```
https://data.economie.gouv.fr/ → rechercher "comptes individuels communes 2022"
Fichier: comptes_communes_2022.csv (50 MB)
```

---

## Phase 3 - OPTIONNEL (Optimisation)

### 9. Catastrophes naturelles GASPAR
```
https://www.data.gouv.fr/fr/datasets/r/4c176fa2-b0cd-4780-b644-f34cecab89fb
Fichier: catnat_gaspar.csv (34.5 MB)
```

### 10. Présidentielle 2022 (détail)
```
Tour 1: https://www.data.gouv.fr/fr/datasets/r/aae19572-df6d-4e05-ab09-06430ca8acde
Tour 2: https://www.data.gouv.fr/fr/datasets/r/11a736be-748f-470b-b2c6-b8ba09b48938
```

### 11. Législatives 2024
```
https://www.data.gouv.fr/fr/datasets/r/bd32fcd3-53df-47ac-bf1d-8d8003fe23a1
Fichier: legislatives_2024_t1.csv (73.5 MB)
```

---

## 📝 Instructions de téléchargement

### Automatique (recommandé)
Utiliser le notebook : `notebooks/01_data_download.ipynb`

### Manuel
1. Clic droit sur chaque URL → "Enregistrer le lien sous..."
2. Sauvegarder dans : `data/raw/`
3. Dézipper si nécessaire

### Vérification
Lancer : `notebooks/01_data_download.ipynb` → section "Vérification des fichiers"