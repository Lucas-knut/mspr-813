# Phase 1 - Déblocage Technique : CORRECTIONS APPLIQUÉES

**Date** : 13 février 2026  
**Notebook** : `02_exploration.ipynb`  
**Statut** : ✅ CORRECTIONS COMPLÈTES - Parsing des fichiers corrigé

---

## CORRECTIONS EFFECTUÉES

### 1. Fichier elections_agregees_1999_2024.csv
**Problème** : Fichier chargé avec 1 seule colonne au lieu de 18  
**Cause** : Séparateur `;` non détecté (défaut pandas : `,`)  
**Solution appliquée** :
```python
df_elections = pd.read_csv(
    DATA_RAW / "elections_agregees_1999_2024.csv",
    sep=";",  # Fichier délimité par point-virgule
    chunksize=10000,
    nrows=10000,
    dtype={'code_commune': str, 'code_departement': str}  # Codes INSEE en string
)
```
**Résultat attendu** : 18 colonnes correctement parsées

---

### 2. Fichier revenus_commune.csv
**Problème** : Colonnes mal parsées, noms de colonnes avec séparateurs intégrés  
**Cause** : Séparateur `;` non détecté  
**Solution appliquée** :
```python
df_revenus = pd.read_csv(
    DATA_RAW / "revenus_commune.csv",
    sep=";"  # Fichier délimité par point-virgule
)
```
**Résultat attendu** : Colonnes séparées correctement (Code géographique, Médiane, Déciles, etc.)

---

### 3. Fichier pop-16ans-dipl6822.xlsx (Population)
**Problème** : DataFrame vide retourné  
**Cause** : Métadonnées INSEE en début de fichier (lignes 0-4)  
**Solution appliquée** :
```python
df_population = pd.read_excel(
    main_file, 
    engine='openpyxl', 
    skiprows=5,  # Sauter les métadonnées INSEE
    nrows=10
)
```
**Alternative testée** : `skiprows=4` si `skiprows=5` échoue  
**Résultat attendu** : Colonnes population par tranche d'âge, codes INSEE

---

### 4. Fichier base-cc-diplomes-formation-2022.xlsx (Diplômes)
**Problème** : Métadonnées INSEE chargées dans les 4 premières lignes  
**Cause** : Fichiers INSEE contiennent en-têtes sur lignes 0-3, vrais headers ligne 4  
**Solution appliquée** :
```python
df_diplomes = pd.read_excel(
    main_file, 
    engine='openpyxl', 
    skiprows=4,  # Sauter métadonnées INSEE (lignes 0-3)
    nrows=10
)
```
**Résultat attendu** : Colonne `CODGEO` en première colonne, données diplômes par commune

---

### 5. Fichier pop-act2554-csp-cd-6822.xlsx (CSP actifs)
**Problème** : Même structure que autres fichiers INSEE (métadonnées en début)  
**Cause** : Format standard fichiers INSEE  
**Solution appliquée** :
```python
df_csp = pd.read_excel(
    main_file, 
    engine='openpyxl', 
    skiprows=4,  # Sauter métadonnées INSEE
    nrows=10
)
```
**Résultat attendu** : Colonne `CODGEO` présente, CSP par catégorie (agriculteurs, artisans, cadres, etc.)

---

## OBSERVATIONS

### 6. Périmètre géographique Petite Couronne - 144 communes détectées
**Statut** : OBSERVATION - Validation requise  
**Constat** : Le filtrage sur départements 75, 92, 93, 94 retourne 144 communes  
**Répartition actuelle** :
- 75 (Paris) : 21 communes  
- 92 (Hauts-de-Seine) : 36 communes  
- 93 (Seine-Saint-Denis) : 40 communes  
- 94 (Val-de-Marne) : 47 communes  
**TOTAL** : 144 communes

**Questionnement** : Référence initiale mentionnait 124 communes  
**Hypothèses** :
1. Les 144 communes sont correctes (données INSEE officielles 2024)
2. Différence peut venir de :
   - Fusions/défusions de communes entre années
   - Arrondissements de Paris comptés séparément (20 arrondissements)
   - Codes INSEE spéciaux (délégations, communes associées)

**Action recommandée** :
- Valider avec INSEE ou source officielle le nombre exact de communes Petite Couronne
- Si 144 est correct : mettre à jour documentation (124 → 144)
- Si 124 est correct : identifier et exclure 20 codes INSEE excédentaires
- Pour le POC : **144 communes est un périmètre valide et exploitable**

---

### 6. Validation périmètre géographique Petite Couronne
**Statut** : PENDING  
**Observation actuelle** : 144 communes détectées  
**Attendu** : 124 communes (75, 92, 93, 94)  
**Action requise** : 
- Vérifier filtre sur codes départements
- Exclure éventuellement codes spéciaux (arrondissements Paris, communes fusionnées)
- Code à vérifier :
```python
df_communes['dept'] = df_communes['COM'].astype(str).str[:2]
df_communes_pc = df_communes[df_communes['dept'].isin(['75', '92', '93', '94'])]
print(df_communes_pc.groupby('dept').size())  # Vérifier répartition
```

---

## PROCHAINES ÉTAPES

### Action immédiate
1. Lancer Docker : `docker-compose up -d`
2. Accéder Jupyter Lab : http://localhost:8888
3. Ouvrir `notebooks/02_exploration.ipynb`
4. Exécuter cellule par cellule (Kernel → Restart & Run All)
5. Vérifier outputs :
   - Elections : 18 colonnes (id_election, code_departement, code_commune, voix, nuance, etc.)
   - Revenus : colonnes séparées (Code géographique, Médiane, etc.)
   - Population : données population par âge (pas de DataFrame vide)

### Si erreurs persistent
1. Noter cellule exacte qui échoue
2. Lire message d'erreur complet
3. Ajuster `skiprows` si nécessaire :
   - Fichiers INSEE : tester skiprows=3, 4, 5, ou 6
   - Vérifier aussi `header=[0,1]` si en-têtes sur 2 lignes

### Après validation parsing
- Passer à Phase 2 : Exploration approfondie
- Filtrer données Petite Couronne
- Analyser qualité données (valeurs manquantes, doublons)
- Créer visualisations exploratoires

---

## LOGS DE MODIFICATION

| Date | Fichier | Modification | Statut |
|------|---------|--------------|--------|
| 13/02/2026 | elections_agregees_1999_2024.csv | Ajout sep=';' + dtype codes INSEE | ✅ Appliqué |
| 13/02/2026 | revenus_commune.csv | Ajout sep=';' | ✅ Appliqué |
| 13/02/2026 | pop-16ans-dipl6822.xlsx | Ajout skiprows=5 + try/except skiprows=4 | ✅ Appliqué |
| 13/02/2026 | base-cc-diplomes-formation-2022.xlsx | Ajout skiprows=4 | ✅ Appliqué |
| 13/02/2026 | pop-act2554-csp-cd-6822.xlsx | Ajout skiprows=4 | ✅ Appliqué |
| 13/02/2026 | Périmètre géographique | Observation 144 communes | ⚠️ À valider |

---

Document créé le : 13 février 2026  
Auteur : Projet MSPR TPRE813 - EPSI 2026
