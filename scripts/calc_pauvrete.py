"""
Script de calcul du taux de pauvreté estimé pour silver_france.revenus
Formule à 3 niveaux basée sur médiane + gini (cf. PLAN_TAUX_PAUVRETE.md)
"""
import psycopg2
import sys

# Paramètres nationaux
MEDIANE_NATIONALE = 22810.0
SEUIL_PAUVRETE = 13686.0  # 60% médiane nationale

conn = psycopg2.connect(
    host="postgres",
    port=5432,
    database="mspr813",
    user="mspr_user",
    password="mspr_password"
)
cur = conn.cursor()

print("Récupération des données revenus...", flush=True)
cur.execute("""
    SELECT code_commune, mediane_revenu_disp, gini
    FROM silver_france.revenus
""")
rows = cur.fetchall()
print(f"  → {len(rows)} communes récupérées", flush=True)

def calcul_taux(mediane, gini):
    """Calcul du taux de pauvreté estimé — formule 3 niveaux."""
    if mediane is None:
        return None  # Niveau 3 : imputation via 05b

    mediane = float(mediane)
    if gini is not None:
        gini = float(gini)
        # Niveau 1 : Gini + médiane disponibles
        if mediane < SEUIL_PAUVRETE:
            taux = 35.0 + (gini - 0.25) * 80.0
        else:
            taux = -5.0 + (gini - 0.20) * 100.0
            ratio = mediane / MEDIANE_NATIONALE
            if ratio < 0.75:
                taux *= 1.4
            elif ratio > 1.25:
                taux *= 0.6
        return max(0.0, min(50.0, taux))
    else:
        # Niveau 2 : médiane seule
        seuil_bas = SEUIL_PAUVRETE * 0.80  # ~10 950 €
        if mediane < seuil_bas:
            return 40.0
        elif mediane < SEUIL_PAUVRETE:
            # interpolation linéaire 40% → 25%
            ratio = (mediane - seuil_bas) / (SEUIL_PAUVRETE - seuil_bas)
            return 40.0 - ratio * 15.0
        elif mediane < MEDIANE_NATIONALE * 0.90:
            return 15.0
        elif mediane < MEDIANE_NATIONALE * 1.10:
            return 10.0
        elif mediane < MEDIANE_NATIONALE * 1.30:
            return 6.0
        else:
            return 3.0

print("Calcul des taux de pauvreté...", flush=True)
updates = []
niveau1 = niveau2 = niveau3 = 0

for code_insee, mediane, gini in rows:
    taux = calcul_taux(mediane, gini)
    if taux is not None:
        updates.append((taux, code_insee))
        if gini is not None:
            niveau1 += 1
        else:
            niveau2 += 1
    else:
        niveau3 += 1

print(f"  → Niveau 1 (gini+médiane) : {niveau1} communes", flush=True)
print(f"  → Niveau 2 (médiane seule) : {niveau2} communes", flush=True)
print(f"  → Niveau 3 (sans données, imputation 05b) : {niveau3} communes", flush=True)
print(f"  → Total à mettre à jour : {len(updates)} communes", flush=True)

print("Mise à jour en base (batch)...", flush=True)
# Mise à jour par batch de 5000
BATCH_SIZE = 5000
for i in range(0, len(updates), BATCH_SIZE):
    batch = updates[i:i+BATCH_SIZE]
    cur.executemany(
        "UPDATE silver_france.revenus SET taux_pauvrete = %s WHERE code_commune = %s",
        batch
    )
    conn.commit()
    print(f"  → {min(i+BATCH_SIZE, len(updates))} / {len(updates)} mises à jour", flush=True)

print("Validation...", flush=True)
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(taux_pauvrete) as non_null,
        ROUND(AVG(taux_pauvrete)::numeric, 2) as moyenne,
        ROUND(MIN(taux_pauvrete)::numeric, 2) as min_val,
        ROUND(MAX(taux_pauvrete)::numeric, 2) as max_val
    FROM silver_france.revenus
""")
row = cur.fetchone()
print(f"\n=== RÉSULTATS ===", flush=True)
print(f"  Total communes    : {row[0]}", flush=True)
print(f"  Non-null          : {row[1]}", flush=True)
print(f"  Moyenne           : {row[2]}%", flush=True)
print(f"  Min               : {row[3]}%", flush=True)
print(f"  Max               : {row[4]}%", flush=True)

cur.close()
conn.close()
print("\nTerminé.", flush=True)
