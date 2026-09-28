import os
import sys
from pathlib import Path

# Never connect to the configured Supabase database during tests or import-time DDL.
os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
