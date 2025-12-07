web: gunicorn -b 0.0.0.0:$PORT -w 4 --timeout 120 app:app
release: python scripts/create_schema.py
