# test_setup.py
import os
from dotenv import load_dotenv

load_dotenv()

print("🧪 Testing Environment Setup...")
print(f"DB Host: {os.getenv('DB_HOST')}")
print(f"Project structure: {os.listdir('.')}")

# Create virtual environment instruction
print("\n📦 To set up virtual environment:")
print("python -m venv venv")
print("source venv/bin/activate  # On Mac/Linux")
print("venv\\Scripts\\activate  # On Windows")
print("pip install -r requirements.txt")