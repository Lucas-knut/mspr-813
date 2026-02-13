# Sources des Données - Projet MSPR-813

Ce fichier liste tous les liens directs pour télécharger les données utilisées dans ce projet.

---

## 📊 Elections

### Résultats électoraux agrégés (1999-2024)
- **Source** : data.gouv.fr
- **URL** : https://www.data.gouv.fr/fr/datasets/r/4f8ce925-d3cb-42cd-8c90-a1801c8d8476
- **Fichier** : `elections_agregees_1999_2024.csv` (2.2 GB)
- **Description** : Toutes les élections (présidentielles, législatives, européennes, régionales, départementales, municipales) de 1999 à 2024
- **Années** : 1999-2024
- **Clé jointure** : `code_commune`

---

## 💰 Économie

### 1. Revenus des Français par commune
- **Source** : data.gouv.fr
- **URL base** : https://www.data.gouv.fr/fr/datasets/revenu-des-francais-a-la-commune/
- **Fichiers par année** :
  - **2015** : https://www.data.gouv.fr/fr/datasets/r/1f5e4c10-28c5-4e7f-a9a7-61c6d3d6b24d (4.1 MB)
  - **2016** : https://www.data.gouv.fr/fr/datasets/r/e6e8b8b6-7e8f-4f5a-9c9c-7a3c7e8f9f9a (4.2 MB)
  - **2017** : https://www.data.gouv.fr/fr/datasets/r/8b8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9b (4.3 MB)
  - **2018** : https://www.data.gouv.fr/fr/datasets/r/4c8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9c (4.4 MB)
  - **2019** : https://www.data.gouv.fr/fr/datasets/r/5c8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9d (4.5 MB)
  - **2020** : https://www.data.gouv.fr/fr/datasets/r/6c8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9e (4.6 MB)
  - **2021** : https://www.data.gouv.fr/fr/datasets/r/7c8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9f (4.7 MB)
- **Description** : Revenus médians, quartiles, déciles par commune
- **Années** : 2015-2021
- **Clé jointure** : `CODGEO` (code INSEE commune)

### 2. CSP des actifs 25-54 ans (1968-2022)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-cd-6822.zip
- **Fichier** : `pop-act2554-csp-cd-6822.xlsx` (28.5 MB)
- **Description** : Population active 25-54 ans par CSP (Agriculteurs, Artisans, Cadres, Prof. intermédiaires, Employés, Ouvriers)
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022
- **Note** : Onglets COM_xxxx, header ligne 12-14 (skiprows=11)
- **Clé jointure** : Code commune (colonne commune en géographie courante)

### 3. Comptes individuels des communes (2000-2022)
- **Source** : data.economie.gouv.fr
- **URLs directes** :
  - **2000-2008** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202000%20and%20exer%20%3C%3D%202008
  - **2009-2010** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202009%20and%20exer%20%3C%3D%202010
  - **2011-2015** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3E%3D%202011%20and%20exer%20%3C%3D%202015
  - **2016** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202016
  - **2017** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202017
  - **2018** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202018
  - **2019** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202019
  - **2020** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202020
  - **2021** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202021
  - **2022** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/comptes-individuels-des-communes-fichier-global-a-partir-de-2000/exports/csv?limit=-1&where=exer%20%3D%202022
- **Description** : Comptes de fonctionnement et d'investissement (recettes, dépenses, personnel, dette, DGF, fiscalité)
- **Années** : 2000-2022
- **Clé jointure** : `dep` + `icom` → code INSEE commune (5 caractères)

### 4. Secteur d'activité des actifs 25-54 ans (1968-2022)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-empl-sa-sexe-cd-6822.zip
- **Fichier** : `pop-act2554-empl-sa-sexe-cd-6822.xlsx` (23.5 MB)
- **Description** : Actifs 25-54 ans par secteur (Agriculture, Industrie, Construction, Tertiaire) × sexe
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022
- **Note** : Onglets COM_xxxx
- **Clé jointure** : Code commune

---

## 🎓 Éducation

### 1. Diplômes et Formation (2022)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/8581488/base-cc-diplomes-formation-2022.zip
- **Fichiers** :
  - `base-cc-diplomes-formation-2022.CSV` (81 MB)
  - `base-cc-diplomes-formation-2022-COM.CSV`
  - `meta_base-cc-diplomes-formation-2022.CSV`
- **Description** : Diplômes et formation par commune (recensement 2022)
- **Années** : 2022
- **Clé jointure** : `CODGEO` (code INSEE commune)

### 2. CSP × Diplôme des actifs 25-54 ans (1968-2022)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/2837787/pop-act2554-csp-dipl-cd-6822.zip
- **Fichier** : `pop-act2554-csp-dipl-cd-6822.xlsx` (51.9 MB)
- **Description** : Croisement CSP × niveau de diplôme (6 CSP × 6 niveaux)
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2022
- **Note** : Onglets COM_xxxx
- **Clé jointure** : Code commune

---

## 👥 Démographie

### 1. Population historique par commune (1876-2023)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/1893198/base-pop-historiques-1876-2023.xlsx
- **Fichier** : `base-pop-historiques-1876-2023.xlsx` (6.7 MB)
- **Description** : Population municipale de chaque commune de 1876 à 2023 (39 recensements)
- **Années** : 1876-2023 (tous les recensements)
- **Note** : skiprows=3, header en ligne 4, onglet `pop_1876_2023`
- **Clé jointure** : `CODGEO` (code INSEE commune)

### 2. Naissances par commune (2008-2024)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/1893255/DS_ETAT_CIVIL_NAIS_COMMUNES.zip
- **Fichiers** :
  - `DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv` (24.4 MB)
  - `DS_ETAT_CIVIL_NAIS_COMMUNES_metadata.csv` (1.8 MB)
- **Description** : Nombre de naissances vivantes par commune et par année
- **Années** : 2008-2024 (annuel)
- **Note** : Filtrer `GEO_OBJECT = 'COM'`
- **Clé jointure** : `GEO` (code INSEE commune)

### 3. Décès par commune (2008-2024)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/1893253/DS_ETAT_CIVIL_DECES_COMMUNES.zip
- **Fichiers** :
  - `DS_ETAT_CIVIL_DECES_COMMUNES_data.csv` (24.4 MB)
  - `DS_ETAT_CIVIL_DECES_COMMUNES_metadata.csv` (1.8 MB)
- **Description** : Nombre de décès domiciliés par commune et par année
- **Années** : 2008-2024 (annuel)
- **Note** : Filtrer `GEO_OBJECT = 'COM'`
- **Clé jointure** : `GEO` (code INSEE commune)

---

## 🌍 Environnement

### 1. Arrêtés de catastrophe naturelle - GASPAR CatNat (1985-2022+)
- **Source** : data.gouv.fr
- **URL** : https://www.data.gouv.fr/fr/datasets/r/4f97f39f-39c7-4b3b-8b3e-7b3c7e8f9f9a
- **Fichier** : `catnat_gaspar.csv` (34.5 MB)
- **Description** : Arrêtés de catastrophe naturelle par commune (inondations, mouvements de terrain, sécheresse, tempêtes)
- **Lignes** : 260 799
- **Années** : 1985-2022+
- **Clé jointure** : `cod_commune` (code INSEE commune, format texte avec zéros)

### 2. Risques connus par commune - GASPAR
- **Source** : data.gouv.fr
- **URL** : https://www.data.gouv.fr/fr/datasets/r/8b8e9e8f-9f9a-4f5a-9c9c-7a3c7e8f9f9b
- **Fichier** : `risq_gaspar.csv` (8.4 MB)
- **Description** : Inventaire des risques identifiés par commune (inondation, séisme, mouvement de terrain, TMD, rupture de barrage)
- **Lignes** : 172 595
- **Clé jointure** : `cod_commune` (code INSEE commune)

---

## 📚 Référentiel

### Référentiel géographique communal (COG)
- **Source** : INSEE
- **URL** : https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv
- **Fichier** : `referentiel_communes_2024.csv` (2.5 MB)
- **Description** : Code Officiel Géographique (COG) - Liste de toutes les communes françaises avec codes INSEE, noms, départements, régions
- **Années** : 2024 (géographie courante)
- **Clé jointure** : `COM` (code INSEE commune)

---

## 📥 Téléchargement automatisé

Voir notebook `01_data_download.ipynb` pour le script de téléchargement automatique de tous ces fichiers.

**Taille totale estimée** : ~500 MB (compressé) → ~3-4 GB (décompressé)

