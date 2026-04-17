"""
setup_metabase.py
-----------------
Cree les 20 questions et 6 dashboards Metabase definis dans docs/METABASE_QUESTIONS.md.

Usage :
    python3 scripts/setup_metabase.py

Le script demande le mot de passe au lancement (jamais stocke).
Il est idempotent : une question ou un dashboard du meme nom ne sera pas recree.

Prerequis :
    pip install requests
    Metabase accessible sur http://localhost:3000
"""

import getpass
import sys
import requests

METABASE_URL = "http://localhost:3000"
EMAIL = "lucas.steichen@ecoles-epsi.net"

# Tables cibles
TABLE_FEATURES    = "gold_france.features_communes"
TABLE_PREDICTIONS = "gold_france.predictions_2022"


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

def get_session_token(email, password):
    resp = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": email, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"Erreur authentification : {resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json().get("id")
    print(f"Authentifie : {email}")
    return token


def headers(token):
    return {"X-Metabase-Session": token, "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Helpers API
# ---------------------------------------------------------------------------

def get_database_id(token, db_name="mspr813"):
    resp = requests.get(f"{METABASE_URL}/api/database", headers=headers(token), timeout=10)
    resp.raise_for_status()
    for db in resp.json().get("data", []):
        if db["name"] == db_name:
            print(f"Datasource trouvee : id={db['id']} name={db['name']}")
            return db["id"]
    print(f"Datasource '{db_name}' introuvable. Datasources disponibles :")
    for db in resp.json().get("data", []):
        print(f"  id={db['id']} name={db['name']}")
    sys.exit(1)


def get_table_id(token, database_id, schema, table_name):
    resp = requests.get(
        f"{METABASE_URL}/api/database/{database_id}/metadata",
        headers=headers(token),
        timeout=30,
    )
    resp.raise_for_status()
    for table in resp.json().get("tables", []):
        if table.get("schema") == schema and table.get("name") == table_name:
            return table["id"]
    print(f"Table {schema}.{table_name} introuvable.")
    return None


def get_field_id(token, table_id, field_name):
    resp = requests.get(
        f"{METABASE_URL}/api/table/{table_id}/query_metadata",
        headers=headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    for field in resp.json().get("fields", []):
        if field["name"] == field_name:
            return field["id"]
    return None


def existing_cards(token):
    resp = requests.get(f"{METABASE_URL}/api/card", headers=headers(token), timeout=10)
    resp.raise_for_status()
    return {c["name"]: c["id"] for c in resp.json()}


def existing_dashboards(token):
    resp = requests.get(f"{METABASE_URL}/api/dashboard", headers=headers(token), timeout=10)
    resp.raise_for_status()
    return {d["name"]: d["id"] for d in resp.json()}


def create_card(token, payload, existing):
    name = payload["name"]
    if name in existing:
        print(f"  SKIP (existe) : {name}")
        return existing[name]
    resp = requests.post(
        f"{METABASE_URL}/api/card",
        headers=headers(token),
        json=payload,
        timeout=30,
    )
    if resp.status_code in (200, 202):
        card_id = resp.json()["id"]
        print(f"  OK : {name} (id={card_id})")
        return card_id
    else:
        print(f"  ERREUR {resp.status_code} : {name} — {resp.text[:200]}")
        return None


def create_dashboard(token, name, existing):
    if name in existing:
        print(f"  SKIP (existe) : {name} (id={existing[name]})")
        return existing[name]
    resp = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers=headers(token),
        json={"name": name},
        timeout=10,
    )
    resp.raise_for_status()
    dash_id = resp.json()["id"]
    print(f"  OK : {name} (id={dash_id})")
    return dash_id


def get_dashboard_dashcards(token, dashboard_id):
    """Retourne la liste complete des dashcards (id, card_id) d'un dashboard."""
    resp = requests.get(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        headers=headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("dashcards", [])


def clear_dashboard(token, dashboard_id):
    """Supprime toutes les dashcards d'un dashboard via PUT avec liste vide."""
    resp = requests.put(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        headers=headers(token),
        json={"dashcards": []},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"    ERREUR vidage dashboard {dashboard_id} : {resp.text[:150]}")


def set_dashboard_cards(token, dashboard_id, card_specs):
    """
    Remplace toutes les dashcards d'un dashboard en une seule requete PUT.
    card_specs : liste de dicts {card_id, col, row, size_x, size_y}
    """
    dashcards = [
        {
            "id": -(i + 1),
            "card_id": spec["card_id"],
            "col": spec["col"],
            "row": spec["row"],
            "size_x": spec.get("size_x", 12),
            "size_y": spec.get("size_y", 8),
            "parameter_mappings": [],
            "visualization_settings": {},
        }
        for i, spec in enumerate(card_specs)
    ]
    resp = requests.put(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        headers=headers(token),
        json={"dashcards": dashcards},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"    ERREUR set dashcards dashboard {dashboard_id} : {resp.text[:200]}")
        return False
    return True


# ---------------------------------------------------------------------------
# Definitions des questions
# ---------------------------------------------------------------------------

def make_sql_card(database_id, name, sql, display="table"):
    """Construit un payload card de type native SQL."""
    return {
        "name": name,
        "dataset_query": {
            "type": "native",
            "database": database_id,
            "native": {"query": sql},
        },
        "display": display,
        "visualization_settings": {},
    }


def build_all_cards(database_id, fields_fc, fields_pred):
    """
    Construit les payloads des 20 questions, toutes en SQL natif.
    Chaque requete retourne un tableau simple (categorie + valeur numerique)
    pour que Metabase puisse afficher le graphique sans configuration manuelle.
    """
    cards = []

    # ------------------------------------------------------------------
    # Q1 — Evolution temporelle des scores moyens par bloc (2002-2022)
    # Ligne avec annee en X et pct moyen en Y, une serie par bloc.
    # Format : annee | bloc | pct_moyen
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q1 - Evolution du score moyen par bloc (2002-2022)",
        sql="""
SELECT annee::text AS annee, 'Gauche'  AS bloc, ROUND(AVG(pct_gauche)::numeric, 1) AS pct_moyen
FROM gold_france.features_communes
GROUP BY annee
UNION ALL
SELECT annee::text, 'Centre'  AS bloc, ROUND(AVG(pct_centre)::numeric, 1) AS pct_moyen
FROM gold_france.features_communes
GROUP BY annee
UNION ALL
SELECT annee::text, 'Droite'  AS bloc, ROUND(AVG(pct_droite)::numeric, 1) AS pct_moyen
FROM gold_france.features_communes
GROUP BY annee
ORDER BY annee, bloc;
""",
        display="line",
    ))

    # ------------------------------------------------------------------
    # Q2 — Nombre de communes par bloc dominant et par annee
    # Bar chart empile : annee en X, nb_communes en Y, serie = bloc
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q2 - Communes par bloc dominant et par annee",
        sql="""
SELECT
    annee::text AS annee,
    bloc_dominant AS bloc,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY annee), 1) AS pourcentage
FROM gold_france.features_communes
GROUP BY annee, bloc_dominant
ORDER BY annee, bloc_dominant;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q3 — Repartition des communes par bloc dominant en 2022 (reel)
    # Pie chart : bloc en categorie, nb_communes et pct en valeurs
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q3 - Repartition des communes par bloc dominant en 2022 (reel)",
        sql="""
SELECT
    bloc_dominant AS bloc,
    COUNT(*) AS nb_communes
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY nb_communes DESC;
""",
        display="pie",
    ))

    # ------------------------------------------------------------------
    # Q4 — Profil CSP moyen par bloc dominant en 2022
    # Tableau : bloc en ligne, CSP en colonnes
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q4 - Profil CSP moyen par bloc dominant en 2022",
        sql="""
SELECT
    bloc_dominant AS bloc,
    ROUND(AVG(cadres_pct)::numeric,   1) AS pct_cadres_prof_intellectuelles,
    ROUND(AVG(ouvriers_pct)::numeric, 1) AS pct_ouvriers,
    ROUND(AVG(employes_pct)::numeric, 1) AS pct_employes,
    ROUND(AVG(artisans_pct)::numeric, 1) AS pct_artisans_commercants
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY bloc_dominant;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q5 — Niveau de diplome moyen par bloc dominant en 2022
    # Bar chart : bloc en X, pct bac+ et sans diplome en Y
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q5 - Niveau de diplome par bloc dominant en 2022",
        sql="""
SELECT bloc_dominant AS bloc, '% diplomes bac+' AS indicateur, ROUND(AVG(pct_bac_plus)::numeric, 1) AS pourcentage_habitants
FROM gold_france.features_communes WHERE annee = 2022 GROUP BY bloc_dominant
UNION ALL
SELECT bloc_dominant, '% sans diplome', ROUND(AVG(pct_sans_diplome)::numeric, 1)
FROM gold_france.features_communes WHERE annee = 2022 GROUP BY bloc_dominant
ORDER BY bloc, indicateur;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q6 — Revenu median et taux de pauvrete par bloc dominant en 2022
    # Tableau : les echelles sont trop differentes pour un graphique mixte
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q6 - Revenu et pauvrete par bloc dominant en 2022",
        sql="""
SELECT
    bloc_dominant AS bloc,
    ROUND(AVG(mediane_revenu_disp)::numeric, 0) AS revenu_median_disponible_eur,
    ROUND(AVG(taux_pauvrete)::numeric,       1) AS taux_pauvrete_pct_population,
    ROUND(AVG(gini)::numeric,                3) AS indice_gini_inegalites_0_a_1
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
ORDER BY bloc_dominant;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q7 — Nombre de communes par bloc et par type de territoire en 2022
    # Bar chart groupe : type de territoire en X, nb_communes en Y, serie = bloc
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q7 - Communes par bloc et type de territoire en 2022",
        sql="""
SELECT
    typologie_territoire AS type_territoire,
    bloc_dominant AS bloc,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY typologie_territoire), 1) AS pourcentage_dans_territoire
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY typologie_territoire, bloc_dominant
ORDER BY type_territoire, bloc;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q8 — Profil socio-eco moyen par type de territoire en 2022
    # Tableau de synthese
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q8 - Profil socio-economique par type de territoire en 2022",
        sql="""
SELECT
    typologie_territoire                             AS type_territoire,
    COUNT(*)                                         AS nb_communes,
    ROUND(AVG(pct_bac_plus)::numeric,          1)   AS pct_habitants_diplomes_bac_plus,
    ROUND(AVG(cadres_pct)::numeric,            1)   AS pct_cadres_prof_intellectuelles,
    ROUND(AVG(mediane_revenu_disp)::numeric,   0)   AS revenu_median_disponible_eur,
    ROUND(AVG(taux_pauvrete)::numeric,         1)   AS taux_pauvrete_pct_population
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY typologie_territoire
ORDER BY nb_communes DESC;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q9 — Top 15 departements avec le plus de communes Gauche en 2022
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q9 - Top 15 departements avec le plus de communes Gauche en 2022",
        sql="""
SELECT
    code_dep AS departement,
    COUNT(*) AS nb_communes_gauche
FROM gold_france.features_communes
WHERE annee = 2022
  AND bloc_dominant = 'Gauche'
GROUP BY code_dep
ORDER BY nb_communes_gauche DESC
LIMIT 15;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q10 — Top 15 departements avec le plus de communes Droite en 2022
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q10 - Top 15 departements avec le plus de communes Droite en 2022",
        sql="""
SELECT
    code_dep AS departement,
    COUNT(*) AS nb_communes_droite
FROM gold_france.features_communes
WHERE annee = 2022
  AND bloc_dominant = 'Droite'
GROUP BY code_dep
ORDER BY nb_communes_droite DESC
LIMIT 15;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q11 — Repartition des communes predites par bloc en 2022
    # Pie chart : resultat du modele ML
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q11 - Repartition des predictions 2022 par bloc (modele ML)",
        sql="""
SELECT
    bloc_predit AS bloc,
    COUNT(*) AS nb_communes
FROM gold_france.predictions_2022
GROUP BY bloc_predit
ORDER BY nb_communes DESC;
""",
        display="pie",
    ))

    # ------------------------------------------------------------------
    # Q12 — Predictions 2022 par bloc et par type de territoire
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q12 - Predictions 2022 par bloc et type de territoire",
        sql="""
SELECT
    typologie_territoire AS type_territoire,
    bloc_predit AS bloc,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY typologie_territoire), 1) AS pourcentage_dans_territoire
FROM gold_france.predictions_2022
GROUP BY typologie_territoire, bloc_predit
ORDER BY type_territoire, bloc;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q13 — Probabilite moyenne d'appartenance a chaque bloc (modele ML)
    # Pivot : une ligne par bloc avec la probabilite moyenne
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q13 - Probabilite moyenne par bloc selon le modele ML",
        sql="""
SELECT 'Gauche' AS bloc, ROUND(AVG(prob_gauche) * 100, 1) AS probabilite_moyenne_pct
FROM gold_france.predictions_2022
UNION ALL
SELECT 'Centre' AS bloc, ROUND(AVG(prob_centre) * 100, 1) AS probabilite_moyenne_pct
FROM gold_france.predictions_2022
UNION ALL
SELECT 'Droite' AS bloc, ROUND(AVG(prob_droite) * 100, 1) AS probabilite_moyenne_pct
FROM gold_france.predictions_2022
ORDER BY probabilite_moyenne_pct DESC;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q14 — Probabilite moyenne par bloc et par type de territoire
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q14 - Probabilite moyenne par bloc et type de territoire (ML)",
        sql="""
SELECT
    typologie_territoire                      AS type_territoire,
    ROUND(AVG(prob_gauche) * 100, 1)          AS prob_gauche_pct,
    ROUND(AVG(prob_centre) * 100, 1)          AS prob_centre_pct,
    ROUND(AVG(prob_droite) * 100, 1)          AS prob_droite_pct
FROM gold_france.predictions_2022
GROUP BY typologie_territoire
ORDER BY type_territoire;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q15 — Top 15 departements avec la probabilite Droite la plus elevee
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q15 - Top 15 departements par probabilite Droite moyenne (ML)",
        sql="""
SELECT
    code_dep AS departement,
    ROUND(AVG(prob_droite) * 100, 1) AS probabilite_droite_moyenne_pct
FROM gold_france.predictions_2022
GROUP BY code_dep
ORDER BY probabilite_droite_moyenne_pct DESC
LIMIT 15;
""",
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q16 — Comparaison reel vs predit 2022 : repartition globale
    # Tableau cote a cote reel / predit
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q16 - Comparaison globale reel 2022 vs predit 2022",
        sql="""
SELECT
    r.bloc,
    r.pct AS pourcentage_reel_2022,
    p.pct AS pourcentage_predit_2022,
    r.pct - p.pct AS ecart_reel_moins_predit
FROM (
    SELECT bloc_dominant AS bloc, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct
    FROM gold_france.features_communes WHERE annee=2022 GROUP BY bloc_dominant
) r
JOIN (
    SELECT bloc_predit AS bloc, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct
    FROM gold_france.predictions_2022 GROUP BY bloc_predit
) p ON r.bloc = p.bloc
ORDER BY r.pct DESC;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q17 — Matrice de confusion reel vs predit 2022
    # Tableau : pour chaque bloc reel, combien de communes predites dans chaque bloc
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q17 - Matrice de confusion reel vs predit 2022",
        sql="""
SELECT
    fc.bloc_dominant  AS bloc_reel,
    p.bloc_predit     AS bloc_predit,
    COUNT(*)          AS nb_communes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY fc.bloc_dominant), 1) AS pct_du_bloc_reel
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
    ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
GROUP BY fc.bloc_dominant, p.bloc_predit
ORDER BY fc.bloc_dominant, nb_communes DESC;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q18 — Accuracy globale et par bloc du modele ML
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q18 - Accuracy du modele ML par bloc (reel vs predit 2022)",
        sql="""
SELECT
    fc.bloc_dominant AS bloc_reel,
    COUNT(*)         AS nb_communes_reel,
    SUM(CASE WHEN p.bloc_predit = fc.bloc_dominant THEN 1 ELSE 0 END) AS nb_bien_predites,
    ROUND(
        SUM(CASE WHEN p.bloc_predit = fc.bloc_dominant THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) AS accuracy_pct
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
    ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
GROUP BY fc.bloc_dominant
ORDER BY fc.bloc_dominant;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q19 — Communes mal predites : liste avec reel et predit
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q19 - Communes mal predites par le modele en 2022",
        sql="""
SELECT
    p.code_commune,
    p.libelle,
    p.code_dep,
    p.typologie_territoire AS territoire,
    fc.bloc_dominant       AS bloc_reel,
    p.bloc_predit          AS bloc_predit,
    ROUND(p.prob_gauche * 100, 1) AS prob_gauche_pct,
    ROUND(p.prob_centre * 100, 1) AS prob_centre_pct,
    ROUND(p.prob_droite * 100, 1) AS prob_droite_pct
FROM gold_france.predictions_2022 p
JOIN gold_france.features_communes fc
    ON p.code_commune = fc.code_commune
WHERE fc.annee = 2022
  AND p.bloc_predit <> fc.bloc_dominant
ORDER BY p.code_dep, p.libelle
LIMIT 200;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q20 — Scores electoraux historiques pour les communes rurales de Gauche
    # Contexte : comprendre pourquoi le modele a du mal a predire ces communes
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q20 - Historique electoral des communes rurales de Gauche",
        sql="""
SELECT annee::text AS annee, 'Score Gauche'  AS indicateur, ROUND(AVG(pct_gauche)::numeric, 1) AS score_moyen_pct
FROM gold_france.features_communes WHERE bloc_dominant='Gauche' AND typologie_territoire='rural' GROUP BY annee
UNION ALL
SELECT annee::text, 'Score Centre', ROUND(AVG(pct_centre)::numeric, 1)
FROM gold_france.features_communes WHERE bloc_dominant='Gauche' AND typologie_territoire='rural' GROUP BY annee
UNION ALL
SELECT annee::text, 'Score Droite', ROUND(AVG(pct_droite)::numeric, 1)
FROM gold_france.features_communes WHERE bloc_dominant='Gauche' AND typologie_territoire='rural' GROUP BY annee
ORDER BY annee, indicateur;
""",
        display="line",
    ))

    # ------------------------------------------------------------------
    # Q21 — Bar chart reel vs predit 2022 par bloc (graphique)
    # Pivot pour avoir source en X et une serie par bloc
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q21 - Reel vs predit 2022 par bloc (graphique)",
        sql="""
SELECT
    'Reel 2022' AS source,
    bloc_dominant AS bloc,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage_communes
FROM gold_france.features_communes
WHERE annee = 2022
GROUP BY bloc_dominant
UNION ALL
SELECT
    'Predit 2022',
    bloc_predit,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)
FROM gold_france.predictions_2022
GROUP BY bloc_predit
ORDER BY source DESC, pourcentage_communes DESC;
""",
        display="bar",
    ))

    return cards


# ---------------------------------------------------------------------------
# Recuperation des champs d'une table
# ---------------------------------------------------------------------------

def get_fields(token, table_id):
    resp = requests.get(
        f"{METABASE_URL}/api/table/{table_id}/query_metadata",
        headers=headers(token),
        timeout=30,
    )
    resp.raise_for_status()
    fields = {f["name"]: f["id"] for f in resp.json().get("fields", [])}
    fields["__table_id__"] = table_id
    return fields


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------

DASHBOARD_DEFINITIONS = [
    {
        "name": "Dashboard 1 - Vue nationale",
        "questions": [
            "Q1 - Evolution du score moyen par bloc (2002-2022)",
            "Q2 - Communes par bloc dominant et par annee",
            "Q3 - Repartition des communes par bloc dominant en 2022 (reel)",
        ],
    },
    {
        "name": "Dashboard 2 - Analyse sociodemographique",
        "questions": [
            "Q4 - Profil CSP moyen par bloc dominant en 2022",
            "Q5 - Niveau de diplome par bloc dominant en 2022",
            "Q6 - Revenu et pauvrete par bloc dominant en 2022",
            "Q8 - Profil socio-economique par type de territoire en 2022",
        ],
    },
    {
        "name": "Dashboard 3 - Typologie territoire",
        "questions": [
            "Q7 - Communes par bloc et type de territoire en 2022",
            "Q12 - Predictions 2022 par bloc et type de territoire",
            "Q14 - Probabilite moyenne par bloc et type de territoire (ML)",
        ],
    },
    {
        "name": "Dashboard 4 - Departements cles",
        "questions": [
            "Q9 - Top 15 departements avec le plus de communes Gauche en 2022",
            "Q10 - Top 15 departements avec le plus de communes Droite en 2022",
            "Q15 - Top 15 departements par probabilite Droite moyenne (ML)",
        ],
    },
    {
        "name": "Dashboard 5 - Predictions 2022",
        "questions": [
            "Q11 - Repartition des predictions 2022 par bloc (modele ML)",
            "Q13 - Probabilite moyenne par bloc selon le modele ML",
            "Q14 - Probabilite moyenne par bloc et type de territoire (ML)",
        ],
    },
    {
        "name": "Dashboard 6 - Comparaison reel vs predit 2022",
        "questions": [
            "Q21 - Reel vs predit 2022 par bloc (graphique)",
            "Q16 - Comparaison globale reel 2022 vs predit 2022",
            "Q17 - Matrice de confusion reel vs predit 2022",
            "Q18 - Accuracy du modele ML par bloc (reel vs predit 2022)",
            "Q19 - Communes mal predites par le modele en 2022",
            "Q20 - Historique electoral des communes rurales de Gauche",
        ],
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Setup Metabase — Electio-Analytics ===\n")

    password = getpass.getpass(f"Mot de passe Metabase ({EMAIL}) : ")
    token = get_session_token(EMAIL, password)

    print("\n--- Datasource ---")
    db_id = get_database_id(token, db_name="MSPR 813")

    print("\n--- Questions ---")
    cards_existing = existing_cards(token)
    # Toutes les questions sont en SQL natif, pas besoin des field ids
    card_payloads = build_all_cards(db_id, {}, {})

    card_ids = {}
    for payload in card_payloads:
        card_id = create_card(token, payload, cards_existing)
        if card_id:
            card_ids[payload["name"]] = card_id

    print("\n--- Dashboards ---")
    dashes_existing = existing_dashboards(token)

    all_cards_cache = None

    for dash_def in DASHBOARD_DEFINITIONS:
        dash_id = create_dashboard(token, dash_def["name"], dashes_existing)
        if not dash_id:
            continue

        # Construit la liste des specs pour ce dashboard
        specs = []
        col, row = 0, 0
        for q_name in dash_def["questions"]:
            cid = card_ids.get(q_name)
            if not cid:
                if all_cards_cache is None:
                    all_cards_cache = existing_cards(token)
                cid = all_cards_cache.get(q_name)
            if not cid:
                print(f"    WARN : question '{q_name}' introuvable, non ajoutee au dashboard")
                continue
            specs.append({"card_id": cid, "col": col, "row": row})
            col = (col + 12) % 24
            if col == 0:
                row += 8

        # Remplace toutes les dashcards en une seule requete
        if set_dashboard_cards(token, dash_id, specs):
            for q_name in dash_def["questions"]:
                if card_ids.get(q_name) or (all_cards_cache and all_cards_cache.get(q_name)):
                    print(f"    Ajoutee : {q_name}")

    print("\n--- Termine ---")
    print(f"Metabase : {METABASE_URL}")
    dashes_final = existing_dashboards(token)
    for dash_def in DASHBOARD_DEFINITIONS:
        name = dash_def["name"]
        did = dashes_final.get(name)
        if did:
            print(f"  {name} : {METABASE_URL}/dashboard/{did}")
    print()


if __name__ == "__main__":
    main()
