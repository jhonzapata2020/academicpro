import os
import sys

# Agregar la raíz del proyecto a sys.path para Vercel Serverless Functions
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app
