# 🍦 FreshWave - ETL Data Pipeline & REST API

An end-to-end data pipeline and REST API built to analyze sales, marketing performance, and weather impacts for **FreshWave**, an ice cream and beverage retail chain across 8 major French cities.

---

## 📌 Project Overview

This project consolidates disparate data sources (sales logs, marketing spend, product details, store metadata, and historical weather data) into a clean, centralized SQLite database. It exposes the consolidated data through a FastAPI service for analytics and business intelligence.

---

## 📂 Repository Structure

```text
pipeline-freshwave/
│
├── pipeline.py               # ETL pipeline (Extract, Transform, Load)
├── api.py                    # FastAPI REST API implementation
├── business_data.db          # SQLite database containing transformed data
├── sales.csv                 # Raw store sales data
├── marketing_campaigns.csv   # Historical marketing campaigns dataset
├── stores.sql                # SQL initialization for stores table
├── products.sql              # SQL initialization for products table
└── README.md                 # Project documentation
```

---

## ⚙️ Data Pipeline (ETL) Highlights

The pipeline implemented in `pipeline.py` executes the following steps:

1. **Database Initialization (`init_database`)**:
   - Creates the `business_data.db` SQLite database.
   - Executes `stores.sql` and `products.sql` scripts to establish reference tables.

2. **Data Extraction (`extract`)**:
   - Reads local CSVs (`sales.csv`, `marketing_campaigns.csv`).
   - Fetches historical daily weather metrics (temperatures, precipitation) for 8 French cities using the **Open-Meteo Archive API**.

3. **Transformation & Cleaning (`transform`)**:
   - Filters sales and marketing records for the target window (**May 1, 2024 – August 31, 2024**).
   - Enriches sales data with store metadata, product prices, and local weather conditions.
   - Adds feature engineering fields: `is_weekend`, `temp_bucket`, and `rain_bucket`.
   - Aggregates metrics (`total_revenue`, `total_quantity`, `nb_transactions`).

4. **Loading (`load`)**:
   - Saves the final consolidated dataset into the SQLite table `final_consolidated_data`.

---

## 🚀 API Endpoints (FastAPI)

The REST API implemented in `api.py` exposes the processed business data.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API Health Check and status welcome message. |
| `GET` | `/api/data` | Query consolidated data with optional filters (`city`, `product_name`, `start_date`, `end_date`, `limit`). |
| `GET` | `/api/summary` | Get aggregated revenue, quantity sold, and transaction counts grouped by city. |

---

## 🛠️ Installation & Execution

### 1. Prerequisites
Ensure you have Python installed. Install required packages:
```bash
python -m pip install pandas requests fastapi uvicorn
```

### 2. Run the ETL Pipeline
To execute the pipeline and update `business_data.db`:
```bash
python pipeline.py
```

### 3. Launch the REST API
Start the FastAPI application using Uvicorn:
```bash
python -m uvicorn api:app --reload
```

### 4. Interactive API Documentation
Once the server is running, open your browser and navigate to:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`