# PLAN D'EXÉCUTION - MSPR-813 ML Electoral

**Projet** : Modèle ML supervisé pour prédiction des tendances électorales  
**Stack** : Python 3.11, pandas 2.1.4, scikit-learn, Jupyter Lab, Docker  
**Format données** : Parquet (traité), CSV/Excel (brut)  
**Principe** : Code minimaliste, scalable, commenté en français

---

## ÉTAT ACTUEL DU PROJET

### Infrastructure
- Docker + Jupyter Lab : configuré et fonctionnel
- Structure dossiers : créée (data/raw/, data/processed/, data/output/, outputs/figures/)
- Environnement Python 3.11 : validé avec toutes les dépendances
- Mémoire disponible : 7 GB (suffisant pour datasets < 10 GB)

### Données Téléchargées (Phase 1 - Petite Couronne)
- Elections agrégées 1999-2024 : 2.2 GB (27.3M lignes)
- Revenus par commune : 4.8 MB (34.9K lignes)
- Population historique 1968-2022 : 43.6 MB (Excel)
- Diplômes formation 2022 : 66 MB (Excel)
- CSP actifs 25-54 ans : 28.5 MB (Excel)
- Référentiel communes INSEE : 2.5 MB (37.5K communes)
- Total : ~2.3 GB

### Notebooks Existants
- 00_setup.ipynb : validation environnement (100% fonctionnel)
- 01_data_download.ipynb : téléchargement datasets (80% - Phase 1 complète)
- 02_exploration.ipynb : exploration données (30% - problèmes de parsing à corriger)

### Notebooks à Créer
- 03_etl.ipynb : pipeline ETL (nettoyage, transformation)
- 04_features.ipynb : feature engineering
- 05_modeling.ipynb : modélisation ML supervisée

---

## PROBLÈMES IDENTIFIÉS À RÉSOUDRE

### Bloquants Critiques

1. Fichiers CSV mal parsés
   - elections_agregees_1999_2024.csv : séparateur ; non détecté → 1 colonne au lieu de 18
   - revenus_commune.csv : même problème
   - Solution : ajouter sep=';' dans pd.read_csv()

2. Fichiers Excel avec métadonnées INSEE
   - Population, Diplômes, CSP : en-têtes sur plusieurs lignes
   - pop-16ans-dipl6822.xlsx retourne DataFrame vide
   - Solution : utiliser skiprows= et header= dans pd.read_excel()

3. Périmètre géographique à valider
   - Incohérence : 144 communes (notebook) vs 124 attendues (Petite Couronne)
   - Solution : vérifier filtre sur codes départements 75, 92, 93, 94

### Secondaires

4. Données Phase 2 manquantes (Extension France)
   - Comptes communaux 2022 : téléchargement manuel requis
   - GASPAR catastrophes naturelles : URLs invalides (404)
   - Naissances/Décès : non téléchargés (optionnel)

5. Dataset CSP non exploré
   - Fichier présent mais pas encore analysé

---

## PLAN D'EXÉCUTION PAR PHASE

### PHASE 1 : DÉBLOCAGE TECHNIQUE (1 jour)
Priorité : CRITIQUE  
Notebook : 02_exploration.ipynb

#### Tâches
1. Corriger parsing CSV
   - Elections : pd.read_csv(..., sep=';', dtype={'code_commune': str, 'code_departement': str})
   - Revenus : pd.read_csv(..., sep=';')
   - Valider nombre de colonnes attendues (18 pour élections)

2. Corriger chargement Excel INSEE
   - Population : identifier bon skiprows et header pour pop-16ans-dipl6822.xlsx
   - Diplômes : idem pour base-cc-diplomes-formation-2022.xlsx
   - CSP : idem pour pop-act2554-csp-cd-6822.xlsx
   - Tester différentes combinaisons jusqu'à obtenir structure correcte

3. Valider périmètre géographique
   - Lister codes INSEE Petite Couronne (75, 92, 93, 94) depuis référentiel
   - Confirmer nombre exact de communes (124 ou 144)
   - Créer liste de référence validée

#### Livrables
- 02_exploration.ipynb : section "1. Chargement corrigé des datasets"
- Tous les datasets chargés correctement avec bon nombre de colonnes
- Liste codes_insee_petite_couronne validée

---

### PHASE 2 : EXPLORATION APPROFONDIE (2 jours)
Priorité : HAUTE  
Notebook : 02_exploration.ipynb

#### Tâches
1. Exploration structure datasets
   - Dimensions (lignes, colonnes)
   - Types de données
   - Mémoire utilisée
   - Échantillon données (head, tail)
   - Statistiques descriptives (describe)

2. Filtrage Petite Couronne
   - Elections : filtrer 27.3M lignes → subset Petite Couronne
   - Revenus, Population, Diplômes, CSP : filtrer sur codes INSEE validés
   - Estimer réduction volumétrie (millions → milliers de lignes)

3. Analyse qualité données
   - Valeurs manquantes par colonne (pourcentage)
   - Doublons (identifier et quantifier)
   - Valeurs aberrantes (outliers via boxplots, IQR)
   - Cohérence temporelle (vérifier années disponibles)
   - Validation clés de jointure (code INSEE présent dans tous datasets)

4. Analyse exploratoire visuelle
   - Distribution revenus par commune (histogramme, boxplot)
   - Évolution population 1968-2022 (courbe temporelle)
   - Répartition CSP (barplot empilé)
   - Répartition diplômes (camembert ou barplot)
   - Résultats électoraux historiques (courbes tendances)
   - Cartes géographiques si coordonnées disponibles

5. Définition variable cible "Tendance Politique"
   - Analyser résultats électoraux par nuance politique
   - Créer 3 catégories : Gauche / Centre / Droite
   - Calculer indice de tendance : (score_gauche - score_droite) / total_votes
   - Valider distribution de la variable cible

6. Analyse corrélations
   - Matrice de corrélation : indicateurs socio-économiques ↔ tendance politique
   - Heatmap de corrélations (seaborn)
   - Identifier top 5 variables les plus corrélées
   - RÉPONDRE À QUESTION 1 : "Quelle donnée est la plus corrélée aux résultats électoraux ?"

#### Livrables
- 02_exploration.ipynb : sections complètes d'exploration
- Graphiques sauvegardés dans outputs/figures/01_eda/
- Documentation insights dans markdown du notebook
- Réponse Question 1 documentée

---

### PHASE 3 : PIPELINE ETL (2-3 jours)
Priorité : HAUTE  
Notebook : 03_etl.ipynb

#### Tâches
1. Chargement données brutes
2. Nettoyage données électorales
3. Nettoyage données socio-économiques
4. Création variable cible finale
5. Jointures datasets
6. Validation pipeline
7. Sauvegarde Parquet

#### Livrables
- 03_etl.ipynb : pipeline ETL complet et commenté
- Datasets Parquet nettoyés dans data/processed/
- Schéma ETL documenté
- Logs de validation

---

### PHASE 4 : FEATURE ENGINEERING (2 jours)
Priorité : HAUTE  
Notebook : 04_features.ipynb

#### Tâches
1. Chargement dataset master
2. Features démographiques
3. Features revenus et pauvreté
4. Features éducation
5. Features CSP
6. Features électorales historiques
7. Features contextuelles
8. Gestion valeurs manquantes
9. Normalisation et encodage
10. Sélection features
11. Validation dataset final
12. Sauvegarde

#### Livrables
- 04_features.ipynb : feature engineering complet
- Dataset features dans data/processed/features_selected.parquet
- Liste des features retenues avec descriptions
- Paramètres normalisation sauvegardés

---

### PHASE 5 : MODÉLISATION ML (2-3 jours)
Priorité : HAUTE  
Notebook : 05_modeling.ipynb

#### Tâches
1. Chargement dataset features
2. Préparation données ML
3. Train/Test Split
4. Documentation Apprentissage Supervisé (RÉPONDRE QUESTION 2)
5. Modèles à tester (Régression Linéaire, Random Forest, Gradient Boosting, Ridge)
6. Évaluation modèles (RÉPONDRE QUESTION 3)
7. Visualisations performances
8. Feature Importance
9. Validation croisée
10. Optimisation hyperparamètres
11. Sélection modèle final
12. Sauvegarde modèle

#### Livrables
- 05_modeling.ipynb : modélisation complète
- Modèle entraîné : data/output/model_best.pkl
- Métriques : data/output/model_metrics.json
- Feature importance : data/output/feature_importance.json
- Graphiques comparaison modèles
- Réponses Questions 2 & 3 dans le notebook

---

### PHASE 6 : PRÉDICTIONS ET VISUALISATIONS (2 jours)
Priorité : HAUTE  
Notebook : 06_predictions.ipynb

#### Tâches
1. Chargement modèle et données
2. Hypothèses évolution indicateurs
3. Génération features futures
4. Prédictions futures (2025, 2026, 2027)
5. Visualisations temporelles
6. Cartes géographiques
7. Diagrammes de probabilité
8. Graphiques comparatifs
9. Exports compatibles PowerBI
10. Exports visualisations
11. Interprétation résultats

#### Livrables
- 06_predictions.ipynb : prédictions futures et visualisations
- data/output/predictions_2025_2027.csv
- Graphiques dans outputs/figures/03_predictions/
- Cartes interactives HTML
- Interprétations et recommandations

---

### PHASE 7 : EXTENSION FRANCE ENTIÈRE (3-4 jours)
Priorité : MOYENNE  
Notebook : 07_extension_france.ipynb

#### Tâches
1. Téléchargement données Phase 2
2. Adaptation filtres géographiques
3. Optimisations scalabilité
4. Pipeline complet France entière
5. Comparaison POC vs France
6. Visualisations France entière
7. Insights régionaux
8. Documentation scalabilité

#### Livrables
- 07_extension_france.ipynb : pipeline France entière
- data/processed/master_dataset_france.parquet
- data/output/predictions_france_2027.csv
- Graphiques France entière
- Section "Scalabilité" dans documentation

---

### PHASE 8 : DOCUMENTATION ET LIVRABLES (2-3 jours)
Priorité : HAUTE  
Documents : Dossier synthèse, Support présentation, MCD

#### Tâches
1. Modèle Conceptuel de Données (MCD)
2. Dossier de synthèse (15-20 pages)
3. Support de présentation (15-20 slides)
4. Finalisation code
5. Reproductibilité

#### Livrables
- docs/MCD.png
- docs/DOSSIER_SYNTHESE.pdf
- docs/SUPPORT_PRESENTATION.pptx
- Tous les notebooks nettoyés et commentés
- README.md à jour
- Pipeline reproductible validé

---

## CALENDRIER RÉCAPITULATIF

| Phase | Durée | Priorité | Notebooks | Livrables Clés |
|-------|-------|----------|-----------|----------------|
| 1. Déblocage technique | 1 jour | CRITIQUE | 02 | Parsing corrigé |
| 2. Exploration | 2 jours | HAUTE | 02 | Corrélations, Réponse Q1 |
| 3. ETL | 2-3 jours | HAUTE | 03 | Dataset master Parquet |
| 4. Features | 2 jours | HAUTE | 04 | Features sélectionnées |
| 5. Modélisation | 2-3 jours | HAUTE | 05 | Modèle ML, Réponses Q2-Q3 |
| 6. Prédictions | 2 jours | HAUTE | 06 | Prédictions 2025-2027 |
| 7. Extension France | 3-4 jours | MOYENNE | 07 | Scalabilité démontrée |
| 8. Documentation | 2-3 jours | HAUTE | - | Dossier synthèse, Présentation |

Total estimé :
- POC Petite Couronne (Phases 1-6, 8) : 11-14 jours
- POC + Extension France (Phases 1-8) : 14-18 jours

---

## RÈGLES DE DÉVELOPPEMENT

### Code Minimaliste
- Ne pas en faire trop : rester sur le strict nécessaire
- Éviter over-engineering : pas de classes complexes si fonctions suffisent
- Privilégier clarté sur performance extrême (pandas suffit, pas Spark)

### Nommage
- Variables en snake_case : df_elections, revenu_median, code_insee
- Fonctions verbes : calculer_tendance(), filtrer_petite_couronne()
- Colonnes explicites : tendance_politique pas tp

### Commentaires
- En français
- Explicatifs, pas redondants
- Pas d'emojis dans le code ou docs

### Scalabilité
- Code extensible : variables PERIMETRE et CODES_DEPT faciles à modifier
- Fonctions réutilisables
- Chunking si fichiers > 1 GB
- Partitionnement Parquet : partition_cols=['departement']

### Traçabilité
- Assertions validation
- Logs informatifs
- Sauvegardes intermédiaires

### RGPD
- Données publiques uniquement
- Pas de données personnelles identifiantes
- Agrégations communales

---

## QUESTIONS TROIS COMPÉTENCES

### Question 1 : Quelle donnée est la plus corrélée aux résultats électoraux ?
Réponse à fournir dans Phase 2 après analyse de corrélations

### Question 2 : Définir le principe d'un apprentissage supervisé
Réponse à fournir dans Phase 5 (modélisation)

### Question 3 : Comment définir le degré de précision (accuracy) du modèle ?
Réponse à fournir dans Phase 5 (évaluation modèles)

---

Document créé le : 13 février 2026  
Dernière mise à jour : 13 février 2026  
Auteur : Projet MSPR TPRE813 - EPSI 2026
