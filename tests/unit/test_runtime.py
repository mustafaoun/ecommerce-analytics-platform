import ast
from contextlib import contextmanager
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pandas as pd
import pytest

from src.database.connection import DatabaseConnection
from src.etl.data_loader import DataLoader


def test_database_url_preserves_special_password_and_ssl(monkeypatch):
    secret = 'synthetic@:/?#test'
    for key, value in {'DB_HOST': 'localhost', 'DB_PORT': '5432', 'DB_NAME': 'demo', 'DB_USER': 'tester', 'DB_PASSWORD': secret, 'DB_SSLMODE': 'require'}.items():
        monkeypatch.setenv(key, value)
    db = DatabaseConnection()
    assert db.get_engine().url.password == secret
    assert db.conn_params['sslmode'] == 'require'
    assert db.get_engine().url.host == 'localhost'
    db.get_engine().dispose()


def test_csv_replaces_first_chunk_then_appends(tmp_path, monkeypatch):
    path = tmp_path / 'rows.csv'
    pd.DataFrame({'x': range(10001)}).to_csv(path, index=False)
    loader = DataLoader.__new__(DataLoader)
    calls = []
    monkeypatch.setattr(loader, 'load_dataframe', lambda df, table, if_exists: calls.append(if_exists) or True)
    assert loader.load_from_csv(str(path), 'demo', if_exists='replace')
    assert calls == ['replace', 'append']


def test_related_tables_cleared_together_before_loading(monkeypatch):
    calls = []
    class Connection:
        def execute(self, statement):
            calls.append(str(statement))
    class Engine:
        @contextmanager
        def begin(self):
            yield Connection()
    loader = DataLoader.__new__(DataLoader)
    loader.engine = Engine()
    monkeypatch.setattr(loader, 'load_dataframe', lambda df, table, **kwargs: calls.append(table) or True)
    monkeypatch.setattr(loader, 'get_table_info', lambda table: {})
    assert loader.run_etl_pipeline({'orders': pd.DataFrame(), 'users': pd.DataFrame()})
    assert calls == ['TRUNCATE TABLE users, orders RESTART IDENTITY', 'users', 'orders']


def test_daily_task_propagates_failed_etl():
    # Load just the callable so this regression check does not require an Airflow install.
    source = Path('dags/ecommerce_daily_pipeline.py').read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'run_etl')
    runner = Mock(side_effect=subprocess.CalledProcessError(1, ['etl']))
    namespace = {'subprocess': type('Process', (), {'run': staticmethod(runner)}), 'os': __import__('os'), 'sys': __import__('sys')}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<daily-task>', 'exec'), namespace)
    with pytest.raises(subprocess.CalledProcessError):
        namespace['run_etl']()
    assert runner.call_args.kwargs['check'] is True


def test_compose_requires_external_password():
    import yaml
    config = yaml.safe_load(Path('docker-compose.airflow.yml').read_text())
    env = config['x-airflow-common']['environment']
    assert env['DB_PASSWORD'].startswith('${DB_PASSWORD:?')
    assert env['ETL_PYTHON'] == '/opt/etl-venv/bin/python'
    assert './scripts:/opt/airflow/scripts:ro' in config['x-airflow-common']['volumes']
