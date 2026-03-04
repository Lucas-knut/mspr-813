#!/usr/bin/env python3
"""Generate the ETL notebook 04_etl_bronze_to_postgres.ipynb"""
import json
import os

cells = []

def md(source):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    })

def code(source):
    cells.append({
        "cell_type": "code",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")],
        "outputs": [],
        "execution_count": None
    })

# ============================================================
# CELL 0: Markdown intro
# ============================================================
md("""# 04 - ETL Bronze → Silver (PostgreSQL)

**Architecture Medallion – Couche Silver**

Ce notebook charge les données brutes (Bronze) et les insère dans la base PostgreSQL `mspr813`, schéma `silver`.

| Table | Source Bronze | Lignes attendues |
|-------|--------------|------------------|
| `silver.referentiel_communes` | referentiels_cog/referentiel_communes_2024.csv | ~144 |
| `silver.elections` | elections_agregees_1999_2024.csv | ~1.5M (144 communes avec Paris arr.) |
| `silver.population` | population_historique/DS_RP_SERIE_HISTORIQUE_2022_data.csv | ~1300 |
| `silver.revenus` | impots/ircom_communes_complet_revenus_{2002..2022}.xlsx | ~720 |
| `silver.emploi` | emploi_chomage/DS_RP_EMPLOI_LR_COMP_2022_data.csv | ~430 |
| `silver.csp` | csp_actifs_2554/pop-act2554-csp-cd-6822.xlsx | ~143 |
| `silver.diplomes` | diplomes_formation_2022/base-cc-diplomes-formation-2022.xlsx | ~142 |
| `silver.insecurite` | insecurite/donnee-dep-*.csv | ~300 |
| `silver.immigration` | immigration/IM_119_immigres_par_departement_1968_2021.xlsx | ~16 |""")

# ============================================================
# CELL 1: Config markdown
# ============================================================
md("## 0. Configuration & imports")

# ============================================================
# CELL 2: Imports + config
# ============================================================
code("""import os
import re
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# --- Configuration ---
BRONZE_DIR = "/app/data/bronze"

PG_HOST     = os.environ.get("POSTGRES_HOST",     "postgres")
PG_PORT     = os.environ.get("POSTGRES_PORT",     "5432")
PG_DB       = os.environ.get("POSTGRES_DB",       "mspr813")
PG_USER     = os.environ.get("POSTGRES_USER",     "mspr_user")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "mspr_password")

DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

DEPS_PC = ['75', '92', '93', '94']
IRCOM_YEARS = [2002, 2007, 2012, 2017, 2022]

engine = create_engine(DB_URL, pool_pre_ping=True)
print(f"Connexion : {PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DB}")

with engine.connect() as conn:
    r = conn.execute(text("SELECT current_database(), current_schema()"))
    print("PostgreSQL OK :", r.fetchone())""")

# ============================================================
# CELL 3: Utilities markdown
# ============================================================
md("## 0b. Fonctions utilitaires")

# ============================================================
# CELL 4: Utility functions
# ============================================================
code("""def extract_year(id_election):
    m = re.search(r'(\\d{4})', str(id_election))
    return int(m.group(1)) if m else None

def extract_type(id_election):
    parts = str(id_election).split('_')
    return parts[1] if len(parts) >= 2 else None

def extract_tour(id_election):
    m = re.search(r't(\\d)', str(id_election))
    return int(m.group(1)) if m else None

def get_paris_pop_weights(engine):
    \"\"\"Poids population des arrondissements parisiens (dernière année dispo).\"\"\"
    query = \"\"\"
    SELECT code_commune, population
    FROM silver.population
    WHERE code_commune LIKE '751%%'
      AND annee = (SELECT MAX(annee) FROM silver.population WHERE code_commune LIKE '751%%')
    \"\"\"
    df = pd.read_sql(query, engine)
    if df.empty:
        print("WARN: pas de données population pour Paris arrondissements")
        return {}
    total = df['population'].sum()
    df['weight'] = df['population'] / total
    return df.set_index('code_commune'.strip())['weight'].to_dict()

def distribute_paris_to_arrondissements(df_paris_rows, pop_weights, value_cols):
    \"\"\"Distribue les données de Paris 75056 vers les 20 arrondissements.\"\"\"
    distributed = []
    for _, row in df_paris_rows.iterrows():
        for code_arr, weight in pop_weights.items():
            new_row = row.copy()
            new_row['code_commune'] = code_arr
            for col in value_cols:
                if col in new_row.index and pd.notna(new_row[col]):
                    new_row[col] = new_row[col] * weight
            distributed.append(new_row)
    return pd.DataFrame(distributed)""")

# ============================================================
# CELL 5: Referentiel markdown
# ============================================================
md("""## 1. Référentiel communes (COG 2024)
Source : `referentiels_cog/referentiel_communes_2024.csv`""")

# ============================================================
# CELL 6: Referentiel load + insert
# ============================================================
code("""cog_path = os.path.join(BRONZE_DIR, "referentiels_cog", "referentiel_communes_2024.csv")
df_cog_raw = pd.read_csv(cog_path, sep=',', dtype=str, low_memory=False)
print("Colonnes:", df_cog_raw.columns.tolist())
print("Shape:", df_cog_raw.shape)

df_cog = df_cog_raw.copy()
col_map = {c.upper(): c for c in df_cog.columns}

rename = {}
for src, tgt in [('COM','code_insee'), ('CODGEO','code_insee'),
                  ('LIBELLE','libelle'), ('NCC','libelle'),
                  ('DEP','code_dep'), ('REG','code_reg'),
                  ('STATUT','statut'), ('ARR','arr')]:
    if src in col_map:
        rename[col_map[src]] = tgt

df_cog = df_cog.rename(columns=rename)
df_cog = df_cog.loc[:, ~df_cog.columns.duplicated()]

keep = ['code_insee', 'libelle', 'code_dep', 'code_reg', 'statut', 'arr']
existing = [c for c in keep if c in df_cog.columns]
df_cog = df_cog[existing].copy()

df_cog['code_insee'] = df_cog['code_insee'].astype(str).str.zfill(5)
df_cog['code_dep_norm'] = df_cog['code_dep'].astype(str).str.lstrip('0').str.zfill(2)
df_cog = df_cog[df_cog['code_dep_norm'].isin(DEPS_PC)].copy()
df_cog = df_cog.drop(columns=['code_dep_norm'])

print(f"Communes Petite Couronne : {len(df_cog)}")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.referentiel_communes CASCADE"))

df_cog.to_sql('referentiel_communes', engine, schema='silver', if_exists='append',
              index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.referentiel_communes")).scalar()
    codes_pc = set(r[0] for r in conn.execute(
        text("SELECT code_insee FROM silver.referentiel_communes")))
print(f"silver.referentiel_communes : {n} lignes")""")

# ============================================================
# CELL 7: Elections markdown
# ============================================================
md("""## 2. Élections 1999-2024 (fix Paris arrondissements)
Source : `elections_agregees_1999_2024.csv`

**Fix Paris** : `code_commune=75056` → extraire n° arrondissement depuis `code_bv` (2 premiers chiffres) → `code_commune = '751' + arr_num`""")

# ============================================================
# CELL 8: Elections load with Paris fix
# ============================================================
code("""elec_path = os.path.join(BRONZE_DIR, "elections_agregees_1999_2024.csv")

# Ajouter 75056 au filtre (sera éclaté en arrondissements)
codes_pc_elec = codes_pc | {'75056'}

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.elections"))

CHUNK_SIZE = 50_000
total_rows = 0

reader = pd.read_csv(elec_path, sep=';', chunksize=CHUNK_SIZE, dtype=str, low_memory=False)

for i, chunk in enumerate(reader):
    chunk['code_commune'] = chunk['code_commune'].astype(str).str.zfill(5)
    chunk = chunk[chunk['code_commune'].isin(codes_pc_elec)].copy()
    if chunk.empty:
        continue

    # Fix Paris : 75056 → arrondissements via code_bv
    mask_paris = chunk['code_commune'] == '75056'
    if mask_paris.any():
        arr_num = chunk.loc[mask_paris, 'code_bv'].astype(str).str[:2]
        chunk.loc[mask_paris, 'code_commune'] = '751' + arr_num

    # Supprimer les éventuels 75056 restants (code_bv manquant)
    chunk = chunk[chunk['code_commune'] != '75056'].copy()

    # Colonnes dérivées
    chunk['annee']         = chunk['id_election'].apply(extract_year).astype('Int16')
    chunk['type_election'] = chunk['id_election'].apply(extract_type)
    chunk['tour']          = chunk['id_election'].apply(extract_tour).astype('Int8')

    # Renommer colonnes Bronze → Silver
    chunk = chunk.rename(columns={
        'nuance': 'nuance_liste',
        'liste': 'nom_liste',
        'nom': 'nom_candidat',
        'prenom': 'prenom_candidat',
        'voix': 'nb_voix',
        'ratio_voix_inscrits': 'pct_voix_ins',
        'ratio_voix_exprimes': 'pct_voix_exp',
    })

    silver_cols = ['code_commune', 'id_election', 'annee', 'type_election', 'tour',
                   'nuance_liste', 'nom_liste', 'nom_candidat', 'prenom_candidat',
                   'sexe', 'nb_voix', 'pct_voix_ins', 'pct_voix_exp',
                   'inscrits', 'votants', 'exprimes']
    chunk = chunk[[c for c in silver_cols if c in chunk.columns]].copy()

    for col in ['nb_voix', 'inscrits', 'votants', 'exprimes']:
        if col in chunk.columns:
            chunk[col] = pd.to_numeric(chunk[col], errors='coerce').astype('Int64')
    for col in ['pct_voix_ins', 'pct_voix_exp']:
        if col in chunk.columns:
            chunk[col] = pd.to_numeric(
                chunk[col].astype(str).str.replace(',', '.', regex=False), errors='coerce')

    chunk.to_sql('elections', engine, schema='silver', if_exists='append',
                 index=False, method='multi', chunksize=2000)
    total_rows += len(chunk)

    if (i + 1) % 20 == 0:
        print(f"  Chunk {i+1} | {total_rows:,} rows")

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.elections")).scalar()
    nc = conn.execute(text("SELECT COUNT(DISTINCT code_commune) FROM silver.elections")).scalar()
print(f"\\nsilver.elections : {n:,} lignes, {nc} communes distinctes")""")

# ============================================================
# CELL 9: Population markdown
# ============================================================
md("""## 3. Population historique (naissances, décès, population)
Source : `population_historique/DS_RP_SERIE_HISTORIQUE_2022_data.csv`

Remplace les anciennes tables `naissances` et `deces`.
Format INSEE SDMX : `GEO_OBJECT IN ('COM','ARM')`, mesures `POP`, `BRTH`, `DEATH`.
Années census : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022.
Paris arrondissements (75101-75120) disponibles nativement.""")

# ============================================================
# CELL 10: Population load + insert
# ============================================================
code("""pop_path = os.path.join(BRONZE_DIR, "population_historique", "DS_RP_SERIE_HISTORIQUE_2022_data.csv")
df_pop_raw = pd.read_csv(pop_path, sep=';', dtype=str, low_memory=False)
print(f"Shape brut : {df_pop_raw.shape}")

# Filtrer : COM/ARM, mesures POP/BRTH/DEATH
df_pop = df_pop_raw[df_pop_raw['GEO_OBJECT'].isin(['COM', 'ARM'])].copy()
df_pop = df_pop[df_pop['RP_MEASURE'].isin(['POP', 'BRTH', 'DEATH'])].copy()

# Code commune et filtre PC
df_pop['code_commune'] = df_pop['GEO'].astype(str).str.zfill(5)
df_pop['code_dep'] = df_pop['code_commune'].str[:2]
df_pop = df_pop[df_pop['code_dep'].isin(DEPS_PC)].copy()

df_pop['annee'] = pd.to_numeric(df_pop['TIME_PERIOD'], errors='coerce').astype('Int16')
df_pop['value'] = pd.to_numeric(df_pop['OBS_VALUE'], errors='coerce')

# Pivot : une ligne par commune+année avec colonnes POP, BRTH, DEATH
df_pop_pivot = df_pop.pivot_table(
    index=['code_commune', 'annee'],
    columns='RP_MEASURE',
    values='value',
    aggfunc='sum'
).reset_index()

df_pop_pivot.columns.name = None
df_pop_pivot = df_pop_pivot.rename(columns={
    'POP': 'population',
    'BRTH': 'nb_naissances',
    'DEATH': 'nb_deces'
})

for col in ['population', 'nb_naissances', 'nb_deces']:
    if col in df_pop_pivot.columns:
        df_pop_pivot[col] = df_pop_pivot[col].astype('Int64')

print(f"Population Silver : {len(df_pop_pivot)} lignes, {df_pop_pivot['code_commune'].nunique()} communes")
print(f"Années : {sorted(df_pop_pivot['annee'].dropna().unique())}")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.population"))

df_pop_pivot.to_sql('population', engine, schema='silver', if_exists='append',
                    index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.population")).scalar()
print(f"silver.population : {n} lignes")""")

# ============================================================
# CELL 11: Revenus markdown
# ============================================================
md("""## 4. Revenus fiscaux IRCOM
Source : `impots/ircom_communes_complet_revenus_{2002,2007,2012,2017,2022}.xlsx`

Chaque fichier Excel : skiprows=5, 1ère ligne = sous-en-tête, filtrer sur tranche "Total".
`code_commune = Dép.(2 chars) + Commune(3 chars)`.
Paris (75056) distribué proportionnellement aux arrondissements via poids population.""")

# ============================================================
# CELL 12: Revenus IRCOM load + insert
# ============================================================
code("""ircom_rows = []

for year in IRCOM_YEARS:
    path = os.path.join(BRONZE_DIR, "impots", f"ircom_communes_complet_revenus_{year}.xlsx")
    if not os.path.exists(path):
        print(f"WARN: {path} introuvable, ignoré")
        continue

    df = pd.read_excel(path, skiprows=5, dtype=str, engine='openpyxl')

    # Supprimer la ligne sous-en-tête (row 0 = NaN metadata)
    df = df.iloc[1:].copy()

    # Filtrer lignes "Total" uniquement
    tranche_cols = [c for c in df.columns if 'tranche' in str(c).lower()]
    if tranche_cols:
        tranche_col = tranche_cols[0]
        df = df[df[tranche_col] == 'Total'].copy()
    else:
        print(f"  WARN {year}: colonne tranche non trouvée")
        continue

    # Construire code_commune = Dép(2) + Commune(3)
    df['code_commune'] = (
        df['Dép.'].astype(str).str.split('.').str[0].str.zfill(2) +
        df['Commune'].astype(str).str.split('.').str[0].str.zfill(3)
    )

    # Filtrer Petite Couronne (inclut 75056 pour distribution ultérieure)
    df['code_dep'] = df['code_commune'].str[:2]
    df = df[df['code_dep'].isin(DEPS_PC)].copy()

    # Extraire colonnes numériques
    col_foyers = 'Nombre de foyers fiscaux'
    col_revenu = 'Revenu fiscal de référence des foyers fiscaux'
    col_impot = 'Impôt net (total)*'
    col_imposes = 'Nombre de foyers fiscaux imposés'

    for col in [col_foyers, col_revenu, col_impot, col_imposes]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.', regex=False).str.replace(' ', '', regex=False),
                errors='coerce')

    tmp = pd.DataFrame({
        'code_commune': df['code_commune'].values,
        'annee': year,
        'nb_foyers_fiscaux': df[col_foyers].values if col_foyers in df.columns else np.nan,
        'revenu_fiscal_ref': df[col_revenu].values if col_revenu in df.columns else np.nan,
        'impot_net': df[col_impot].values if col_impot in df.columns else np.nan,
        'nb_foyers_imposes': df[col_imposes].values if col_imposes in df.columns else np.nan,
    })

    ircom_rows.append(tmp)
    print(f"  {year}: {len(tmp)} communes")

df_rev = pd.concat(ircom_rows, ignore_index=True)

# Colonnes dérivées
df_rev['revenu_moyen_par_foyer'] = (df_rev['revenu_fiscal_ref'] / df_rev['nb_foyers_fiscaux']).round(2)
df_rev['taux_imposition'] = (df_rev['nb_foyers_imposes'] / df_rev['nb_foyers_fiscaux']).round(4)

# Distribuer Paris 75056 → 20 arrondissements
pop_weights = get_paris_pop_weights(engine)
if pop_weights:
    mask_paris = df_rev['code_commune'] == '75056'
    df_paris = df_rev[mask_paris]
    df_non_paris = df_rev[~mask_paris]

    if not df_paris.empty:
        value_cols = ['nb_foyers_fiscaux', 'revenu_fiscal_ref', 'impot_net', 'nb_foyers_imposes']
        df_distributed = distribute_paris_to_arrondissements(df_paris, pop_weights, value_cols)
        # Recalculer colonnes dérivées
        df_distributed['revenu_moyen_par_foyer'] = (
            df_distributed['revenu_fiscal_ref'] / df_distributed['nb_foyers_fiscaux']).round(2)
        df_distributed['taux_imposition'] = (
            df_distributed['nb_foyers_imposes'] / df_distributed['nb_foyers_fiscaux']).round(4)
        df_rev = pd.concat([df_non_paris, df_distributed], ignore_index=True)
        print(f"  Paris distribué : {len(df_paris)} lignes → {len(df_distributed)} lignes")

df_rev = df_rev.drop_duplicates(subset=['code_commune', 'annee'])
df_rev['annee'] = df_rev['annee'].astype('Int16')

# Types entiers
for col in ['nb_foyers_fiscaux', 'nb_foyers_imposes']:
    df_rev[col] = df_rev[col].round(0).astype('Int64')

print(f"Revenus Silver : {len(df_rev)} lignes, {df_rev['code_commune'].nunique()} communes")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.revenus"))

df_rev.to_sql('revenus', engine, schema='silver', if_exists='append',
              index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.revenus")).scalar()
print(f"silver.revenus : {n} lignes")""")

# ============================================================
# CELL 13: Emploi markdown
# ============================================================
md("""## 5. Emploi / chômage
Source : `emploi_chomage/DS_RP_EMPLOI_LR_COMP_2022_data.csv`

Format INSEE SDMX. Filtres : `GEO_OBJECT IN ('COM','ARM')`, `AGE='Y15T64'`, `PCS='_T'`.
- `EMPSTA_ENQ='1T2'` → actifs (total)
- `EMPSTA_ENQ='2'` → chômeurs""")

# ============================================================
# CELL 14: Emploi load + insert
# ============================================================
code("""emp_path = os.path.join(BRONZE_DIR, "emploi_chomage", "DS_RP_EMPLOI_LR_COMP_2022_data.csv")
df_emp_raw = pd.read_csv(emp_path, sep=';', dtype=str, low_memory=False)
print(f"Shape brut : {df_emp_raw.shape}")

# Filtrer : COM/ARM, âge 15-64, toutes CSP
df_emp = df_emp_raw[df_emp_raw['GEO_OBJECT'].isin(['COM', 'ARM'])].copy()
df_emp = df_emp[df_emp['AGE'] == 'Y15T64'].copy()
df_emp = df_emp[df_emp['PCS'] == '_T'].copy()

df_emp['code_commune'] = df_emp['GEO'].astype(str).str.zfill(5)
df_emp['code_dep'] = df_emp['code_commune'].str[:2]
df_emp = df_emp[df_emp['code_dep'].isin(DEPS_PC)].copy()

df_emp['annee'] = pd.to_numeric(df_emp['TIME_PERIOD'], errors='coerce').astype('Int16')
df_emp['value'] = pd.to_numeric(df_emp['OBS_VALUE'], errors='coerce')

# Actifs et chômeurs
df_actifs = df_emp[df_emp['EMPSTA_ENQ'] == '1T2'][['code_commune', 'annee', 'value']].rename(
    columns={'value': 'actifs'})
df_chom = df_emp[df_emp['EMPSTA_ENQ'] == '2'][['code_commune', 'annee', 'value']].rename(
    columns={'value': 'chomeurs'})

df_emploi = df_actifs.merge(df_chom, on=['code_commune', 'annee'], how='outer')
df_emploi['taux_chomage'] = (df_emploi['chomeurs'] / df_emploi['actifs'] * 100).round(3)

for col in ['actifs', 'chomeurs']:
    df_emploi[col] = df_emploi[col].astype('Int64')

df_emploi = df_emploi.drop_duplicates(subset=['code_commune', 'annee'])
print(f"Emploi Silver : {len(df_emploi)} lignes, {df_emploi['code_commune'].nunique()} communes")
print(f"Années : {sorted(df_emploi['annee'].dropna().unique())}")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.emploi"))

df_emploi.to_sql('emploi', engine, schema='silver', if_exists='append',
                 index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.emploi")).scalar()
print(f"silver.emploi : {n} lignes")""")

# ============================================================
# CELL 15: CSP markdown
# ============================================================
md("""## 6. CSP actifs 25-54 ans (RP 2022)
Source : `csp_actifs_2554/pop-act2554-csp-cd-6822.xlsx`
- Sheet : `COM_2022`, skiprows=15
- Code INSEE = DR (2 chars) + CR (3 chars)
- Paris arrondissements déjà présents dans les données""")

# ============================================================
# CELL 16: CSP load + insert
# ============================================================
code("""csp_path = os.path.join(BRONZE_DIR, "csp_actifs_2554", "pop-act2554-csp-cd-6822.xlsx")

df_csp_raw = pd.read_excel(csp_path, sheet_name='COM_2022', skiprows=15,
                            header=0, dtype=str, engine='openpyxl')
print(f"Shape brut : {df_csp_raw.shape}")

df_csp = df_csp_raw.copy()
df_csp['code_commune'] = (
    df_csp['DR'].astype(str).str.zfill(2) +
    df_csp['CR'].astype(str).str.zfill(3)
)

df_csp = df_csp[df_csp['code_commune'].isin(codes_pc)].copy()
df_csp['annee'] = 2022

col_mapping = {
    'csx_rec1taxtypac_rec1rpop2022': 'agriculteurs_emploi',
    'csx_rec1taxtypac_rec2rpop2022': 'agriculteurs_chomeurs',
    'csx_rec2taxtypac_rec1rpop2022': 'artisans_emploi',
    'csx_rec2taxtypac_rec2rpop2022': 'artisans_chomeurs',
    'csx_rec3taxtypac_rec1rpop2022': 'cadres_emploi',
    'csx_rec3taxtypac_rec2rpop2022': 'cadres_chomeurs',
    'csx_rec4taxtypac_rec1rpop2022': 'prof_interm_emploi',
    'csx_rec4taxtypac_rec2rpop2022': 'prof_interm_chomeurs',
    'csx_rec5taxtypac_rec1rpop2022': 'employes_emploi',
    'csx_rec5taxtypac_rec2rpop2022': 'employes_chomeurs',
    'csx_rec6taxtypac_rec1rpop2022': 'ouvriers_emploi',
    'csx_rec6taxtypac_rec2rpop2022': 'ouvriers_chomeurs',
}

df_csp_silver = df_csp[['code_commune', 'annee']].copy()
for bronze_col, silver_col in col_mapping.items():
    if bronze_col in df_csp.columns:
        df_csp_silver[silver_col] = pd.to_numeric(df_csp[bronze_col], errors='coerce')
    else:
        df_csp_silver[silver_col] = np.nan

df_csp_silver['annee'] = df_csp_silver['annee'].astype('Int16')
df_csp_silver = df_csp_silver.drop_duplicates(subset=['code_commune', 'annee'])

print(f"CSP Silver : {len(df_csp_silver)} communes")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.csp"))

df_csp_silver.to_sql('csp', engine, schema='silver', if_exists='append',
                     index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.csp")).scalar()
print(f"silver.csp : {n} lignes")""")

# ============================================================
# CELL 17: Diplomes markdown
# ============================================================
md("""## 7. Diplômes et formation (RP 2022)
Source : `diplomes_formation_2022/base-cc-diplomes-formation-2022.xlsx`
- Sheet : `COM_2022`, skiprows=5
- Paris (75056) distribué vers les 20 arrondissements via poids population""")

# ============================================================
# CELL 18: Diplomes load + insert
# ============================================================
code("""dipl_path = os.path.join(BRONZE_DIR, "diplomes_formation_2022", "base-cc-diplomes-formation-2022.xlsx")

df_dipl_raw = pd.read_excel(dipl_path, sheet_name='COM_2022', skiprows=5,
                             header=0, dtype=str, engine='openpyxl')
print(f"Shape brut : {df_dipl_raw.shape}")

df_dipl = df_dipl_raw.copy()
df_dipl = df_dipl.rename(columns={'CODGEO': 'code_commune'})
df_dipl['code_commune'] = df_dipl['code_commune'].astype(str).str.zfill(5)

# Filtrer PC (inclut 75056 pour distribution)
codes_pc_with_paris = codes_pc | {'75056'}
df_dipl = df_dipl[df_dipl['code_commune'].isin(codes_pc_with_paris)].copy()
df_dipl['annee'] = 2022

dipl_mapping = {
    'P22_NSCOL15P':          'nscol15p',
    'P22_NSCOL15P_DIPLMIN':  'sans_diplome',
    'P22_NSCOL15P_BEPC':     'bepc_brevet',
    'P22_NSCOL15P_CAPBEP':   'cap_bep',
    'P22_NSCOL15P_BAC':      'bac',
    'P22_NSCOL15P_SUP2':     'sup_bac2',
    'P22_NSCOL15P_SUP34':    'sup_bac34',
    'P22_NSCOL15P_SUP5':     'sup_bac5',
}

df_dipl_silver = df_dipl[['code_commune', 'annee']].copy()
for bronze_col, silver_col in dipl_mapping.items():
    if bronze_col in df_dipl.columns:
        df_dipl_silver[silver_col] = pd.to_numeric(df_dipl[bronze_col], errors='coerce')
    else:
        df_dipl_silver[silver_col] = np.nan

# Distribuer Paris 75056 → arrondissements si nécessaire
has_paris = '75056' in df_dipl_silver['code_commune'].values
has_arr = df_dipl_silver['code_commune'].str.startswith('751').any()

if has_paris and not has_arr:
    pop_weights = get_paris_pop_weights(engine)
    if pop_weights:
        mask_paris = df_dipl_silver['code_commune'] == '75056'
        df_paris_dipl = df_dipl_silver[mask_paris]
        df_non_paris_dipl = df_dipl_silver[~mask_paris]

        value_cols = list(dipl_mapping.values())
        df_distributed = distribute_paris_to_arrondissements(df_paris_dipl, pop_weights, value_cols)
        df_dipl_silver = pd.concat([df_non_paris_dipl, df_distributed], ignore_index=True)
        print(f"  Paris distribué : 1 ligne → {len(df_distributed)} arrondissements")

# Supprimer 75056 s'il reste (on garde uniquement les arrondissements)
df_dipl_silver = df_dipl_silver[df_dipl_silver['code_commune'] != '75056'].copy()

df_dipl_silver['annee'] = df_dipl_silver['annee'].astype('Int16')
df_dipl_silver = df_dipl_silver.drop_duplicates(subset=['code_commune', 'annee'])

print(f"Diplômes Silver : {len(df_dipl_silver)} communes")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.diplomes"))

df_dipl_silver.to_sql('diplomes', engine, schema='silver', if_exists='append',
                      index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.diplomes")).scalar()
print(f"silver.diplomes : {n} lignes")""")

# ============================================================
# CELL 19: Insecurite markdown
# ============================================================
md("""## 8. Insécurité (niveau département)
Source : `insecurite/donnee-dep-*.csv`

CSV simple, séparateur `;`. Filtrer départements 75/92/93/94.
Granularité : département × année × indicateur.""")

# ============================================================
# CELL 20: Insecurite load + insert
# ============================================================
code("""insec_dir = os.path.join(BRONZE_DIR, "insecurite")
insec_files = [f for f in os.listdir(insec_dir) if f.endswith('.csv')]
insec_path = os.path.join(insec_dir, insec_files[0])
print(f"Fichier : {insec_files[0]}")

df_insec = pd.read_csv(insec_path, sep=';', dtype=str, low_memory=False)
print(f"Shape brut : {df_insec.shape}")

# Filtrer départements PC
df_insec = df_insec[df_insec['Code_departement'].isin(DEPS_PC)].copy()

df_insec_silver = pd.DataFrame({
    'code_dep': df_insec['Code_departement'].values,
    'annee': pd.to_numeric(df_insec['annee'], errors='coerce').astype('Int16'),
    'indicateur': df_insec['indicateur'].values,
    'nombre': pd.to_numeric(df_insec['nombre'], errors='coerce').astype('Int64'),
    'taux_pour_mille': pd.to_numeric(
        df_insec['taux_pour_mille'].astype(str).str.replace(',', '.', regex=False),
        errors='coerce'),
})

df_insec_silver = df_insec_silver.drop_duplicates(subset=['code_dep', 'annee', 'indicateur'])
print(f"Insécurité Silver : {len(df_insec_silver)} lignes")
print(f"Indicateurs : {df_insec_silver['indicateur'].unique().tolist()}")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.insecurite"))

df_insec_silver.to_sql('insecurite', engine, schema='silver', if_exists='append',
                       index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.insecurite")).scalar()
print(f"silver.insecurite : {n} lignes")""")

# ============================================================
# CELL 21: Immigration markdown
# ============================================================
md("""## 9. Immigration (niveau département)
Source : `immigration/IM_119_immigres_par_departement_1968_2021.xlsx`

Sheet `Figure 2` : Part d'immigrés dans la population des départements.
Années disponibles : 1968, 1975, 1999, 2021.""")

# ============================================================
# CELL 22: Immigration load + insert
# ============================================================
code("""imm_path = os.path.join(BRONZE_DIR, "immigration",
                       "IM_119_immigres_par_departement_1968_2021.xlsx")

df_imm = pd.read_excel(imm_path, sheet_name='Figure 2', header=None, engine='openpyxl')
print(f"Shape brut : {df_imm.shape}")

# Trouver la ligne d'en-tête (contient "Département")
header_idx = None
for i in range(min(df_imm.shape[0], 60)):
    row_vals = [str(x) for x in df_imm.iloc[i].tolist()]
    if any('partement' in x.lower() for x in row_vals if x != 'nan'):
        header_idx = i
        break

if header_idx is None:
    raise ValueError("En-tête non trouvé dans Figure 2")

df_imm.columns = df_imm.iloc[header_idx]
df_imm = df_imm.iloc[header_idx + 1:].copy()

# Filtrer départements PC
df_imm['Code département'] = df_imm['Code département'].astype(str).str.zfill(2)
df_imm = df_imm[df_imm['Code département'].isin(DEPS_PC)].copy()

print(f"Départements PC trouvés : {df_imm['Code département'].unique().tolist()}")

# Pivoter années en lignes
year_cols = [c for c in df_imm.columns if isinstance(c, (int, float)) and not pd.isna(c) and c > 1900]
print(f"Années disponibles : {year_cols}")

df_imm_long = df_imm.melt(
    id_vars=['Code département'],
    value_vars=year_cols,
    var_name='annee',
    value_name='pct_immigres'
)
df_imm_long = df_imm_long.rename(columns={'Code département': 'code_dep'})
df_imm_long['annee'] = pd.to_numeric(df_imm_long['annee'], errors='coerce').astype('Int16')
df_imm_long['pct_immigres'] = pd.to_numeric(df_imm_long['pct_immigres'], errors='coerce').round(3)

# Supprimer la colonne "Évolution" si elle s'est glissée dans le melt
df_imm_long = df_imm_long.dropna(subset=['annee'])
df_imm_long = df_imm_long.drop_duplicates(subset=['code_dep', 'annee'])

print(f"Immigration Silver : {len(df_imm_long)} lignes")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE silver.immigration"))

df_imm_long.to_sql('immigration', engine, schema='silver', if_exists='append',
                    index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM silver.immigration")).scalar()
print(f"silver.immigration : {n} lignes")""")

# ============================================================
# CELL 23: Validation markdown
# ============================================================
md("## 10. Validation finale")

# ============================================================
# CELL 24: Validation queries
# ============================================================
code("""validation_queries = {
    'referentiel_communes': 'SELECT COUNT(*), COUNT(DISTINCT code_dep) FROM silver.referentiel_communes',
    'elections':   'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_commune) FROM silver.elections',
    'population':  'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_commune) FROM silver.population',
    'revenus':     'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_commune) FROM silver.revenus',
    'emploi':      'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_commune) FROM silver.emploi',
    'csp':         'SELECT COUNT(*), COUNT(DISTINCT code_commune) FROM silver.csp',
    'diplomes':    'SELECT COUNT(*), COUNT(DISTINCT code_commune) FROM silver.diplomes',
    'insecurite':  'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_dep) FROM silver.insecurite',
    'immigration': 'SELECT COUNT(*), MIN(annee), MAX(annee), COUNT(DISTINCT code_dep) FROM silver.immigration',
}

print("=" * 60)
print("VALIDATION SILVER LAYER")
print("=" * 60)

with engine.connect() as conn:
    for table, query in validation_queries.items():
        result = conn.execute(text(query)).fetchone()
        print(f"\\n{table}:")
        print(f"  → {result}")

print("\\n" + "=" * 60)
print("ETL Bronze → Silver terminé !")
print("=" * 60)""")

# ============================================================
# Build notebook JSON
# ============================================================
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "cells": cells
}

# Strip trailing newline from last line of each cell
for cell in notebook["cells"]:
    if cell["source"] and cell["source"][-1].endswith("\n"):
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "notebooks", "04_etl_bronze_to_postgres.ipynb"
)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook écrit : {output_path}")
print(f"Nombre de cellules : {len(cells)}")
