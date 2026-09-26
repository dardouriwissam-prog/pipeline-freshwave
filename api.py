from typing import Optional
import sqlite3
from fastapi import FastAPI, HTTPException
import pandas as pd

DB_NAME = "business_data.db"

app = FastAPI(
    title="Business & Météo API",
    description="API REST pour consulter les données consolidées des ventes et de la météo",
    version="1.0.0",
)


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Pour obtenir les résultats sous forme de dictionnaire
    return conn


@app.get("/")
def root():
    """Endpoint de test pour vérifier que l'API fonctionne."""
    return {"status": "ok", "message": "API opérationnelle ! Rendez-vous sur /docs pour la documentation interactive."}


@app.get("/api/data")
def get_consolidated_data(
    city: Optional[str] = None,
    product_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """
    Récupère les données consolidées avec des filtres optionnels :
    - **city**: Filtrer par ville (ex: Paris, Lyon)
    - **product_name**: Filtrer par produit (ex: Glace Vanille)
    - **start_date**: Date de début (YYYY-MM-DD)
    - **end_date**: Date de fin (YYYY-MM-DD)
    - **limit**: Nombre maximum de résultats (défaut: 100)
    """
    conn = get_db_connection()
    query = "SELECT * FROM final_consolidated_data WHERE 1=1"
    params = []

    if city:
        query += " AND city = ?"
        params.append(city)

    if product_name:
        query += " AND product_name = ?"
        params.append(product_name)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += f" LIMIT {limit}"

    cursor = conn.cursor()
    rows = cursor.execute(query, params).fetchall()
    conn.close()

    # Conversion des résultats en liste de dictionnaires JSON
    return [dict(row) for row in rows]


@app.get("/api/summary")
def get_summary_by_city():
    """Renvoie un résumé du chiffre d'affaires et des ventes par ville."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM final_consolidated_data", conn)
    conn.close()

    if df.empty:
        raise HTTPException(status_code=444, detail="Aucune donnée trouvée")

    summary = (
        df.groupby("city")
        .agg(
            chiffre_affaires_total=("total_revenue", "sum"),
            quantite_totale=("total_quantity", "sum"),
            nombre_transactions=("nb_transactions", "sum")
        )
        .reset_index()
    )

    return summary.to_dict(orient="records")