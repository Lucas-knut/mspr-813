# MSPR Big Data - Prédiction Électorale

**Projet EPSI - BLOC 3 RNCP35584**  
Analyse prédictive des tendances électorales avec Apache Spark

## 📊 Objectif

Développer un modèle prédictif pour anticiper les résultats électoraux à 1-3 ans en utilisant des indicateurs socio-économiques (sécurité, emploi, démographie, pauvreté, économie locale).

## 🎯 Périmètre

**Zone géographique :** Petite Couronne parisienne (Paris 75, Hauts-de-Seine 92, Seine-Saint-Denis 93, Val-de-Marne 94)  
**Volume :** ~150 communes  
**Extensible :** Architecture scalable pour toute la France (~35,000 communes)

## 📁 Structure du Projet

```
mspr-813/
├── data/                              # 🗄️ Données (non versionnées Git)
│   ├── raw/                           # Données sources téléchargées
│   │   ├── elections_agregees_1999_2024.csv    # 2.2 GB - Variable cible
│   │   ├── revenus_commune.csv                 # 4.8 MB - Indicateur économique
│   │   ├── referentiel_communes.csv            # 3 MB - Clé de jointure
│   │   ├── population_historique_1968_2022/    # 40 MB - Dynamique démographique
│   │   ├── diplomes_formation_2022/            # 81 MB - Niveau éducation
│   │   ├── csp_actifs_2554/                    # 28.5 MB - Catégories socio-pro
│   │   └── ...autres datasets Phase 2...
│   │
│   ├── processed/                     # Données transformées (Parquet optimisé Spark)
│   │   ├── elections_clean.parquet            # Élections nettoyées + filtrées
│   │   ├── socio_eco_features.parquet         # Features engineerées
│   │   └── master_dataset.parquet             # Dataset final jointuré
│   │
│   └── output/                        # Résultats finaux
│       ├── predictions_2027.csv               # Prédictions générées
│       └── model_metrics.json                 # Métriques de performance
│
├── notebooks/                         # 📓 Notebooks Jupyter (développement interactif)
│   ├── 00_setup_spark.ipynb           # ✅ Validation environnement Spark
│   ├── 01_data_download.ipynb         # ⬇️ Téléchargement datasets (Phase 1 + Phase 2)
│   ├── 02_exploration.ipynb           # 🔍 EDA - Analyse exploratoire (À CRÉER)
│   ├── 03_etl_spark.ipynb             # 🔄 Pipeline ETL avec PySpark (À CRÉER)
│   ├── 04_feature_engineering.ipynb   # 🛠️ Création features prédictives (À CRÉER)
│   ├── 05_modeling.ipynb              # 🤖 Entraînement modèles ML (À CRÉER)
│   └── 06_evaluation.ipynb            # 📊 Évaluation et visualisations (À CRÉER)
│
├── outputs/                           # 📈 Exports pour soutenance
│   └── figures/                       # Graphiques et visualisations
│       ├── correlation_matrix.png
│       ├── feature_importance.png
│       └── predictions_map.html       # Carte interactive
│
├── docs/                              # 📚 Documentation projet
│   ├── ARCHITECTURE.md                # Architecture détaillée et choix techniques
│   ├── DATASETS.md                    # Liste exhaustive datasets avec métadonnées
│   ├── DOWNLOAD_PRIORITY.md           # Stratégie téléchargement par phases
│   └── URLS_DATASETS.md               # URLs de téléchargement corrigées
│
├── Dockerfile                         # 🐳 Image Docker Python + Spark + Java 21
├── docker-compose.yml                 # Orchestration conteneur Jupyter Lab
├── requirements.txt                   # Dépendances Python (PySpark, scikit-learn, viz)
└── README.md                          # Ce fichier
```

## 🏗️ Organisation et Architecture

### Principe de l'organisation

Le projet suit une **architecture en couches** typique d'un projet Big Data :

1. **Couche Données (`data/`)** : Séparation claire entre données brutes (immuables), transformées (optimisées), et résultats
2. **Couche Traitement (`notebooks/`)** : Pipeline séquentiel de notebooks pour traçabilité et reproductibilité
3. **Couche Présentation (`outputs/`)** : Exports prêts pour soutenance
4. **Couche Infrastructure** : Docker pour isolation et reproductibilité environnement

### Pourquoi cette structure ?

#### ✅ **Séparation raw/processed/output**
- **`raw/`** : Données sources **jamais modifiées** → reproductibilité garantie
- **`processed/`** : Format **Parquet** → 10x plus rapide que CSV avec Spark, compression efficace
- **`output/`** : Résultats finaux **isolés** pour faciliter export/partage

#### ✅ **Notebooks numérotés**
- **Ordre d'exécution clair** : 00 → 01 → 02 → ... 
- **Pipeline modulaire** : chaque étape = 1 notebook
- **Développement itératif** : retour en arrière facile
- **Documentation intégrée** : code + explications + résultats

#### ✅ **Format Parquet pour Big Data**
- **Columnar storage** : lecture optimisée pour analyses (vs CSV row-based)
- **Compression automatique** : 5-10x moins d'espace disque
- **Types de données préservés** : pas de parsing à chaque lecture
- **Partitionnement possible** : scalabilité 150 communes → 35K communes

### Approche Progressive : Phase 1 → Phase 2

Le projet est conçu pour **progression par étapes** :

| Phase | Périmètre | Datasets | Volume | Objectif |
|-------|-----------|----------|--------|----------|
| **Phase 1 - POC** | Petite Couronne (150 communes) | Socio-économiques essentiels | ~2.4 GB | Valider modèle de base |
| **Phase 2 - Extension** | France entière (35K communes) | + Territorial (finances, environnement) | +140 MB | Démontrer scalabilité |

**Phase 1** = Développement rapide avec variables de référence (revenus, CSP, diplômes)  
**Phase 2** = Extension testée pour soutenance ("architecture pensée Big Data")

📖 **Pour plus de détails** : voir [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🚀 Workflow de Développement

### Installation et Démarrage

```bash
# 1. Cloner le projet
git clone <repo-url>
cd mspr-813

# 2. Lancer l'environnement Docker
docker-compose up -d

# 3. Accéder à Jupyter Lab
# Ouvrir : http://localhost:8888
```

### Pipeline d'Exécution des Notebooks

Exécuter dans l'ordre :

```
00_setup_spark.ipynb        → Valider installation Spark ✅
01_data_download.ipynb      → Télécharger datasets Phase 1 (+ Phase 2 si besoin)
02_exploration.ipynb        → Explorer et comprendre les données
03_etl_spark.ipynb          → Nettoyer, transformer, joindre avec PySpark
04_feature_engineering.ipynb → Créer variables prédictives
05_modeling.ipynb           → Entraîner modèles ML
06_evaluation.ipynb         → Évaluer performance et visualiser
```

### Arrêt de l'Environnement

```bash
docker-compose down
```

## 🛠️ Stack Technique

- **Big Data :** Apache Spark (PySpark 3.5.0)
- **ML :** Scikit-learn + Spark MLlib
- **Visualisation :** Matplotlib, Seaborn, Plotly
- **Format :** Parquet (optimisé Big Data)
- **Orchestration :** Docker + Jupyter Lab
- **Langage :** Python 3.11
- **Runtime :** Java 21 (requis pour Spark)

## 📦 Datasets et Stratégie de Données

### Phase 1 - POC Petite Couronne (~2.4 GB)

| Dataset | Taille | Utilité | Justification scientifique |
|---------|--------|---------|----------------------------|
| **Élections agrégées 1999-2024** | 2.2 GB | Variable cible | Historique électoral complet toutes élections |
| **Revenus par commune** | 4.8 MB | Vote économique | Revenu médian = prédicteur fort (sociologie électorale) |
| **Population historique 1968-2022** | 40 MB | Dynamique urbaine | Croissance/déclin = indicateur dynamisme commune |
| **Diplômes et formation 2022** | 81 MB | Vote culturel | Niveau éducation = variable de référence (ouverture/fermeture) |
| **CSP actifs 25-54 ans** | 28.5 MB | Vote de classe | Ouvriers ≠ Cadres (vote professionnel) |

→ **Les 3 variables socio-économiques classiques** : Revenus + Diplômes + CSP

### Phase 2 - Extension France Entière (~140 MB)

| Dataset | Taille | Utilité pour France entière |
|---------|--------|-----------------------------|
| **Comptes communaux 2022** | 50 MB | Diversité finances locales (rural ≠ urbain) |
| **Catastrophes naturelles GASPAR** | 34.5 MB | Exposition risques environnementaux (littoral, montagne) |
| **Risques GASPAR** | variable | Perception des risques |
| **Naissances/Décès 2008-2024** | 48 MB | Vieillissement fin (communes retraités ≠ jeunes familles) |

→ **Capture la diversité territoriale** pour scalabilité 35K communes

### Référentiel Transversal

| Dataset | Taille | Utilité |
|---------|--------|---------|
| **COG - Référentiel communes** | 3 MB | Clé de jointure (codes INSEE, départements, régions) |

📋 **Documentation complète** :
- [DATASETS.md](docs/DATASETS.md) - Liste exhaustive avec métadonnées
- [DOWNLOAD_PRIORITY.md](docs/DOWNLOAD_PRIORITY.md) - Stratégie progressive par phases
- [URLS_DATASETS.md](docs/URLS_DATASETS.md) - URLs corrigées et stables

## 📚 Documentation Complète

- 📖 **[README.md](README.md)** (ce fichier) - Vue d'ensemble et démarrage rapide
- 🏗️ **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture détaillée, choix techniques et bonnes pratiques
- 📊 **[DATASETS.md](docs/DATASETS.md)** - Catalogue exhaustif des datasets avec métadonnées
- 🎯 **[DOWNLOAD_PRIORITY.md](docs/DOWNLOAD_PRIORITY.md)** - Stratégie de téléchargement par phases
- 🔗 **[URLS_DATASETS.md](docs/URLS_DATASETS.md)** - URLs de téléchargement corrigées et stables

## 👥 Équipe

Projet MSPR TPRE813 - EPSI 2026

---

**Dernière mise à jour** : 10 février 2026
