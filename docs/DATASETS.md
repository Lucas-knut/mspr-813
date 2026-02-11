# Sources de données pour le projet MSPR

## Données Électorales

### Résultats électoraux agrégés (RECOMMANDÉ)
- **Toutes élections 1999-2024** : https://www.data.gouv.fr/datasets/donnees-des-elections-agregees
- **Fichier** : candidats_results.txt (2.1 GB)
- **Contenu** : Présidentielles, législatives, européennes, régionales, départementales, municipales
- **Clé** : Code département + Code commune

### Présidentielles
- **2022 (T1 & T2)** : https://www.data.gouv.fr/fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour/
- **2017 (T1 & T2)** : https://www.data.gouv.fr/fr/datasets/election-presidentielle-des-23-avril-et-7-mai-2017-resultats-definitifs-du-1er-tour/

### Législatives
- **2024** : https://www.data.gouv.fr/fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/
- **2022** : https://www.data.gouv.fr/fr/datasets/elections-legislatives-des-12-et-19-juin-2022-resultats-definitifs-du-1er-tour/
- **2017** : https://www.data.gouv.fr/fr/datasets/elections-legislatives-des-11-et-18-juin-2017-resultats-du-1er-tour/

### Européennes
- **2024** : https://www.data.gouv.fr/fr/datasets/elections-europeennes-du-9-juin-2024-resultats-definitifs/
- **2019** : https://www.data.gouv.fr/fr/datasets/elections-europeennes-du-26-mai-2019-resultats-definitifs/

---

## Données Économiques

### Revenus par commune (PRIORITAIRE)
- **Lien** : https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune
- **Fichier** : revenu-des-francais-a-la-commune-*.csv (4.8 MB)
- **Contenu** : Revenus médians, quartiles, déciles
- **Clé** : Code INSEE commune

### CSP des actifs 25-54 ans (1968-2022) (PRIORITAIRE)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : pop-act2554-csp-cd-6822.xlsx (28.5 MB)
- **Contenu** : Population active par CSP (Agriculteurs, Artisans, Cadres, Prof. intermédiaires, Employés, Ouvriers) × statut
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022
- **Clé** : Code INSEE commune

### Comptes individuels des communes (2000-2022)
- **Lien** : https://data.economie.gouv.fr/explore/?q=comptes+individuels+des+communes
- **Fichiers** :
  - comptes_communes_2000_2008.csv (344 MB)
  - comptes_communes_2011_2015.csv (214 MB)
  - comptes_communes_2017.csv (44 MB)
  - comptes_communes_2022.csv (50 MB)
- **Contenu** : Recettes, dépenses, personnel, dette, DGF, fiscalité locale
- **Clé** : dep + icom (reconstituer code INSEE 5 chiffres)

### Secteur d'activité des actifs (1968-2022)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : pop-act2554-empl-sa-sexe-cd-6822.xlsx (23.5 MB)
- **Contenu** : Actifs par secteur (Agriculture, Industrie, Construction, Tertiaire) × sexe
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022

---

## Données Éducation

### Diplômes et Formation 2022 (PRIORITAIRE)
- **Lien** : https://www.insee.fr/fr/statistiques/8581488
- **Fichiers** :
  - base-cc-diplomes-formation-2022.CSV (81 MB)
  - base-cc-diplomes-formation-2022-COM.CSV
- **Contenu** : Diplômes et formation par commune
- **Clé** : CODGEO (code INSEE commune)

### CSP × Diplôme des actifs (1968-2022)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : pop-act2554-csp-dipl-cd-6822.xlsx (51.9 MB)
- **Contenu** : Croisement CSP × niveau diplôme (6 CSP × 6 niveaux)

---

## Données Démographiques

### Population historique (1876-2023) (RECOMMANDÉ)
- **Lien** : https://www.data.gouv.fr/datasets/bases-de-donnees-et-fichiers-details-du-recensement-de-la-population
- **Fichier** : base-pop-historiques-1876-2023.xlsx (6.7 MB)
- **Contenu** : Population municipale de 1876 à 2023 (39 recensements)
- **Clé** : CODGEO (code INSEE commune)

### Naissances par commune (2008-2024)
- **Lien** : https://www.insee.fr/fr/statistiques/1893255
- **Fichiers** :
  - DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv (24.4 MB)
  - DS_ETAT_CIVIL_NAIS_COMMUNES_metadata.csv (1.8 MB)
- **Clé** : GEO (code INSEE commune)

### Décès par commune (2008-2024)
- **Lien** : https://www.insee.fr/fr/statistiques/1893253
- **Fichiers** :
  - DS_ETAT_CIVIL_DECES_COMMUNES_data.csv (24.4 MB)
  - DS_ETAT_CIVIL_DECES_COMMUNES_metadata.csv (1.8 MB)

---

## Données Environnement

### Catastrophes naturelles - GASPAR (1985-2022+)
- **Lien** : https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/
- **Fichier** : catnat_gaspar.csv (34.5 MB)
- **Contenu** : Arrêtés catastrophe naturelle (inondations, sécheresse, tempêtes...)
- **Clé** : cod_commune (code INSEE commune)

### Risques connus par commune - GASPAR
- **Lien** : https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/
- **Fichier** : risq_gaspar.csv (8.4 MB)
- **Contenu** : Inventaire des risques (inondation, séisme, mouvement de terrain...)

---

## Sécurité & Criminalité

- **Base communale crimes/délits** (depuis 2016) : https://www.data.gouv.fr/fr/datasets/bases-communale-et-departementale-des-principaux-indicateurs-des-crimes-et-delits-enregistres-par-la-police-et-la-gendarmerie-nationales/

---

## Emploi

- **Taux de chômage communal** : https://www.data.gouv.fr/fr/datasets/taux-de-chomage-localise-par-zone-demploi/
- **Demandeurs d'emploi par commune** : https://www.data.gouv.fr/fr/datasets/demandeurs-demploi-inscrits-a-pole-emploi/

---

## Démographie & Économie (INSEE)

### Démographie
- **Population communale** : https://www.insee.fr/fr/statistiques/fichier/6683035/ensemble.zip
- **Densité population** : Calculable à partir population + superficie

### Revenus
- **Revenus médians par commune** : https://www.insee.fr/fr/statistiques/7233950
- **Taux de pauvreté** : https://www.insee.fr/fr/statistiques/7233950

### Économie
- **Base SIRENE (entreprises)** : https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
- **Nombre d'entreprises par commune** : Aggrégation SIRENE

---

## Référentiels géographiques

- **Code officiel géographique (COG)** : https://www.insee.fr/fr/information/6800675
- **Contours communes** (optionnel pour carto) : https://www.data.gouv.fr/fr/datasets/contours-des-communes-de-france-simplifie-avec-regions-et-departements-doutre-mer-rapproches/

---

## Notes

### Périmètre : Petite Couronne
Filtrer les données pour :
- **75** : Paris
- **92** : Hauts-de-Seine
- **93** : Seine-Saint-Denis
- **94** : Val-de-Marne

### Format privilégié
- CSV pour download
- Parquet pour stockage optimisé (pandas, compression)

### Période temporelle
- Données électorales : 2017-2024
- Données socio-économiques : La plus récente disponible (2021-2023)

---

## DATASETS PRIORITAIRES pour le Modèle ML

### Essentiels (Télécharger en priorité)
1. **Élections agrégées 1999-2024 (2.1 GB)** - Variable cible + historique complet
2. **Revenus par commune (4.8 MB)** - Fort indicateur sociologique  
3. **CSP des actifs (28.5 MB)** - Corrélation élevée avec orientation politique
4. **Diplômes et formation 2022 (81 MB)** - Fort pouvoir prédictif
5. **Population historique 1876-2023 (6.7 MB)** - Évolution démographique

### Importants (Ajouter ensuite)
6. **Comptes communaux 2022 (50 MB)** - Richesse locale, dette, DGF
7. **Crimes et délits communaux** - Indicateur sécurité/insécurité
8. **Catastrophes naturelles GASPAR (34.5 MB)** - Contexte local

### Optionnels (Si temps disponible)
9. Naissances/Décès (48.8 MB) - Dynamisme démographique
10. Secteur d'activité (23.5 MB) - Contexte économique local
11. Risques GASPAR (8.4 MB) - Sensibilité environnementale

---

## Ordre de téléchargement recommandé

### Phase 1 - Modèle de base (Sprint 1)
```
1. Élections agrégées (2.1 GB) CRITIQUE
2. Revenus commune (4.8 MB)
3. Référentiel communes INSEE
4. Population historique (6.7 MB)
```
**Total** : ~2.1 GB | **Permet** : Modèle prédictif de base

### Phase 2 - Enrichissement (Sprint 2)
```
5. Diplômes 2022 (81 MB)
6. CSP actifs (28.5 MB)
7. Crimes/délits communaux
8. Comptes communaux 2022 (50 MB)
```
**Total** : ~2.3 GB | **Permet** : Modèle enrichi socio-économique

### Phase 3 - Optimisation (Sprint 3)
```
9. Catastrophes naturelles (34.5 MB)
10. Secteur d'activité (23.5 MB)
11. Naissances/Décès (48.8 MB)
```
**Total** : ~2.4 GB | **Permet** : Modèle complet avec contexte local

---

## Volumétrie totale estimée

- **Minimum viable** : ~2.1 GB (Phase 1)
- **Recommandé** : ~2.3 GB (Phases 1+2)
- **Complet** : ~2.4 GB (Toutes phases)

---

## Clés de jointure

Toutes les données se croisent sur **Code INSEE commune** (5 chiffres) :
- Format : `CODGEO`, `GEO`, `cod_commune`, ou `dep + icom`
- Exemples Petite Couronne : `75056` (Paris), `92050` (Nanterre), `93008` (Bobigny), `94028` (Créteil)
