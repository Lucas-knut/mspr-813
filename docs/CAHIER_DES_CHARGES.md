# CAHIER DES CHARGES - MSPR Big Data et Analyse de Données

**Certification Professionnelle**: Expert en Informatique et Système d'Information RNCP35584  
**Bloc 3**: Piloter l'informatique décisionnel d'un S.I (Big Data & Business Intelligence)

---

## COMPÉTENCES ÉVALUÉES

1. Collecter les besoins en données des directions métiers de l'entreprise afin d'avoir une vision structurée de l'ensemble des données du système d'information et partager la stratégie Data globale avec le comité de direction.

2. Définir une architecture business intelligence à partir des orientations stratégiques arrêtées avec le comité de direction afin de mettre à disposition des utilisateurs métiers les données structurées d'un S.I.

3. Définir une stratégie big data (de la collecte aux traitements des données) à partir des orientations stratégiques arrêtées avec le comité de direction afin d'aider l'entreprise à mieux comprendre ses clients et à créer de nouveaux services.

4. Proposer des modèles statistiques et de data science (machine learning) à mettre en pratique aux directions métiers afin de détecter des nouveaux services, anticiper des besoins et résoudre des problématiques métiers de l'entreprise.

5. Organiser les sources de données sous forme de résultats exploitables (data visualisation) pour alimenter les outils décisionnels et visualiser les résultats de façon compréhensible permettant d'aider les directions métiers à la prise de décision.

6. Définir les données de référence de l'entreprise à partir des données utilisées pour créer un référentiel de données afin d'assurer la mise à disposition de données cohérentes aux directions métiers.

7. Créer un entrepôt unique à partir du référentiel de données établi pour centraliser les informations stratégiques de l'entreprise et répondre rapidement aux besoins métiers.

8. Assurer la qualité des données en utilisant les outils de gestion de la qualité de données pour garantir l'exactitude, la cohérence, la synchronisation et la traçabilité des données afin de satisfaire les besoins d'accessibilité des utilisateurs métiers.

9. Appliquer les procédures de sécurité établies par le/la RSSI de l'entreprise afin d'assurer la confidentialité et la sécurité des données et garantir une mise en conformité avec les obligations légales du RGPD.

---

## MODALITÉS D'ÉVALUATION

### Phase 1 : Préparation
- **Durée de préparation**: 25 heures
- **Organisation**: Travail d'équipe (4 apprenants-candidats, 5 maximum si groupe impair)
- **Objectif**: Mettre en avant et démontrer que les compétences visées par ce bloc sont bien acquises
- **Moyen**: Support de présentation

### Phase 2 : Présentation orale collective + entretien collectif
- **Durée totale**: 50 minutes par groupe
  - 20 minutes de soutenance orale par l'équipe
  - 30 minutes d'entretien collectif avec le jury (questionnement complémentaire)
- **Jury d'évaluation**: 2 personnes (binôme d'évaluateurs) par jury
  - Les évaluateurs n'ont pas participé à la formation
  - Les évaluateurs ne connaissent pas les apprenants

### Critères d'évaluation
L'évaluation repose sur la combinaison de trois éléments :
1. La qualité du travail réalisé au cours du projet
2. La pertinence et l'exhaustivité des livrables remis
3. La capacité de l'équipe à présenter, justifier et valoriser ce travail lors de la soutenance orale

---

## I - PRÉSENTATION DE L'ENTREPRISE

**Préambule**: L'entreprise choisie pour cette MSPR est fictive, les prénoms sont fictifs, toute ressemblance à un cas réel serait purement fortuite.

### Electio-Analytics

**Création**: Start-up créée en 2017 par Jean-Édouard de la Motte-Rouge

**Activité**: Conseil stratégique dédié aux campagnes électorales

**Clients**: Candidats, partis politiques et cabinets de conseil

**Ambition**: Apporter des analyses prospectives précises grâce à l'exploitation de données publiques et privées

### Équipe
- **Expert en analyse politique**: Doctorat en science politique, expérience terrain sur plusieurs scrutins nationaux
- **Business developer**: Master en marketing digital, réseau de contacts auprès de partis et d'organismes de financement (prospection, élaboration d'offres, recherche de subventions)
- **Assistante**: Formation en gestion administrative (coordination du projet et suivi administratif)

### Besoin stratégique
Mettre en place une capacité de prévision des tendances électorales à moyen terme (1 à 3 ans) en se basant sur des indicateurs :
- Sécurité
- Emploi
- Vie associative
- Population
- Vie économique (nombre d'entreprises)
- Pauvreté
- Autres critères pertinents (à ajouter si nécessaire)

**Objectif**: Obtenir un avantage concurrentiel important dans son activité

---

## II - CAHIER DES CHARGES

### Contexte
Avant d'engager des investissements lourds, la société veut valider cette approche par une **preuve de concept (POC)**. Elle fait appel à une société de service pour établir ce POC.

### 1. Périmètre géographique
- **Contrainte**: Secteur géographique restreint et unique (ville, arrondissement, circonscription, département)
- **Objectif**: Limiter la volumétrie des données et assurer la traçabilité des résultats

### 2. Collecte des données
Collecter les jeux de données publics disponibles :
- Résultats électoraux historiques
- Indicateurs de sécurité
- Indicateurs d'emploi
- Données démographiques
- Activité économique
- Indicateurs de pauvreté

**Enrichissement possible** : Enquêtes d'opinion, flux de réseaux sociaux, dépenses publiques locales

### 3. Pipeline ETL
- Nettoyage et normalisation des données
- Stockage dans une base structurée
- Pipeline ETL automatisé (Extraction, Transformation, Chargement)
- Schéma de base de données clairement nommé

### 4. Analyse exploratoire
- Visualisations descriptives : cartes, histogrammes, heat-maps
- Identification des corrélations potentielles entre chaque indicateur et les résultats électoraux passés

### 5. Modèle prédictif
- **Approche**: Modèle prédictif supervisé
- **Méthodologie**: Découpage en jeux d'entraînement et jeux de tests
- **Objectif**: Vérifier la fiabilité du modèle

### 6. Prédictions
Présentation sous forme de graphiques illustrant les scénarios à 1, 2 et 3 ans :
- Courbes temporelles
- Cartes de chaleur
- Diagrammes de probabilité

### 7. Documentation
Consigner toute la démarche, les résultats et les recommandations dans un rapport complet.

---

## III - BESOINS EXPRIMÉS PAR ELECTIO-ANALYTICS

### Justifications attendues
- Choix géographique basé sur la disponibilité des données, la représentativité et la taille exploitable
- Indicateurs pertinents démontrant une forte corrélation avec les résultats électoraux

### Pipeline de traitement
- Automatisé, fiable et traçable
- Garantie de la qualité des données
- Reproductibilité du processus

### Visualisations
- Claires et accessibles à des non-techniciens
- Permettant une prise de décision stratégique rapide

### Documentation
Documentation exhaustive requise :
- Rapport
- Schéma conceptuel de données
- Code commenté
- Jeu de données nettoyé

### Formats compatibles
SQL, CSV, notebooks Jupyter, PowerBI

### Conseils méthodologiques

1. Proposer un schéma de traitement des données (flux de données)
2. Utiliser un outil de normalisation des données (ETL)
3. Définir une architecture de données adaptée aux traitements
4. Nommer spécifiquement et de manière pertinente les tables et champs
5. Ouvrir les données avec un langage adapté (Python - Pandas, R)
6. Créer un modèle prédictif à partir des données passées (apprentissage supervisé)
7. Proposer des visualisations claires (PowerBI ou librairies Python comme Matplotlib)

### Questions d'analyse à traiter

1. Parmi les données sélectionnées, laquelle est la plus corrélée aux résultats des élections ?
2. Définir le principe d'un apprentissage supervisé
3. Comment définir le degré de précision (accuracy) du modèle ?

---

## IV - LIVRABLES

Les livrables doivent être produits selon une logique industrielle : entièrement documentés, reproductibles et immédiatement exploitables.

### 1. Dossier de synthèse

Répondant aux attentes suivantes :
- Justification du choix de la zone géographique
- Choix des critères et justification
- Démarche suivie et méthodes employées
- Modèle Conceptuel de Données (MCD)
- Modèles testés
- Résultats du modèle choisi
- Visualisations
- Accuracy (pouvoir prédictif du modèle)
- Réponses aux questions d'analyse (+ indicateurs additionnels pertinents)

### 2. Jeu de données nettoyé, normalisé et optimisé

Format libre : SQL ou NoSQL

### 3. Code propre et commenté

### 4. Support de soutenance

Support de présentation destiné à la soutenance finale devant le client (public technique), synthétisant les principaux éléments du travail réalisé.

---

## V - RESSOURCES FOURNIES

### Jeux de données disponibles (liste non exhaustive)

- **Élections**: https://www.data.gouv.fr/fr/pages/donnees-des-elections/
- **Sécurité**: https://www.data.gouv.fr/fr/pages/donnees-securite/
- **Emploi**: https://www.data.gouv.fr/datasets/search?q=emploi
- **INSEE**: https://www.data.gouv.fr/fr/organizations/institut-national-de-la-statistique-et-des-etudes-economiques-insee/?datasets_page=7#organization-datasets

### Assistance et périmètre

Dans le cadre de ce projet pédagogique :
- Aucun contact direct avec Electio-Analytics
- Le cahier des charges constitue la seule expression officielle du besoin
- Toute demande de clarification doit être traitée avec l'encadrant pédagogique (jouant le rôle du client)
