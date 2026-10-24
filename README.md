# E-commerce Analytics Platform

A portfolio data platform: synthetic ecommerce records → Python ETL → PostgreSQL → SQL analytics, report generation, and Metabase setup scripts. Includes Airflow DAGs for scheduled workflows.

## Evidence and scope

Historical project runs used approximately 118,600 synthetic records; throughput depends on the database and environment. These are demonstration data, not customer transactions or measured business savings. [Saved reports](reports/index.html), [SQL examples](sample_queries.sql), and [schema](src/database/schema_ddl.sql) provide inspectable outputs.

## Minimal local ETL setup

Use Python 3.10+ and Docker Compose, from this repository's root:

```bash
git clone https://github.com/mustafaoun/ecommerce-analytics-platform.git
cd ecommerce-analytics-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-etl.txt
cp .env.example .env
```

Set your own `DB_PASSWORD` in `.env`. Leave the local defaults for host, port, name and user. On Windows activate with `.venv\Scripts\activate`.

```bash
docker compose up -d postgres
python scripts/create_schema.py
python scripts/run_etl.py
```

Wait for PostgreSQL to become healthy before creating the schema. The ETL generates synthetic data and **replaces records in its five demo tables**. Use a dedicated empty development database, not a business database. Rerunning the generator is not incremental ingestion.

For a hosted database, set its connection settings and `DB_SSLMODE=require` (or the provider's verified certificate settings). Passwords containing URL punctuation are handled through SQLAlchemy's structured URL API.

## Optional reports and BI

`requirements.txt` adds the larger analytics/web/reporting dependencies. After installing those dependencies, inspect/run `python -m src.visualization.report_generator --all` against the populated database. Metabase setup scripts are in `scripts/setup_metabase*.py`; provide `METABASE_ADMIN_PASSWORD` through the environment. Existing authenticated Metabase instances may require manual setup rather than repeating first-run initialization.

The Power BI materials are in `powerbi/`. Saved outputs document prior runs; they do not establish a currently deployed service.

## Optional Airflow scheduling

Airflow has its own environment to avoid conflicting with SQLAlchemy 2 used by the ETL. Its Dockerfile installs ETL dependencies into `/opt/etl-venv`.

Set `AIRFLOW_WEBSERVER_SECRET_KEY` and `AIRFLOW_ADMIN_PASSWORD` in `.env`. Ensure the ecommerce database above is running. For this Compose command set `DB_HOST=host.docker.internal` in the shell or a separate env file; the host Python commands use `DB_HOST=localhost`.

```bash
DB_HOST=host.docker.internal docker compose -f docker-compose.airflow.yml build
DB_HOST=host.docker.internal docker compose -f docker-compose.airflow.yml up airflow-init
DB_HOST=host.docker.internal docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```

On Windows use your shell's environment-variable syntax. Open <http://localhost:8080> and log in as `admin` using your configured password. Airflow metadata and the ecommerce data database are separate services. The daily DAG mounts `scripts/`, uses the isolated ETL interpreter, and raises when the ETL command fails so retries/failure status work correctly. Full Docker/Airflow startup requires separate integration verification.

## Checks

```bash
pip install -r requirements-dev.txt
pytest -q
python -m compileall -q scripts src dags
```

Unit tests cover URL-safe database configuration, CSV replacement behavior, ETL cleanup ordering, and propagation of subprocess failure in the daily DAG. They do not connect to a hosted database or validate every optional analytics workflow.

## Configuration hygiene

Credentials belong in environment variables, never committed source. A previously embedded Git backup is excluded from the current source tree. Removing current-file secrets does not remove old Git history; any previously exposed database or admin credentials must be rotated by their owner.
