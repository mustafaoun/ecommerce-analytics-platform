# Ecommerce Analytics Platform

> Full-stack data engineering and BI solution — from raw data generation to production dashboard.

---

## What this project does

Builds a complete, production-style data pipeline for an e-commerce business:
- Generates realistic synthetic transaction and customer data
- Runs an ETL process to clean, transform, and load data into PostgreSQL
- Surfaces business insights through a Metabase BI dashboard

This project demonstrates the ability to architect a scalable data stack from scratch — not just run analysis on an existing clean dataset.

---

## Architecture

```
Data Generation (Python)
        ↓
   ETL Pipeline
  (Clean · Transform · Load)
        ↓
  PostgreSQL Database
        ↓
  Metabase Dashboard
  (KPIs · Trends · Segments)
```

---

## Key business questions answered

- Which product categories drive the most revenue?
- What is the customer retention rate by cohort?
- Where are the biggest drops in the purchase funnel?
- Which customer segments have the highest lifetime value?

---

## Tech stack

| Layer | Technology |
|---|---|
| Data generation | Python (Faker, Pandas) |
| ETL pipeline | Python (custom scripts) |
| Database | PostgreSQL |
| BI dashboard | Metabase |
| Version control | Git / GitHub |

---

## How to run it

```bash
# Clone the repo
git clone https://github.com/mustafaoun/ecommerce-analytics-platform
cd ecommerce-analytics-platform

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
python generate_data.py

# Run ETL pipeline
python etl_pipeline.py

# Connect Metabase to your PostgreSQL instance
# See /docs/metabase_setup.md for connection instructions
```

---

## What I learned

- Designing a normalized PostgreSQL schema for transactional data
- Building modular ETL scripts that handle real-world data quality issues
- Connecting a BI tool (Metabase) to a live database for dynamic reporting
- Thinking about data pipelines from a production, not a notebook, perspective

---

## Next steps / improvements

- Add dbt for SQL transformations
- Schedule pipeline runs with Apache Airflow
- Add data quality checks with Great Expectations
- Deploy PostgreSQL on AWS RDS for cloud-hosted demo

---

*Part of a 9-month production ML engineering roadmap.*

📬 mustafaoun.ds@gmail.com · [LinkedIn](https://linkedin.com/in/mustafa-oun)
