#!/usr/bin/env python3
"""
Run the ETL pipeline and then regenerate the HTML reports.
This creates automated dashboards (HTML) that update whenever data is regenerated.

Usage:
  python scripts/automate_etl_and_reports.py

You can schedule this script in your environment or call it from Airflow.
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
PY = sys.executable

def run_cmd(cmd, cwd=None):
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main():
    # 1. Run ETL
    run_cmd(f"{PY} scripts/run_etl.py", cwd=ROOT)

    # 2. Regenerate HTML reports
    # report_generator exposes a CLI; use module invocation if available
    run_cmd(f"{PY} -m src.visualization.report_generator --all", cwd=ROOT)

    print("\n✅ ETL and report generation completed. Check the `reports/` folder for updated dashboards.")

if __name__ == '__main__':
    main()
