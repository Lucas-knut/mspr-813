#!/usr/bin/env python3
"""Generate the feature engineering notebook 05_feature_engineering.ipynb"""
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
md("""# 05 - Feature Engineering : Silver → Gold

**Architecture Medallion – Couche Gold**

Ce notebook construit la table `gold.features_communes` (~30 features) en :
1. Agrégeant les résultats présidentiels T1 par commune × année → variable cible (bloc dominant)
2. Joignant les features socio-économiques (population, revenus IRCOM, emploi, CSP, diplômes)
3. Joignant les features contextuelles (insécurité, immigration — niveau département)
4. Créant des features dérivées (ratios, indicateurs géographiques)

### Alignement temporel
| Élection | Census | IRCOM |
|----------|--------|-------|
| 2002 | 1999 | 2002 |
| 2007 | 2006 | 2007 |
| 2012 | 2011 | 2012 |
| 2017 | 2016 | 2017 |
| 2022 | 2022 | 2022 |

### Variable cible : Bloc dominant
| Bloc | Exemples de nuances |
|------|---------------------|
| **Gauche** | EXG, COM, SOC, DVG, FG, NUP, LFI, ECO, VEC |
| **Centre** | ENS, REM, BAYR, UDF, MDM, UDI, DVC |
| **Droite** | UMP, LR, RPR, DVD, DLF |
| **ExtrêmeDroite** | FN, RN, MNR, REC, EXD |
| **Divers** | DIV, AUT, REG |""")

# ============================================================
md("## 0. Configuration & imports")
code("""import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

PG_HOST     = os.environ.get("POSTGRES_HOST",     "postgres")
PG_PORT     = os.environ.get("POSTGRES_PORT",     "5432")
PG_DB       = os.environ.get("POSTGRES_DB",       "mspr813")
PG_USER     = os.environ.get("POSTGRES_USER",     "mspr_user")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "mspr_password")

DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(DB_URL, pool_pre_ping=True)

# Alignement élection → census → IRCOM
ELECTION_TO_CENSUS = {2002: 1999, 2007: 2006, 2012: 2011, 2017: 2016, 2022: 2022}
ELECTION_YEARS = [2002, 2007, 2012, 2017, 2022]

with engine.connect() as conn:
    print("PostgreSQL OK :", conn.execute(text("SELECT current_database()")).scalar())""")

# ============================================================
md("## 1. Schéma Gold")
code("""with engine.begin() as conn:
    conn.execute(text(\"\"\"
        CREATE SCHEMA IF NOT EXISTS gold;
        DROP TABLE IF EXISTS gold.features_communes CASCADE;

        CREATE TABLE gold.features_communes (
            -- Clé
            code_commune        CHAR(5)      NOT NULL,
            annee               SMALLINT     NOT NULL,
            libelle             VARCHAR(100),
            code_dep            CHAR(3),

            -- Variable cible (présidentielle T1)
            pct_gauche          NUMERIC(6,3),
            pct_centre          NUMERIC(6,3),
            pct_droite          NUMERIC(6,3),
            pct_extremedroite   NUMERIC(6,3),
            pct_divers          NUMERIC(6,3),
            bloc_dominant       VARCHAR(20),

            -- Démographie (population historique)
            population          INTEGER,
            nb_naissances       INTEGER,
            nb_deces            INTEGER,
            solde_naturel       INTEGER,
            taux_natalite       NUMERIC(6,3),
            taux_mortalite      NUMERIC(6,3),

            -- Revenus (IRCOM)
            revenu_moyen_par_foyer  NUMERIC(10,2),
            taux_imposition         NUMERIC(6,4),

            -- Emploi
            taux_chomage        NUMERIC(6,3),

            -- CSP (2022, répliqué)
            cadres_pct          NUMERIC(6,3),
            ouvriers_pct        NUMERIC(6,3),
            employes_pct        NUMERIC(6,3),
            artisans_pct        NUMERIC(6,3),
            ratio_cadres_ouvriers NUMERIC(8,3),

            -- Diplômes (2022, répliqué)
            pct_bac_plus        NUMERIC(6,3),
            pct_sans_diplome    NUMERIC(6,3),

            -- Insécurité (département)
            taux_crimes_mille   NUMERIC(10,5),

            -- Immigration (département)
            pct_immigres        NUMERIC(6,3),

            -- Contexte géographique
            is_paris            BOOLEAN,
            is_93               BOOLEAN,

            -- Métadonnées
            created_at          TIMESTAMP DEFAULT NOW(),
            CONSTRAINT pk_gold_features PRIMARY KEY (code_commune, annee)
        );
    \"\"\"))
print("Schéma gold créé")""")

# ============================================================
md("## 2. Mapping nuance → bloc politique")
code("""NUANCE_TO_BLOC = {
    # GAUCHE
    'EXG': 'Gauche', 'LEXG': 'Gauche', 'LXG': 'Gauche', 'DXG': 'Gauche',
    'COM': 'Gauche', 'LCOM': 'Gauche',
    'SOC': 'Gauche', 'LSOC': 'Gauche',
    'DVG': 'Gauche', 'LDVG': 'Gauche',
    'FG':  'Gauche', 'LFG':  'Gauche',
    'NUP': 'Gauche', 'LFI': 'Gauche', 'FI': 'Gauche',
    'ECO': 'Gauche', 'LECO': 'Gauche',
    'VEC': 'Gauche', 'LVEC': 'Gauche',
    'LCR': 'Gauche', 'LO': 'Gauche',
    'PG':  'Gauche', 'LPG': 'Gauche',
    'BC-EXG': 'Gauche', 'BC-DVG': 'Gauche', 'BC-FG': 'Gauche',
    'BC-SOC': 'Gauche', 'BC-FI': 'Gauche', 'BC-COM': 'Gauche',
    'BC-VEC': 'Gauche', 'BC-ECO': 'Gauche', 'BC-PG': 'Gauche',
    'BC-UCG': 'Gauche', 'GAU': 'Gauche', 'PREP': 'Gauche',
    'MELE': 'Gauche', 'HOLL': 'Gauche', 'ROYA': 'Gauche',
    'BUFF': 'Gauche', 'VOYN': 'Gauche', 'BESA': 'Gauche',
    'ARTH': 'Gauche', 'POUT': 'Gauche', 'GLUC': 'Gauche',
    'HUE': 'Gauche', 'JOSP': 'Gauche', 'BOVE': 'Gauche',
    'TAUB': 'Gauche', 'JOLY': 'Gauche', 'MAME': 'Gauche',
    # CENTRE
    'ENS': 'Centre', 'REM': 'Centre', 'LREM': 'Centre',
    'BC-REM': 'Centre', 'BC-MDM': 'Centre',
    'BAYR': 'Centre', 'LCOP': 'Centre',
    'UDF': 'Centre', 'LUDF': 'Centre',
    'MODM': 'Centre', 'LMDM': 'Centre', 'MDM': 'Centre', 'MDC': 'Centre',
    'UDI': 'Centre', 'LUDI': 'Centre', 'BC-UDI': 'Centre',
    'LUD': 'Centre', 'UG': 'Centre', 'LUG': 'Centre', 'LUC': 'Centre',
    'LUGE': 'Centre', 'DVC': 'Centre', 'LDVC': 'Centre', 'LCMD': 'Centre',
    'BC-UC': 'Centre', 'BC-UCD': 'Centre', 'BC-DVC': 'Centre',
    'NCE': 'Centre', 'M': 'Centre', 'M-NC': 'Centre',
    'CHEV': 'Centre', 'LEPAGE': 'Centre', 'LASA': 'Centre',
    # DROITE
    'UMP': 'Droite', 'LUMP': 'Droite', 'BC-UMP': 'Droite',
    'LR': 'Droite', 'LLR': 'Droite', 'BC-LR': 'Droite',
    'RPR': 'Droite', 'RPF': 'Droite',
    'DVD': 'Droite', 'LDVD': 'Droite', 'BC-DVD': 'Droite',
    'DLF': 'Droite', 'LDLF': 'Droite', 'BC-DLF': 'Droite',
    'MPF': 'Droite', 'UDFD': 'Droite', 'CPNT': 'Droite',
    'SARK': 'Droite', 'CHIR': 'Droite', 'MADE': 'Droite',
    'PECA': 'Droite', 'FILL': 'Droite',
    'VILL': 'Droite', 'NIHO': 'Droite', 'SCHI': 'Droite',
    'BOUT': 'Droite', 'DUPO': 'Droite', 'CHEM': 'Droite',
    'SAIN': 'Droite', 'LAGU': 'Droite',
    # EXTREME DROITE
    'FN': 'ExtremeDroite', 'LFN': 'ExtremeDroite',
    'RN': 'ExtremeDroite', 'LRN': 'ExtremeDroite', 'BC-RN': 'ExtremeDroite',
    'MNR': 'ExtremeDroite', 'MEGR': 'ExtremeDroite',
    'LEPA': 'ExtremeDroite',
    'EXD': 'ExtremeDroite', 'LEXD': 'ExtremeDroite', 'LXD': 'ExtremeDroite',
    'BC-EXD': 'ExtremeDroite', 'BC-FN': 'ExtremeDroite',
    'REC': 'ExtremeDroite', 'LREC': 'ExtremeDroite',
    'DTE': 'ExtremeDroite', 'FRN': 'ExtremeDroite', 'MNA': 'ExtremeDroite',
    'UXD': 'ExtremeDroite',
    # DIVERS
    'DIV': 'Divers', 'LDIV': 'Divers', 'LDV': 'Divers',
    'AUT': 'Divers', 'LAUT': 'Divers', 'BC-DIV': 'Divers', 'REG': 'Divers',
    'LDD': 'Divers', 'DSV': 'Divers',
    'BC-RDG': 'Divers', 'RDG': 'Divers', 'PRG': 'Divers', 'PRV': 'Divers',
    'ALLI': 'Divers', 'LAGE': 'Divers', 'LDR': 'Divers',
}

CANDIDAT_PRES_TO_BLOC = {
    'ARTHAUD': 'Gauche', 'POUTOU': 'Gauche', 'MELENCHON': 'Gauche',
    'MÉLENCHON': 'Gauche', 'JADOT': 'Gauche', 'HIDALGO': 'Gauche',
    'ROUSSEL': 'Gauche', 'HAMON': 'Gauche', 'HOLLANDE': 'Gauche',
    'ROYAL': 'Gauche', 'JOSPIN': 'Gauche', 'BUFFET': 'Gauche',
    'VOYNET': 'Gauche', 'BESANCENOT': 'Gauche', 'GLUCKSTEIN': 'Gauche',
    'HUE': 'Gauche', 'MAMERE': 'Gauche', 'BOVÉ': 'Gauche',
    'TAUBIRA': 'Gauche', 'JOLY': 'Gauche', 'LAGUILLER': 'Gauche',
    'MACRON': 'Centre', 'BAYROU': 'Centre', 'CHEVENEMENT': 'Centre',
    'LEPAGE': 'Centre', 'LASSALLE': 'Centre',
    'SARKOZY': 'Droite', 'CHIRAC': 'Droite', 'FILLON': 'Droite',
    'PÉCRESSE': 'Droite', 'MADELIN': 'Droite', 'de VILLIERS': 'Droite',
    'NIHOUS': 'Droite', 'SCHIVARDI': 'Droite', 'BOUTIN': 'Droite',
    'DUPONT-AIGNAN': 'Droite', 'SAINT-JOSSE': 'Droite',
    'ASSELINEAU': 'Droite', 'CHEMINADE': 'Divers',
    'LE PEN': 'ExtremeDroite', 'ZEMMOUR': 'ExtremeDroite',
    'MEGRET': 'ExtremeDroite',
}

print(f"Mapping nuances : {len(NUANCE_TO_BLOC)} entrées")
print(f"Mapping candidats : {len(CANDIDAT_PRES_TO_BLOC)} entrées")""")

# ============================================================
md("""## 3. Agrégation électorale par commune × année

Présidentielles T1 : 2002, 2007, 2012, 2017, 2022.
Maintenant avec 144 communes (Paris arrondissements séparés).""")

code("""df_elec = pd.read_sql(\"\"\"
    SELECT code_commune, id_election, annee, nuance_liste, nom_candidat, nb_voix
    FROM silver.elections
    WHERE type_election = 'pres' AND tour = 1
      AND nb_voix IS NOT NULL
\"\"\", engine)

print(f"Lignes présidentielles T1 : {len(df_elec):,}")
print(f"Années : {sorted(df_elec['annee'].unique())}")
print(f"Communes : {df_elec['code_commune'].nunique()}")

# Attribution bloc
def get_bloc(row):
    if pd.notna(row['nuance_liste']) and row['nuance_liste'] != '':
        b = NUANCE_TO_BLOC.get(row['nuance_liste'])
        if b:
            return b
    if pd.notna(row['nom_candidat']) and row['nom_candidat'] != '':
        nom = row['nom_candidat'].upper().strip()
        b = CANDIDAT_PRES_TO_BLOC.get(nom)
        if b:
            return b
        for k, v in CANDIDAT_PRES_TO_BLOC.items():
            if k.upper() in nom or nom in k.upper():
                return v
    return 'Divers'

df_elec['bloc'] = df_elec.apply(get_bloc, axis=1)

print("\\nDistribution voix par bloc:")
print(df_elec.groupby('bloc')['nb_voix'].sum().sort_values(ascending=False).to_string())""")

code("""# Agréger par commune × année × bloc
df_bloc = df_elec.groupby(['code_commune', 'annee', 'bloc'], as_index=False)['nb_voix'].sum()
df_total = df_elec.groupby(['code_commune', 'annee'], as_index=False)['nb_voix'].sum().rename(
    columns={'nb_voix': 'total_voix'})

df_bloc = df_bloc.merge(df_total, on=['code_commune', 'annee'])
df_bloc['pct'] = df_bloc['nb_voix'] / df_bloc['total_voix'] * 100

# Pivoter
df_pivot = df_bloc.pivot_table(
    index=['code_commune', 'annee'], columns='bloc', values='pct', fill_value=0
).reset_index()
df_pivot.columns.name = None

for bloc in ['Gauche', 'Centre', 'Droite', 'ExtremeDroite', 'Divers']:
    if bloc not in df_pivot.columns:
        df_pivot[bloc] = 0.0

df_pivot = df_pivot.rename(columns={
    'Gauche': 'pct_gauche', 'Centre': 'pct_centre',
    'Droite': 'pct_droite', 'ExtremeDroite': 'pct_extremedroite',
    'Divers': 'pct_divers',
})

# Bloc dominant
blocs_cols = ['pct_gauche', 'pct_centre', 'pct_droite', 'pct_extremedroite']
bloc_labels = ['Gauche', 'Centre', 'Droite', 'ExtremeDroite']
df_pivot['bloc_dominant'] = df_pivot[blocs_cols].idxmax(axis=1).map(
    dict(zip(blocs_cols, bloc_labels)))

print(f"Shape pivot : {df_pivot.shape}")
print(f"\\nDistribution blocs dominants:")
print(df_pivot.groupby(['annee', 'bloc_dominant']).size().to_string())""")

# ============================================================
md("## 4. Chargement des features Silver")

code("""# Référentiel communes
df_ref = pd.read_sql(\"\"\"
    SELECT code_insee AS code_commune, libelle, code_dep
    FROM silver.referentiel_communes
\"\"\", engine)
print(f"Référentiel : {len(df_ref)} communes")

# Population historique (remplace naissances/décès)
df_pop = pd.read_sql(\"\"\"
    SELECT code_commune, annee, population, nb_naissances, nb_deces
    FROM silver.population
\"\"\", engine)
print(f"Population : {len(df_pop)} lignes, {df_pop['code_commune'].nunique()} communes")

# Revenus IRCOM
df_rev = pd.read_sql(\"\"\"
    SELECT code_commune, annee, revenu_moyen_par_foyer, taux_imposition
    FROM silver.revenus
\"\"\", engine)
print(f"Revenus : {len(df_rev)} lignes, {df_rev['code_commune'].nunique()} communes")

# Emploi
df_emp = pd.read_sql(\"\"\"
    SELECT code_commune, annee, taux_chomage
    FROM silver.emploi
\"\"\", engine)
print(f"Emploi : {len(df_emp)} lignes, {df_emp['code_commune'].nunique()} communes")

# CSP (2022)
df_csp = pd.read_sql(\"\"\"
    SELECT code_commune,
           cadres_emploi, ouvriers_emploi, employes_emploi, artisans_emploi,
           prof_interm_emploi, agriculteurs_emploi
    FROM silver.csp WHERE annee = 2022
\"\"\", engine)

total_emp = (df_csp[['cadres_emploi','ouvriers_emploi','employes_emploi',
                      'artisans_emploi','prof_interm_emploi','agriculteurs_emploi']]
             .sum(axis=1))
df_csp['cadres_pct']   = (df_csp['cadres_emploi']   / total_emp * 100).round(3)
df_csp['ouvriers_pct'] = (df_csp['ouvriers_emploi'] / total_emp * 100).round(3)
df_csp['employes_pct'] = (df_csp['employes_emploi'] / total_emp * 100).round(3)
df_csp['artisans_pct'] = (df_csp['artisans_emploi'] / total_emp * 100).round(3)
df_csp['ratio_cadres_ouvriers'] = (df_csp['cadres_emploi'] / df_csp['ouvriers_emploi'].replace(0, np.nan)).round(3)
df_csp = df_csp[['code_commune','cadres_pct','ouvriers_pct','employes_pct','artisans_pct',
                  'ratio_cadres_ouvriers']]
print(f"CSP : {len(df_csp)} communes")

# Diplômes (2022)
df_dipl = pd.read_sql(\"\"\"
    SELECT code_commune, nscol15p,
           COALESCE(sup_bac2,0) + COALESCE(sup_bac34,0) + COALESCE(sup_bac5,0) AS bac_plus,
           COALESCE(sans_diplome,0) AS sans_diplome
    FROM silver.diplomes WHERE annee = 2022
\"\"\", engine)
df_dipl['pct_bac_plus']     = (df_dipl['bac_plus']     / df_dipl['nscol15p'] * 100).round(3)
df_dipl['pct_sans_diplome'] = (df_dipl['sans_diplome'] / df_dipl['nscol15p'] * 100).round(3)
df_dipl = df_dipl[['code_commune','pct_bac_plus','pct_sans_diplome']]
print(f"Diplômes : {len(df_dipl)} communes")

# Insécurité (département) — agrégation moyenne par département × année
df_insec = pd.read_sql(\"\"\"
    SELECT code_dep, annee,
           SUM(taux_pour_mille) AS taux_crimes_mille
    FROM silver.insecurite
    GROUP BY code_dep, annee
\"\"\", engine)
print(f"Insécurité : {len(df_insec)} lignes")

# Immigration (département)
df_imm = pd.read_sql(\"\"\"
    SELECT code_dep, annee, pct_immigres
    FROM silver.immigration
\"\"\", engine)
print(f"Immigration : {len(df_imm)} lignes")""")

# ============================================================
md("## 5. Jointure et construction du Gold")

code("""def find_closest_year(target, available_years):
    \"\"\"Retourne l'année disponible la plus proche.\"\"\"
    if not available_years:
        return None
    return min(available_years, key=lambda y: abs(y - target))

def join_by_closest_year(df_main, df_feat, join_keys, feat_cols, year_col='annee'):
    \"\"\"Jointure sur l'année la plus proche disponible dans df_feat.\"\"\"
    available = sorted(df_feat[year_col].unique())
    if not len(available):
        for c in feat_cols:
            df_main[c] = np.nan
        return df_main

    result_rows = []
    for elec_year in df_main['annee'].unique():
        closest = find_closest_year(elec_year, available)
        df_year = df_feat[df_feat[year_col] == closest][join_keys + feat_cols].copy()
        df_main_year = df_main[df_main['annee'] == elec_year].copy()
        merged = df_main_year.merge(df_year, on=join_keys, how='left', suffixes=('', '_feat'))
        result_rows.append(merged)

    return pd.concat(result_rows, ignore_index=True)

# Base : élections pivotées
df_gold = df_pivot.copy()

# Référentiel (libellé, département)
df_gold = df_gold.merge(df_ref, on='code_commune', how='left')

# Population historique (année census la plus proche)
pop_feat_cols = ['population', 'nb_naissances', 'nb_deces']
df_gold = join_by_closest_year(df_gold, df_pop, ['code_commune'], pop_feat_cols)

# Solde naturel et taux
df_gold['solde_naturel'] = (df_gold['nb_naissances'].fillna(0) - df_gold['nb_deces'].fillna(0)).astype('Int64')
df_gold['taux_natalite'] = (df_gold['nb_naissances'] / df_gold['population'] * 1000).round(3)
df_gold['taux_mortalite'] = (df_gold['nb_deces'] / df_gold['population'] * 1000).round(3)

# Revenus IRCOM (même année que l'élection)
df_gold = join_by_closest_year(df_gold, df_rev, ['code_commune'],
                                ['revenu_moyen_par_foyer', 'taux_imposition'])

# Emploi (année census la plus proche)
df_gold = join_by_closest_year(df_gold, df_emp, ['code_commune'], ['taux_chomage'])

# CSP (statique 2022, répliqué)
df_gold = df_gold.merge(df_csp, on='code_commune', how='left')

# Diplômes (statique 2022, répliqué)
df_gold = df_gold.merge(df_dipl, on='code_commune', how='left')

# Insécurité (par département, année la plus proche)
df_gold['code_dep_clean'] = df_gold['code_dep'].astype(str).str.strip()
df_insec['code_dep'] = df_insec['code_dep'].astype(str).str.strip()
df_gold = join_by_closest_year(df_gold, df_insec.rename(columns={'code_dep': 'code_dep_clean'}),
                                ['code_dep_clean'], ['taux_crimes_mille'])
df_gold = df_gold.drop(columns=['code_dep_clean'], errors='ignore')

# Immigration (par département, année la plus proche)
df_gold['code_dep_clean'] = df_gold['code_dep'].astype(str).str.strip()
df_imm['code_dep'] = df_imm['code_dep'].astype(str).str.strip()
df_gold = join_by_closest_year(df_gold, df_imm.rename(columns={'code_dep': 'code_dep_clean'}),
                                ['code_dep_clean'], ['pct_immigres'])
df_gold = df_gold.drop(columns=['code_dep_clean'], errors='ignore')

# Features géographiques
df_gold['is_paris'] = df_gold['code_commune'].astype(str).str.strip().str.startswith('751')
df_gold['is_93'] = df_gold['code_dep'].astype(str).str.strip() == '93'

print(f"Gold shape : {df_gold.shape}")
print(f"Colonnes : {df_gold.columns.tolist()}")""")

# ============================================================
md("## 6. Validation et taux de remplissage")

code("""print("Taux de remplissage (% non-null) :")
fill_rate = (df_gold.notna().sum() / len(df_gold) * 100).round(1)
for col, rate in fill_rate.items():
    flag = " ⚠️" if rate < 90 else ""
    print(f"  {col:30s} {rate:5.1f}%{flag}")

print(f"\\nNombre de communes : {df_gold['code_commune'].nunique()}")
print(f"Nombre de lignes : {len(df_gold)}")""")

# ============================================================
md("## 7. Insertion dans gold.features_communes")

code("""gold_cols = [
    'code_commune', 'annee', 'libelle', 'code_dep',
    'pct_gauche', 'pct_centre', 'pct_droite', 'pct_extremedroite', 'pct_divers',
    'bloc_dominant',
    'population', 'nb_naissances', 'nb_deces', 'solde_naturel',
    'taux_natalite', 'taux_mortalite',
    'revenu_moyen_par_foyer', 'taux_imposition',
    'taux_chomage',
    'cadres_pct', 'ouvriers_pct', 'employes_pct', 'artisans_pct', 'ratio_cadres_ouvriers',
    'pct_bac_plus', 'pct_sans_diplome',
    'taux_crimes_mille', 'pct_immigres',
    'is_paris', 'is_93',
]

df_insert = df_gold[[c for c in gold_cols if c in df_gold.columns]].copy()

for c in gold_cols:
    if c not in df_insert.columns:
        df_insert[c] = np.nan
        print(f"WARN: {c} absent, mis à NaN")

df_insert['annee'] = df_insert['annee'].astype('Int16')
for col in ['population', 'nb_naissances', 'nb_deces', 'solde_naturel']:
    if col in df_insert.columns:
        df_insert[col] = df_insert[col].astype('Int64')

print(f"Lignes à insérer : {len(df_insert)}")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE gold.features_communes"))

df_insert.to_sql('features_communes', engine, schema='gold', if_exists='append',
                 index=False, method='multi', chunksize=1000)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM gold.features_communes")).scalar()
    dist = conn.execute(text(\"\"\"
        SELECT annee, bloc_dominant, COUNT(*) AS n
        FROM gold.features_communes
        GROUP BY annee, bloc_dominant
        ORDER BY annee, bloc_dominant
    \"\"\")).fetchall()

print(f"\\ngold.features_communes : {n} lignes")
print("\\nDistribution blocs dominants par année :")
for row in dist:
    print(f"  {row[0]} | {row[1]:15s} | {row[2]} communes")""")

# ============================================================
md("## 8. Validation finale")

code("""df_val = pd.read_sql(\"\"\"
    SELECT annee,
           COUNT(*) AS nb_communes,
           ROUND(AVG(pct_gauche)::numeric, 1)           AS moy_gauche,
           ROUND(AVG(pct_centre)::numeric, 1)           AS moy_centre,
           ROUND(AVG(pct_droite)::numeric, 1)           AS moy_droite,
           ROUND(AVG(pct_extremedroite)::numeric, 1)    AS moy_xd,
           ROUND(AVG(revenu_moyen_par_foyer)::numeric, 0) AS moy_revenu,
           ROUND(AVG(taux_chomage)::numeric, 1)         AS moy_chomage,
           ROUND(AVG(cadres_pct)::numeric, 1)           AS moy_cadres,
           ROUND(AVG(pct_bac_plus)::numeric, 1)         AS moy_bac_plus
    FROM gold.features_communes
    GROUP BY annee
    ORDER BY annee
\"\"\", engine)

print("=" * 80)
print("VALIDATION GOLD LAYER")
print("=" * 80)
print(df_val.to_string(index=False))
print("\\nFeature engineering terminé !")""")

# ============================================================
# Build notebook
# ============================================================
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"}
    },
    "cells": cells
}

for cell in notebook["cells"]:
    if cell["source"] and cell["source"][-1].endswith("\n"):
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "notebooks", "05_feature_engineering.ipynb")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook écrit : {output_path}")
print(f"Nombre de cellules : {len(cells)}")
