-- =============================================================================
-- MSPR-813 - Electio-Analytics
-- Silver Layer Schema - PostgreSQL 15
-- Architecture Medallion : Bronze -> Silver (ce fichier) -> Gold
-- =============================================================================

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS unaccent;

-- =============================================================================
-- SCHEMA silver
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS silver;

-- =============================================================================
-- TABLE : referentiel_communes
-- Source : data/bronze/referentiels_cog/referentiel_communes_2024.csv
-- Clé : code_insee (5 chars, paddé zéros)
-- Périmètre : 144 communes Petite Couronne (75, 92, 93, 94)
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.referentiel_communes (
    code_insee      CHAR(5)      NOT NULL,
    libelle         VARCHAR(100) NOT NULL,
    code_dep        CHAR(3)      NOT NULL,
    code_reg        CHAR(2),
    statut          VARCHAR(50),
    arr             CHAR(5),
    -- Métadonnées
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_referentiel_communes PRIMARY KEY (code_insee)
);

COMMENT ON TABLE silver.referentiel_communes IS
    'Référentiel COG 2024 des communes de la Petite Couronne (dép. 75, 92, 93, 94)';

-- =============================================================================
-- TABLE : elections
-- Source : data/bronze/elections_agregees_1999_2024.csv
-- Clé : (code_commune, id_election, nuance_liste) ou (code_commune, id_election, nom_candidat)
-- Note : colonne annee extraite via regex (\d{4}) depuis id_election
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.elections (
    id              BIGSERIAL    NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    id_election     VARCHAR(50)  NOT NULL,  -- ex: '2022_pres_t1'
    annee           SMALLINT     NOT NULL,  -- extrait de id_election
    type_election   VARCHAR(30),            -- ex: 'pres', 'leg', 'mun'
    tour            SMALLINT,               -- 1 ou 2
    nuance_liste    VARCHAR(20),
    nom_liste       VARCHAR(200),
    nom_candidat    VARCHAR(200),
    prenom_candidat VARCHAR(100),
    sexe            CHAR(1),                -- M/F, ~80% NULL normal
    nb_voix         INTEGER,
    pct_voix_ins    NUMERIC(6,3),
    pct_voix_exp    NUMERIC(6,3),
    inscrits        INTEGER,
    votants         INTEGER,
    exprimes        INTEGER,
    -- Métadonnées
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_elections PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_elections_commune_annee
    ON silver.elections (code_commune, annee);
CREATE INDEX IF NOT EXISTS idx_elections_id_election
    ON silver.elections (id_election);
CREATE INDEX IF NOT EXISTS idx_elections_annee
    ON silver.elections (annee);

COMMENT ON TABLE silver.elections IS
    'Résultats électoraux agrégés 1999-2024, filtrés Petite Couronne';

-- =============================================================================
-- TABLE : naissances
-- Source : data/bronze/naissances_2008_2024/DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv
-- Clé : (code_commune, annee)
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.naissances (
    id              SERIAL       NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    annee           SMALLINT     NOT NULL,
    nb_naissances   INTEGER,
    -- Métadonnées
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_naissances PRIMARY KEY (id),
    CONSTRAINT uq_naissances UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_naissances_commune_annee
    ON silver.naissances (code_commune, annee);

COMMENT ON TABLE silver.naissances IS
    'Naissances par commune 2008-2024, Petite Couronne';

-- =============================================================================
-- TABLE : deces
-- Source : data/bronze/deces_2008_2024/DS_ETAT_CIVIL_DECES_COMMUNES_data.csv
-- Clé : (code_commune, annee)
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.deces (
    id              SERIAL       NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    annee           SMALLINT     NOT NULL,
    nb_deces        INTEGER,
    -- Métadonnées
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_deces PRIMARY KEY (id),
    CONSTRAINT uq_deces UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_deces_commune_annee
    ON silver.deces (code_commune, annee);

COMMENT ON TABLE silver.deces IS
    'Décès par commune 2008-2024, Petite Couronne';

-- =============================================================================
-- TABLE : revenus
-- Source : data/bronze/revenus_commune.csv
-- Clé : (code_commune, annee)
-- Colonnes retenues : médiane revenu disponible, gini, taux pauvreté
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.revenus (
    id                      SERIAL       NOT NULL,
    code_commune            CHAR(5)      NOT NULL,
    annee                   SMALLINT     NOT NULL,
    -- Revenu disponible
    mediane_revenu_disp     NUMERIC(10,2),  -- [DISP] D5 : médiane
    q1_revenu_disp          NUMERIC(10,2),  -- [DISP] D1
    q9_revenu_disp          NUMERIC(10,2),  -- [DISP] D9
    gini                    NUMERIC(6,4),   -- [DISP] Gini
    taux_pauvrete           NUMERIC(6,3),   -- [DISP] Taux pauvreté 60%
    -- Revenu déclaré
    mediane_revenu_dec      NUMERIC(10,2),  -- [DEC] médiane
    -- Métadonnées
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_revenus PRIMARY KEY (id),
    CONSTRAINT uq_revenus UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_revenus_commune_annee
    ON silver.revenus (code_commune, annee);

COMMENT ON TABLE silver.revenus IS
    'Revenus et inégalités par commune, Petite Couronne';

-- =============================================================================
-- TABLE : csp
-- Source : data/bronze/csp_actifs_2554/pop-act2554-csp-cd-6822.xlsx
-- Sheet : COM_2022, skiprows=14 (header row 14), données row 16+
-- Note : code_insee = DR (2 chars) + CR (3 chars)
-- Une seule année disponible : 2022
-- CSP : rec1=Agriculteurs, rec2=Artisans/commerçants, rec3=Cadres,
--       rec4=Prof. intermédiaires, rec5=Employés, rec6=Ouvriers
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.csp (
    id                          SERIAL       NOT NULL,
    code_commune                CHAR(5)      NOT NULL,
    annee                       SMALLINT     NOT NULL DEFAULT 2022,
    -- Actifs ayant un emploi
    agriculteurs_emploi         NUMERIC(12,4),
    artisans_emploi             NUMERIC(12,4),
    cadres_emploi               NUMERIC(12,4),
    prof_interm_emploi          NUMERIC(12,4),
    employes_emploi             NUMERIC(12,4),
    ouvriers_emploi             NUMERIC(12,4),
    -- Chômeurs (ayant déjà eu un emploi)
    agriculteurs_chomeurs       NUMERIC(12,4),
    artisans_chomeurs           NUMERIC(12,4),
    cadres_chomeurs             NUMERIC(12,4),
    prof_interm_chomeurs        NUMERIC(12,4),
    employes_chomeurs           NUMERIC(12,4),
    ouvriers_chomeurs           NUMERIC(12,4),
    -- Métadonnées
    created_at                  TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_csp PRIMARY KEY (id),
    CONSTRAINT uq_csp UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_csp_commune
    ON silver.csp (code_commune);

COMMENT ON TABLE silver.csp IS
    'CSP actifs 25-54 ans par commune, RP 2022, Petite Couronne';

-- =============================================================================
-- TABLE : diplomes
-- Source : data/bronze/diplomes_formation_2022/base-cc-diplomes-formation-2022.xlsx
-- Sheet : COM_2022, skiprows=5 (header = row 5 = codes techniques CODGEO...)
-- Clé : code_commune
-- Colonnes retenues : niveaux de diplôme pop 15 ans et + non scolarisée
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.diplomes (
    id                      SERIAL       NOT NULL,
    code_commune            CHAR(5)      NOT NULL,
    annee                   SMALLINT     NOT NULL DEFAULT 2022,
    -- Population 15+ non scolarisée (total)
    nscol15p                NUMERIC(12,4),  -- P22_NSCOL15P
    -- Niveaux de diplôme
    sans_diplome            NUMERIC(12,4),  -- P22_NSCOL15P_DIPLMIN
    bepc_brevet             NUMERIC(12,4),  -- P22_NSCOL15P_BEPC
    cap_bep                 NUMERIC(12,4),  -- P22_NSCOL15P_CAPBEP
    bac                     NUMERIC(12,4),  -- P22_NSCOL15P_BAC
    sup_bac2                NUMERIC(12,4),  -- P22_NSCOL15P_SUP2
    sup_bac34               NUMERIC(12,4),  -- P22_NSCOL15P_SUP34
    sup_bac5                NUMERIC(12,4),  -- P22_NSCOL15P_SUP5
    -- Métadonnées
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_diplomes PRIMARY KEY (id),
    CONSTRAINT uq_diplomes UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_diplomes_commune
    ON silver.diplomes (code_commune);

COMMENT ON TABLE silver.diplomes IS
    'Diplômes et formation par commune, RP 2022, Petite Couronne';

-- =============================================================================
-- VUE : v_communes_petite_couronne
-- Jointure referentiel + agrégats électoraux synthétiques
-- =============================================================================
CREATE OR REPLACE VIEW silver.v_communes_petite_couronne AS
SELECT
    r.code_insee,
    r.libelle,
    r.code_dep,
    CASE r.code_dep
        WHEN '75' THEN 'Paris'
        WHEN '092' THEN 'Hauts-de-Seine'
        WHEN '093' THEN 'Seine-Saint-Denis'
        WHEN '094' THEN 'Val-de-Marne'
        ELSE r.code_dep
    END AS nom_departement
FROM silver.referentiel_communes r;

COMMENT ON VIEW silver.v_communes_petite_couronne IS
    '144 communes de la Petite Couronne avec libellé département';

-- =============================================================================
-- Fin du script
-- =============================================================================
