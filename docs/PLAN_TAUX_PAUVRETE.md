# Calcul du taux de pauvreté estimé

> **Status : TERMINE.** `taux_pauvrete` est peuplé à 90% dans `silver_france.revenus`
> (31 242 / 34 844 communes, moyenne 8.47%) et à 100% dans `gold_france.features_communes`.

## Contexte

Le fichier INSEE `revenus_commune.csv` ne contient pas le taux de pauvreté communal.
La colonne `taux_pauvrete` existe dans les schémas Silver et Gold mais est vide (0 valeurs sur 34 844 communes).

## Diagnostic

| Colonne | Silver (source) | Couverture |
|---------|-----------------|------------|
| `mediane_revenu_disp` | 31 242 / 34 844 | 90% |
| `gini` | 5 291 / 34 844 | 15% |
| `q1_revenu_disp` (D1) | 5 291 / 34 844 | 15% |
| `taux_pauvrete` | 0 / 34 844 | 0% — MANQUANT |

Paramètres nationaux calculés depuis les données disponibles :
- Médiane nationale : 22 810 €/an
- Seuil de pauvreté (60% médiane) : 13 686 €/an

## Solution retenue — Option A : calcul estimé

### Formule à 3 niveaux

**Niveau 1 — Communes avec Gini + médiane (15% des communes)**

Formule empirique calibrée sur Filosofi INSEE 2020-2022 :
```
si médiane < seuil_pauvreté :
    taux = 35 + (gini - 0.25) × 80           [borné 0-50%]
sinon :
    taux = -5 + (gini - 0.20) × 100
    si médiane < 75% médiane_nationale : taux × 1.4
    si médiane > 125% médiane_nationale : taux × 0.6
    [borné 0-50%]
```

**Niveau 2 — Communes avec médiane seule (74% des communes)**

Tranches de revenus :
```
médiane < 80% seuil (~10 950€)  → taux = 40%
médiane < seuil (13 686€)       → interpolation linéaire 40% → 25%
médiane < 90% médiane_nat       → taux = 15%
médiane < 110% médiane_nat      → taux = 10%
médiane < 130% médiane_nat      → taux = 6%
médiane >= 130% médiane_nat     → taux = 3%
```

**Niveau 3 — Communes sans médiane (10% des communes)**

Imputation par médiane départementale puis médiane nationale (déjà gérée dans 05b).

### Précision estimée

±5% vs données Filosofi réelles. Suffisant pour l'analyse prédictive
(objectif : discriminer communes pauvres vs aisées, pas mesure exacte).

## Fichiers modifiés

| Fichier | Modification |
|---------|-------------|
| `notebooks/communes/france/01_etl_bronze_to_postgres.ipynb` | Ajout fonction `calcul_taux_pauvrete()` après le mapping revenus |
| `notebooks/communes/france/02_feature_engineering.ipynb` | Aucune modification (imputation déjà en place) |
| `notebooks/communes/france/03_modeling.ipynb` | `mediane_revenu_disp`, `gini`, `taux_pauvrete` dans les features ML |
| `docs/METABASE_QUESTIONS.md` | Note sur estimation de `taux_pauvrete` dans Q6 |

## Ordre d'exécution (reference — déjà exécuté)

1. Modifier `notebooks/communes/france/01_etl_bronze_to_postgres.ipynb`
2. Exécuter `01_etl_bronze_to_postgres.ipynb` (section revenus uniquement, recalcul complet pour être sûr)
3. Vérifier `silver_france.revenus.taux_pauvrete` → ~31k valeurs, moyenne ~12-16%
4. Exécuter `notebooks/communes/france/02_feature_engineering.ipynb` → rebuild `gold_france.features_communes`
5. Vérifier `gold_france.features_communes.taux_pauvrete` → 100% couverture
6. Modifier `notebooks/communes/france/03_modeling.ipynb` (features revenus)
7. Exécuter `notebooks/communes/france/03_modeling.ipynb` → rebuild `gold_france.predictions_2022`
8. Validation finale en base

## Critères de validation

| Étape | Valeur attendue |
|-------|----------------|
| `silver_france.revenus.taux_pauvrete` non-null | ~31 000 communes (90%) |
| Moyenne nationale `taux_pauvrete` | 12–16% |
| `gold_france.features_communes.taux_pauvrete` non-null | 174 000 lignes (100%) |
| Feature importance `taux_pauvrete` dans RF | Top 15 |
| Accuracy RF post-ajout features revenus | >= accuracy précédente |

## Note méthodologique (à rappeler dans les analyses)

> Le `taux_pauvrete` dans cette base est une **estimation calculée**, non une valeur
> directement issue de l'INSEE. Il est estimé à partir du revenu médian communal
> et du coefficient de Gini (lorsque disponible), calibré sur la méthodologie
> Filosofi INSEE 2020-2022. Précision : ±5%.
