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

def make_gui_card(database_id, table_id, name, aggregations, breakouts, filters=None, order_by=None, limit=None, display="bar"):
    """Construit un payload card de type query builder (MBQL)."""
    query = {
        "source-table": table_id,
        "aggregation": aggregations,
        "breakout": breakouts,
    }
    if filters:
        query["filter"] = filters
    if order_by:
        query["order-by"] = order_by
    if limit:
        query["limit"] = limit

    return {
        "name": name,
        "dataset_query": {
            "type": "query",
            "database": database_id,
            "query": query,
        },
        "display": display,
        "visualization_settings": {},
    }


def make_sql_card(database_id, name, sql, display="table"):
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
    Construit les payloads des 20 questions.
    fields_fc   : dict field_name -> field_id pour features_communes
    fields_pred : dict field_name -> field_id pour predictions_2022
    """

    def fc(name):
        fid = fields_fc.get(name)
        if fid is None:
            print(f"    WARN : champ '{name}' introuvable dans features_communes")
        return fid

    def pr(name):
        fid = fields_pred.get(name)
        if fid is None:
            print(f"    WARN : champ '{name}' introuvable dans predictions_2022")
        return fid

    tid_fc   = fields_fc["__table_id__"]
    tid_pred = fields_pred["__table_id__"]

    cards = []

    # ------------------------------------------------------------------
    # Q1 — Evolution temporelle des blocs (features_communes)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q1 - Evolution temporelle des blocs",
        aggregations=[
            ["avg", ["field", fc("pct_gauche"),  {}]],
            ["avg", ["field", fc("pct_centre"),  {}]],
            ["avg", ["field", fc("pct_droite"),  {}]],
        ],
        breakouts=[["field", fc("annee"), {}]],
        display="line",
    ))

    # ------------------------------------------------------------------
    # Q2 — Repartition des blocs dominants par annee
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q2 - Repartition blocs dominants par annee",
        aggregations=[["count"]],
        breakouts=[
            ["field", fc("annee"),          {}],
            ["field", fc("bloc_dominant"),  {}],
        ],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q3 — Communes par bloc dominant en 2022
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q3 - Communes par bloc dominant en 2022",
        aggregations=[["count"]],
        breakouts=[["field", fc("bloc_dominant"), {}]],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q4 — CSP par bloc dominant (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q4 - CSP par bloc dominant (2022)",
        aggregations=[
            ["avg", ["field", fc("cadres_pct"),    {}]],
            ["avg", ["field", fc("ouvriers_pct"),  {}]],
            ["avg", ["field", fc("employes_pct"),  {}]],
            ["avg", ["field", fc("artisans_pct"),  {}]],
        ],
        breakouts=[["field", fc("bloc_dominant"), {}]],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q5 — Diplomes par bloc dominant (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q5 - Diplomes par bloc dominant (2022)",
        aggregations=[
            ["avg", ["field", fc("pct_bac_plus"),     {}]],
            ["avg", ["field", fc("pct_sans_diplome"), {}]],
        ],
        breakouts=[["field", fc("bloc_dominant"), {}]],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q6 — Revenus et pauvrete par bloc dominant (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q6 - Revenus et pauvrete par bloc dominant (2022)",
        aggregations=[
            ["median", ["field", fc("mediane_revenu_disp"), {}]],
            ["avg",    ["field", fc("taux_pauvrete"),       {}]],
        ],
        breakouts=[["field", fc("bloc_dominant"), {}]],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q7 — Bloc dominant par typologie (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q7 - Bloc dominant par typologie (2022)",
        aggregations=[["count"]],
        breakouts=[
            ["field", fc("typologie_territoire"), {}],
            ["field", fc("bloc_dominant"),        {}],
        ],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q8 — Caracteristiques socio-economiques par typologie (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q8 - Caracteristiques socio-economiques par typologie (2022)",
        aggregations=[
            ["avg", ["field", fc("pct_bac_plus"),         {}]],
            ["avg", ["field", fc("cadres_pct"),            {}]],
            ["avg", ["field", fc("mediane_revenu_disp"),  {}]],
        ],
        breakouts=[["field", fc("typologie_territoire"), {}]],
        filters=["=", ["field", fc("annee"), {}], 2022],
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q9 — Top 10 departements Gauche (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q9 - Top 10 departements Gauche (2022)",
        aggregations=[["count"]],
        breakouts=[["field", fc("code_dep"), {}]],
        filters=["and",
            ["=", ["field", fc("annee"),          {}], 2022],
            ["=", ["field", fc("bloc_dominant"),  {}], "Gauche"],
        ],
        order_by=[["desc", ["aggregation", 0]]],
        limit=10,
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q10 — Top 10 departements Droite (2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_fc,
        name="Q10 - Top 10 departements Droite (2022)",
        aggregations=[["count"]],
        breakouts=[["field", fc("code_dep"), {}]],
        filters=["and",
            ["=", ["field", fc("annee"),          {}], 2022],
            ["=", ["field", fc("bloc_dominant"),  {}], "Droite"],
        ],
        order_by=[["desc", ["aggregation", 0]]],
        limit=10,
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q11 — Predictions 2022 par bloc
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_pred,
        name="Q11 - Predictions 2022 par bloc",
        aggregations=[["count"]],
        breakouts=[["field", pr("bloc_predit"), {}]],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q12 — Communes predites en 2022
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_pred,
        name="Q12 - Communes predites en 2022",
        aggregations=[["count"]],
        breakouts=[
            ["field", pr("bloc_predit"),          {}],
            ["field", pr("typologie_territoire"), {}],
        ],
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q13 — Probabilites moyennes par bloc (predit 2022)
    # Requete SQL native : pivot des 3 probabilites en lignes (bloc, prob_moyenne)
    # pour obtenir un bar chart lisible avec axe X = bloc.
    # ------------------------------------------------------------------
    cards.append(make_sql_card(
        database_id,
        name="Q13 - Probabilites moyennes par bloc (predit 2022)",
        sql=(
            "SELECT 'Gauche'  AS bloc, ROUND(AVG(prob_gauche)::numeric, 4) AS prob_moyenne "
            "FROM gold_france.predictions_2022\n"
            "UNION ALL\n"
            "SELECT 'Centre'  AS bloc, ROUND(AVG(prob_centre)::numeric, 4) AS prob_moyenne "
            "FROM gold_france.predictions_2022\n"
            "UNION ALL\n"
            "SELECT 'Droite'  AS bloc, ROUND(AVG(prob_droite)::numeric, 4) AS prob_moyenne "
            "FROM gold_france.predictions_2022\n"
            "ORDER BY bloc"
        ),
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q14 — Predictions 2022 par typologie
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_pred,
        name="Q14 - Predictions 2022 par typologie",
        aggregations=[["count"]],
        breakouts=[
            ["field", pr("typologie_territoire"), {}],
            ["field", pr("bloc_predit"),          {}],
        ],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q15 — Probabilite Droite par typologie (predit 2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_pred,
        name="Q15 - Probabilite Droite par typologie (predit 2022)",
        aggregations=[["avg", ["field", pr("prob_droite"), {}]]],
        breakouts=[["field", pr("typologie_territoire"), {}]],
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q16 — Top 20 departements Droite (predit 2022)
    # ------------------------------------------------------------------
    cards.append(make_gui_card(
        database_id, tid_pred,
        name="Q16 - Top 20 departements Droite (predit 2022)",
        aggregations=[["count"]],
        breakouts=[["field", pr("code_dep"), {}]],
        filters=["=", ["field", pr("bloc_predit"), {}], "Droite"],
        order_by=[["desc", ["aggregation", 0]]],
        limit=20,
        display="bar",
    ))

    # ------------------------------------------------------------------
    # Q17 — Communes mal predites : predit vs reel 2022
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q17 - Communes mal predites : predit vs reel 2022",
        sql="""
SELECT
  p.code_commune,
  p.libelle,
  p.code_dep,
  p.bloc_predit,
  fc.bloc_dominant AS bloc_reel,
  p.typologie_territoire
FROM gold_france.predictions_2022 p
JOIN gold_france.features_communes fc
  ON p.code_commune = fc.code_commune
WHERE fc.annee = 2022
  AND p.bloc_predit <> fc.bloc_dominant
ORDER BY p.code_dep, p.libelle
LIMIT 100;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q18 — Comparaison reel 2022 vs predit 2022 par departement
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q18 - Comparaison reel vs predit 2022 par departement",
        sql="""
SELECT 'Reel 2022' AS source, code_dep, bloc_dominant AS bloc, COUNT(*) AS nb
FROM gold_france.features_communes
WHERE annee = 2022
  AND code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_dominant
UNION ALL
SELECT 'Predit 2022', p.code_dep, p.bloc_predit, COUNT(*)
FROM gold_france.predictions_2022 p
WHERE code_dep IN ('59','62','69','13','75','92','93','94','06','33')
GROUP BY code_dep, bloc_predit
ORDER BY code_dep, source, nb DESC;
""",
        display="table",
    ))

    # ------------------------------------------------------------------
    # Q19 — Accuracy par bloc : reel vs predit 2022
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q19 - Accuracy par bloc : reel vs predit 2022",
        sql="""
SELECT
  fc.bloc_dominant AS bloc_reel,
  p.bloc_predit,
  COUNT(*) AS nb_communes,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY fc.bloc_dominant), 1) AS pct
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
    # Q20 — Prob Droite predit pour communes rurales Gauche reel 2022
    # ------------------------------------------------------------------
    cards.append(make_sql_card(database_id,
        name="Q20 - Prob Droite predit pour communes rurales Gauche 2022",
        sql="""
SELECT
  fc.typologie_territoire,
  fc.bloc_dominant AS bloc_reel_2022,
  p.bloc_predit    AS bloc_predit_2022,
  COUNT(*)         AS nb_communes,
  ROUND(AVG(p.prob_droite), 3) AS prob_droite_moy
FROM gold_france.features_communes fc
JOIN gold_france.predictions_2022 p
  ON fc.code_commune = p.code_commune
WHERE fc.annee = 2022
  AND fc.typologie_territoire = 'rural'
  AND fc.bloc_dominant = 'Gauche'
GROUP BY fc.typologie_territoire, fc.bloc_dominant, p.bloc_predit
ORDER BY nb_communes DESC;
""",
        display="table",
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
        "questions": ["Q1 - Evolution temporelle des blocs",
                      "Q2 - Repartition blocs dominants par annee",
                      "Q11 - Predictions 2022 par bloc"],
    },
    {
        "name": "Dashboard 2 - Analyse sociodemographique",
        "questions": ["Q4 - CSP par bloc dominant (2022)",
                      "Q5 - Diplomes par bloc dominant (2022)",
                      "Q6 - Revenus et pauvrete par bloc dominant (2022)",
                      "Q8 - Caracteristiques socio-economiques par typologie (2022)"],
    },
    {
        "name": "Dashboard 3 - Typologie territoire",
        "questions": ["Q7 - Bloc dominant par typologie (2022)",
                      "Q14 - Predictions 2022 par typologie",
                      "Q15 - Probabilite Droite par typologie (predit 2022)"],
    },
    {
        "name": "Dashboard 4 - Departements cles",
        "questions": ["Q9 - Top 10 departements Gauche (2022)",
                      "Q10 - Top 10 departements Droite (2022)",
                      "Q16 - Top 20 departements Droite (predit 2022)"],
    },
    {
        "name": "Dashboard 5 - Predictions 2022",
        "questions": ["Q12 - Communes predites en 2022",
                      "Q13 - Probabilites moyennes par bloc (predit 2022)",
                      "Q16 - Top 20 departements Droite (predit 2022)"],
    },
    {
        "name": "Dashboard 6 - Comparaison reel vs predit 2022",
        "questions": ["Q18 - Comparaison reel vs predit 2022 par departement",
                      "Q19 - Accuracy par bloc : reel vs predit 2022",
                      "Q20 - Prob Droite predit pour communes rurales Gauche 2022"],
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

    print("\n--- Tables ---")
    table_id_fc = get_table_id(token, db_id, schema="gold_france", table_name="features_communes")
    table_id_pred = get_table_id(token, db_id, schema="gold_france", table_name="predictions_2022")

    if not table_id_fc or not table_id_pred:
        print("Tables introuvables. Verifier que PostgreSQL est synchronise dans Metabase.")
        print("Admin > Databases > mspr813 > Sync database schema now")
        sys.exit(1)

    print(f"  features_communes : id={table_id_fc}")
    print(f"  predictions_2022  : id={table_id_pred}")

    print("\n--- Champs ---")
    fields_fc   = get_fields(token, table_id_fc)
    fields_pred = get_fields(token, table_id_pred)
    print(f"  features_communes : {len(fields_fc)-1} champs")
    print(f"  predictions_2022  : {len(fields_pred)-1} champs")

    print("\n--- Questions ---")
    cards_existing = existing_cards(token)
    card_payloads = build_all_cards(db_id, fields_fc, fields_pred)

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
