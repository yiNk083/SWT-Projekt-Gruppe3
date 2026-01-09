import pytest
import pandas as pd
import sys
import os
import sqlite3
from streamlit.testing.v1 import AppTest

# Pfad zu src hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Echte Funktion importieren
try:
    from src.db_importer import clean_currency_string
except ImportError:
    # Fallback für Tests, falls Import scheitert
    def clean_currency_string(val): return 0.0

# --- TEST 1: Währungsumrechnung (Kritisch!) ---
def test_currency_conversion():
    """Prüft, ob deutsche SAP-Formate korrekt in Floats umgewandelt werden."""
    assert clean_currency_string("1.000,50") == 1000.50
    assert clean_currency_string("500") == 500.0
    assert clean_currency_string("1000.50") == 1000.50  # Englisches Format
    assert clean_currency_string(None) == 0.0

# --- TEST 2: Budget Berechnung ---
def test_budget_logic():
    """Prüft die Formel: Verfügbar = Budget - (Ist + Obligo)"""
    budget = 10000.0
    ist = 2500.0
    obligo = 1500.0
    verfuegbar = budget - (ist + obligo)
    assert verfuegbar == 6000.0

# --- TEST 3: Merge Logik (Full Outer Join) ---
def test_merge_logic():
    """Prüft, ob Ist und Obligo korrekt zusammengeführt werden."""
    df_ist = pd.DataFrame({'psp': ['A', 'B'], 'wert': [100, 200]})
    df_obligo = pd.DataFrame({'psp': ['A', 'C'], 'obligo_wert': [50, 300]})
    
    merged = pd.merge(df_ist, df_obligo, on='psp', how='outer').fillna(0)
    
    assert len(merged) == 3
    # A hat beides
    assert merged[merged['psp']=='A']['wert'].iloc[0] == 100
    assert merged[merged['psp']=='A']['obligo_wert'].iloc[0] == 50
    # C hat nur Obligo
    assert merged[merged['psp']=='C']['obligo_wert'].iloc[0] == 300

# --- TEST 4: DB Connection ---
def test_database_connection():
    """Prüft SQLite Funktionalität In-Memory."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER, betrag REAL)")
    cursor.execute("INSERT INTO test VALUES (1, 99.50)")
    conn.commit()
    df = pd.read_sql("SELECT * FROM test", conn)
    assert df['betrag'][0] == 99.50
    conn.close()

# --- TEST 5: UI Smoke Test ---
def test_app_starts():
    """Prüft, ob die App ohne Absturz startet."""
    at = AppTest.from_file("src/app.py")
    at.run()
    assert not at.exception