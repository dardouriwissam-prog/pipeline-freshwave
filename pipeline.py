import sqlite3
import pandas as pd
import requests

DB_NAME = "business_data.db"

CITY_COORDS = {
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Marseille": (43.2965, 5.3698),
    "Bordeaux": (44.8378, -0.5792),
    "Lille": (50.6292, 3.0573),
    "Nantes": (47.2184, -1.5536),
    "Toulouse": (43.6047, 1.4442),
    "Nice": (43.7102, 7.2620),
}

START_DATE = "2024-05-01"
END_DATE = "2024-08-31"


def init_database():
    """Étape 2 : Initialise la base SQLite avec stores.sql et products.sql."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    with open("stores.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    with open("products.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès !")


def fetch_weather_for_city(city, lat, lon):
    """Étape 3 : Appel API Open-Meteo pour une ville donnée."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "auto",
    }

    response = requests.get(url, params=params)
    data = response.json()

    df_weather = pd.DataFrame(data["daily"])
    df_weather["city"] = city
    df_weather["time"] = pd.to_datetime(df_weather["time"])

    df_weather = df_weather.rename(
        columns={
            "time": "date",
            "temperature_2m_max": "temperature_max",
            "temperature_2m_min": "temperature_min",
            "precipitation_sum": "precipitation_sum",
            "wind_speed_10m_max": "wind_speed_max",
        }
    )

    return df_weather


def extract():
    """Étape 3 : Extraction globale des données."""
    data = {}

    # 1. Chargement des CSV
    data["sales"] = pd.read_csv("sales.csv")
    data["marketing_campaigns"] = pd.read_csv("marketing_campaigns.csv")

    # Formatage des dates
    data["sales"]["date"] = pd.to_datetime(data["sales"]["date"])
    data["marketing_campaigns"]["date"] = pd.to_datetime(
        data["marketing_campaigns"]["date"]
    )

    # 2. Récupération des tables SQLite
    conn = sqlite3.connect(DB_NAME)
    data["stores"] = pd.read_sql_query("SELECT * FROM stores", conn)
    data["products"] = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    # 3. Récupération des données météo via l'API
    print("⏳ Récupération de la météo pour les 8 villes...")
    weather_list = []
    for city, (lat, lon) in CITY_COORDS.items():
        df_city = fetch_weather_for_city(city, lat, lon)
        weather_list.append(df_city)

    weather = pd.concat(weather_list, ignore_index=True)
    data["weather"] = weather

    print(f"✅ Météo récupérée : {len(weather)} lignes pour {weather['city'].nunique()} villes.")
    return data


def transform(data):
    """Étape 4 : Nettoyage, fusions, catégories et agrégation."""
    print("⏳ Transformation et agrégation des données...")

    sales = data["sales"]
    marketing = data["marketing_campaigns"]
    stores = data["stores"]
    products = data["products"]
    weather = data["weather"]

    # 1. Nettoyage & Filtrage Mai - Août 2024
    start = pd.to_datetime(START_DATE)
    end = pd.to_datetime(END_DATE)

    sales = sales[(sales["date"] >= start) & (sales["date"] <= end)]
    marketing = marketing[(marketing["date"] >= start) & (marketing["date"] <= end)]

    # 2. Fusions : Sales + Stores + Products
    merged = sales.merge(stores, on="store_id", how="inner")
    merged = merged.merge(products, on="product_id", how="inner")

    # Fusion avec Météo (sur date et city)
    merged = merged.merge(weather, on=["date", "city"], how="left")

    # 3. Variables d'analyse
    merged["is_weekend"] = merged["date"].dt.dayofweek.isin([5, 6])

    merged["temp_bucket"] = pd.cut(
        merged["temperature_max"],
        bins=[-float("inf"), 20, 25, 30, float("inf")],
        labels=["<=20°C", "20-25°C", "25-30°C", ">30°C"],
    )

    merged["rain_bucket"] = pd.cut(
        merged["precipitation_sum"],
        bins=[-0.1, 0, 5, 20, float("inf")],
        labels=["0 mm", "0-5 mm", "5-20 mm", ">20 mm"],
    )

    # Fusion avec les dépenses marketing (agrégées par date et ville)
    mkt_agg = (
        marketing.groupby(["date", "city"])
        .agg(marketing_spend=("marketing_spend", "sum"))
        .reset_index()
    )
    merged = merged.merge(mkt_agg, on=["date", "city"], how="left")
    merged["marketing_spend"] = merged["marketing_spend"].fillna(0)

    # 4. Agrégation finale
    group_cols = [
        "date",
        "city",
        "store_id",
        "product_name",
        "category",
        "temperature_max",
        "precipitation_sum",
        "marketing_spend",
    ]

    final_df = (
        merged.groupby(group_cols, observed=True)
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity=("quantity_sold", "sum"),
            nb_transactions=("sale_id", "nunique"),
        )
        .reset_index()
    )

    # Formatage de la date en chaîne de caractères pour SQLite
    final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

    print("✅ Transformation terminée avec succès !")
    return final_df


def load(df):
    """Étape 6 : Enregistre le DataFrame final dans SQLite."""
    conn = sqlite3.connect(DB_NAME)
    df.to_sql("final_consolidated_data", conn, if_exists="replace", index=False)
    conn.close()
    print("✅ Table final_consolidated_data sauvegardée dans business_data.db !")


def main():
    init_database()
    data = extract()
    final_df = transform(data)
    load(final_df)


if __name__ == "__main__":
    main()