-- =============================================================================
-- MSPR-813 - Electio-Analytics
-- France Layer Schema - PostgreSQL 15
-- Architecture Medallion : Bronze -> Silver France -> Gold France
-- Périmètre : France métropolitaine (~35 000 communes, dép. 01-95 + 2A/2B)
-- Migration parallèle : schémas silver_france et gold_france (silver/gold conservés)
-- =============================================================================

-- =============================================================================
-- SCHEMA silver_france
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS silver_france;

-- =============================================================================
-- TABLE : referentiel_communes
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.referentiel_communes (
    code_insee      CHAR(5)      NOT NULL,
    libelle         VARCHAR(100) NOT NULL,
    code_dep        CHAR(3)      NOT NULL,
    code_reg        CHAR(2),
    statut          VARCHAR(50),
    arr             CHAR(5),
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_referentiel_communes PRIMARY KEY (code_insee)
);

COMMENT ON TABLE silver_france.referentiel_communes IS
    'Référentiel COG 2024 — France métropolitaine (~35 000 communes, dép. 01-95 + 2A/2B)';

-- =============================================================================
-- TABLE : elections
-- Note : volumétrie ~365M lignes — index critiques pour les performances
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.elections (
    id              BIGSERIAL    NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    id_election     VARCHAR(50)  NOT NULL,
    annee           SMALLINT     NOT NULL,
    type_election   VARCHAR(30),
    tour            SMALLINT,
    nuance_liste    VARCHAR(20),
    nom_liste       TEXT,
    nom_candidat    VARCHAR(200),
    prenom_candidat VARCHAR(100),
    sexe            CHAR(1),
    nb_voix         INTEGER,
    pct_voix_ins    NUMERIC(6,3),
    pct_voix_exp    NUMERIC(6,3),
    inscrits        INTEGER,
    votants         INTEGER,
    exprimes        INTEGER,
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_elections PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_fr_elections_commune_annee
    ON silver_france.elections (code_commune, annee);
CREATE INDEX IF NOT EXISTS idx_fr_elections_id_election
    ON silver_france.elections (id_election);
CREATE INDEX IF NOT EXISTS idx_fr_elections_annee
    ON silver_france.elections (annee);
CREATE INDEX IF NOT EXISTS idx_fr_elections_type_tour
    ON silver_france.elections (type_election, tour);

COMMENT ON TABLE silver_france.elections IS
    'Résultats électoraux agrégés 1999-2024 — France métropolitaine (~365M lignes)';

-- =============================================================================
-- TABLE : naissances
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.naissances (
    id              SERIAL       NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    annee           SMALLINT     NOT NULL,
    nb_naissances   INTEGER,
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_naissances PRIMARY KEY (id),
    CONSTRAINT uq_fr_naissances UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_naissances_commune_annee
    ON silver_france.naissances (code_commune, annee);

COMMENT ON TABLE silver_france.naissances IS
    'Naissances par commune 2008-2024 — France métropolitaine';

-- =============================================================================
-- TABLE : deces
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.deces (
    id              SERIAL       NOT NULL,
    code_commune    CHAR(5)      NOT NULL,
    annee           SMALLINT     NOT NULL,
    nb_deces        INTEGER,
    created_at      TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_deces PRIMARY KEY (id),
    CONSTRAINT uq_fr_deces UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_deces_commune_annee
    ON silver_france.deces (code_commune, annee);

COMMENT ON TABLE silver_france.deces IS
    'Décès par commune 2008-2024 — France métropolitaine';

-- =============================================================================
-- TABLE : revenus
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.revenus (
    id                      SERIAL       NOT NULL,
    code_commune            CHAR(5)      NOT NULL,
    annee                   SMALLINT     NOT NULL,
    mediane_revenu_disp     NUMERIC(10,2),
    q1_revenu_disp          NUMERIC(10,2),
    q9_revenu_disp          NUMERIC(10,2),
    gini                    NUMERIC(6,4),
    taux_pauvrete           NUMERIC(6,3),
    mediane_revenu_dec      NUMERIC(10,2),
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_revenus PRIMARY KEY (id),
    CONSTRAINT uq_fr_revenus UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_revenus_commune_annee
    ON silver_france.revenus (code_commune, annee);

COMMENT ON TABLE silver_france.revenus IS
    'Revenus et inégalités par commune — France métropolitaine';

-- =============================================================================
-- TABLE : csp
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.csp (
    id                          SERIAL       NOT NULL,
    code_commune                CHAR(5)      NOT NULL,
    annee                       SMALLINT     NOT NULL DEFAULT 2022,
    agriculteurs_emploi         NUMERIC(12,4),
    artisans_emploi             NUMERIC(12,4),
    cadres_emploi               NUMERIC(12,4),
    prof_interm_emploi          NUMERIC(12,4),
    employes_emploi             NUMERIC(12,4),
    ouvriers_emploi             NUMERIC(12,4),
    agriculteurs_chomeurs       NUMERIC(12,4),
    artisans_chomeurs           NUMERIC(12,4),
    cadres_chomeurs             NUMERIC(12,4),
    prof_interm_chomeurs        NUMERIC(12,4),
    employes_chomeurs           NUMERIC(12,4),
    ouvriers_chomeurs           NUMERIC(12,4),
    created_at                  TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_csp PRIMARY KEY (id),
    CONSTRAINT uq_fr_csp UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_csp_commune
    ON silver_france.csp (code_commune);

COMMENT ON TABLE silver_france.csp IS
    'CSP actifs 25-54 ans par commune, RP 2022 — France métropolitaine';

-- =============================================================================
-- TABLE : diplomes
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver_france.diplomes (
    id                      SERIAL       NOT NULL,
    code_commune            CHAR(5)      NOT NULL,
    annee                   SMALLINT     NOT NULL DEFAULT 2022,
    nscol15p                NUMERIC(12,4),
    sans_diplome            NUMERIC(12,4),
    bepc_brevet             NUMERIC(12,4),
    cap_bep                 NUMERIC(12,4),
    bac                     NUMERIC(12,4),
    sup_bac2                NUMERIC(12,4),
    sup_bac34               NUMERIC(12,4),
    sup_bac5                NUMERIC(12,4),
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_diplomes PRIMARY KEY (id),
    CONSTRAINT uq_fr_diplomes UNIQUE (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_diplomes_commune
    ON silver_france.diplomes (code_commune);

COMMENT ON TABLE silver_france.diplomes IS
    'Diplômes et formation par commune, RP 2022 — France métropolitaine';

-- =============================================================================
-- SCHEMA gold_france
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS gold_france;

-- =============================================================================
-- TABLE : features_communes
-- Enrichie avec : typologie_territoire (urbain / periurbain / rural)
-- Calculée depuis densité de population (population / superficie_km2)
--   >= 1500 hab/km2  → urbain
--   >= 50   hab/km2  → periurbain
--   <  50   hab/km2  → rural
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold_france.features_communes (
    code_commune            CHAR(5)      NOT NULL,
    libelle                 VARCHAR(100),
    code_dep                CHAR(3),
    annee                   SMALLINT     NOT NULL,

    -- Features électorales
    pct_gauche              NUMERIC(6,3),
    pct_centre              NUMERIC(6,3),
    pct_droite              NUMERIC(6,3),
    pct_divers              NUMERIC(6,3),
    bloc_dominant           VARCHAR(20),

    -- Features CSP
    cadres_pct              NUMERIC(6,3),
    ouvriers_pct            NUMERIC(6,3),
    employes_pct            NUMERIC(6,3),
    artisans_pct            NUMERIC(6,3),

    -- Features diplômes
    pct_bac_plus            NUMERIC(6,3),
    pct_sans_diplome        NUMERIC(6,3),

    -- Features démographiques
    nb_naissances           INTEGER,
    nb_deces                INTEGER,
    solde_naturel           INTEGER,

    -- Features revenus
    mediane_revenu_disp     NUMERIC(10,2),
    gini                    NUMERIC(6,4),
    taux_pauvrete           NUMERIC(6,3),

    -- Feature territoire (nouveau vs gold Petite Couronne)
    typologie_territoire    VARCHAR(20),   -- 'urbain', 'periurbain', 'rural'

    -- Métadonnées
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_features PRIMARY KEY (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_features_commune
    ON gold_france.features_communes (code_commune);
CREATE INDEX IF NOT EXISTS idx_fr_features_annee
    ON gold_france.features_communes (annee);
CREATE INDEX IF NOT EXISTS idx_fr_features_dep
    ON gold_france.features_communes (code_dep);
CREATE INDEX IF NOT EXISTS idx_fr_features_bloc
    ON gold_france.features_communes (bloc_dominant);
CREATE INDEX IF NOT EXISTS idx_fr_features_typo
    ON gold_france.features_communes (typologie_territoire);

COMMENT ON TABLE gold_france.features_communes IS
    'Features ML par commune et par année électorale — France métropolitaine (~150k lignes)';
COMMENT ON COLUMN gold_france.features_communes.typologie_territoire IS
    'Typologie territoire calculée depuis densité : urbain (>=1500 hab/km2), periurbain (>=50), rural (<50)';

-- =============================================================================
-- TABLE : predictions_2022
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold_france.predictions_2022 (
    code_commune            CHAR(5)      NOT NULL,
    libelle                 VARCHAR(100),
    code_dep                CHAR(3),
    annee                   SMALLINT     NOT NULL,
    bloc_predit             VARCHAR(20)  NOT NULL,
    prob_gauche             NUMERIC(6,4),
    prob_centre             NUMERIC(6,4),
    prob_droite             NUMERIC(6,4),
    modele                  VARCHAR(30),
    typologie_territoire    VARCHAR(20),
    created_at              TIMESTAMP    DEFAULT NOW(),
    CONSTRAINT pk_fr_predictions PRIMARY KEY (code_commune, annee)
);

CREATE INDEX IF NOT EXISTS idx_fr_pred_commune
    ON gold_france.predictions_2022 (code_commune);
CREATE INDEX IF NOT EXISTS idx_fr_pred_annee
    ON gold_france.predictions_2022 (annee);
CREATE INDEX IF NOT EXISTS idx_fr_pred_dep
    ON gold_france.predictions_2022 (code_dep);
CREATE INDEX IF NOT EXISTS idx_fr_pred_bloc
    ON gold_france.predictions_2022 (bloc_predit);
CREATE INDEX IF NOT EXISTS idx_fr_pred_typo
    ON gold_france.predictions_2022 (typologie_territoire);

COMMENT ON TABLE gold_france.predictions_2022 IS
    'Predictions bloc dominant 2022 par commune — France metropolitaine (~34 783 communes)';

-- =============================================================================
-- Validation finale
-- =============================================================================
DO $$
DECLARE
    nb_tables_silver INT;
    nb_tables_gold   INT;
BEGIN
    SELECT COUNT(*) INTO nb_tables_silver
    FROM information_schema.tables
    WHERE table_schema = 'silver_france';

    SELECT COUNT(*) INTO nb_tables_gold
    FROM information_schema.tables
    WHERE table_schema = 'gold_france';

    RAISE NOTICE '=== init_db_france.sql terminé ===';
    RAISE NOTICE 'silver_france : % tables créées', nb_tables_silver;
    RAISE NOTICE 'gold_france   : % tables créées', nb_tables_gold;
    RAISE NOTICE 'Pret pour ETL Bronze -> silver_france (notebook france/01_etl_bronze_to_postgres.ipynb)';
END $$;

-- =============================================================================
-- Fin du script
-- =============================================================================
