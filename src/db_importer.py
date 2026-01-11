import pandas as pd
from sqlalchemy import create_engine
import os
import glob
import sentry_sdk 

# --- SENTRY MONITORING ---
# Für Abgabe via ZIP ist der Key hardcodiert
sentry_sdk.init(
    dsn="https://b9a777fa97d28f7260385b4052a44486@o4510688530137088.ingest.de.sentry.io/4510688535576656",
    traces_sample_rate=1.0, # Erfasst 100% der Transaktionen für Debugging
)

def run_import():
        base_dir = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, DB_NAME)
        
        # --- ALTE DATENBANK LÖSCHEN ---
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"🗑️  Alte Datenbank gelöscht: {db_path}")
            except PermissionError:
                print("❌ FEHLER: Die Datenbank ist noch geöffnet! Bitte schließe Streamlit/VS Code.")
                return
        # -------------------------------

        engine = create_engine(f'sqlite:///{db_path}')

# --- 1. Hilfsfunktion (Wichtig: Repariert deutsche Zahlenformate) ---
def clean_currency_string(value):
    """
    Wandelt deutsche Strings (1.000,00) in Python Floats (1000.0) um.
    Verhindert den 'Faktor 100'-Fehler.
    """
    if pd.isna(value) or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).strip()
    
    # WICHTIG: Unterscheidung Deutsch (Komma) vs. Englisch/Tech (Punkt)
    if ',' in val_str:
        # Deutsches Format: 1.000,00 -> Tausender-Punkte weg, Komma zu Punkt
        val_str = val_str.replace('.', '').replace(',', '.')
    else:
        # Kein Komma? Vielleicht 1000 oder 1000.00 -> Nur Punkte weg wenn es Tausender sind?
        # Sicherer Weg: Nichts tun, außer es sieht kaputt aus.
        pass
    
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# --- 2. Konfiguration ---
DB_NAME = 'finanzdaten.db'

FILE_MAPPING = [
    # (Erkennungs-Text, Tabellenname, Header-Zeile)
    ('CJI3', 'ist_kosten', 0),
    ('CJI5', 'obligo_cji5', 0),
    ('CNB1', 'obligo_banf', 0),
    ('CNB2', 'obligo_bestell', 0),
    ('LV-Übersicht', 'vertraege_uebersicht', 1),
    ('LV_Kontierung_Aufwand', 'vertraege_aufwand', 0),
    ('LV_Kontierung_Projekt', 'vertraege_projekt', 0),
    ('CON_per', 'journal_con', 0),
    ('SOBJ_per', 'journal_sobj', 0),
    ('Plausi-Check', 'plausi_ref', 7)
]

# --- 3. Hauptlogik ---
def run_import():
    # Pfade bestimmen
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, DB_NAME)
    data_dir = os.path.join(base_dir, 'data')

    engine = create_engine(f'sqlite:///{db_path}')
    print(f"🔌 Starte Import in: {db_path}")

    all_files = glob.glob(os.path.join(data_dir, "*.*"))
    
    if not all_files:
        print("⚠️  Keine Dateien im 'data'-Ordner!")
        return

    for filepath in all_files:
        filename = os.path.basename(filepath)
        imported = False
        
        for pattern, table_name, header_row in FILE_MAPPING:
            if pattern.lower() in filename.lower():
                print(f"🔄 Verarbeite '{filename}' -> '{table_name}'...")
                
                try:
                    # A) Datei einlesen (CSV mit Strichpunkt, Excel normal)
                    if filename.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(filepath, header=header_row, dtype=str)
                    elif filename.lower().endswith('.csv'):
                        # WICHTIG: thousands=None verhindert, dass Pandas Punkte falsch interpretiert
                        df = pd.read_csv(filepath, header=header_row, dtype=str, sep=';', encoding='latin1', thousands=None)
                    else:
                        continue
                    
                    # Spaltennamen normalisieren (alles klein, keine Leerzeichen)
                    df.columns = [str(c).strip().replace(' ', '_').replace('.', '').lower() for c in df.columns]
                    
                    # B) Finanz-Spalten bereinigen
                    finance_keywords = ['wert', 'betrag', 'kosten', 'obligo', 'budget', 'auftragswert']
                    for col in df.columns:
                        if any(kw in col for kw in finance_keywords):
                            df[col] = df[col].apply(clean_currency_string)
                    
                    # C) Hauptprojekt-Spalte erzeugen (für die Gruppierung im Dashboard)
                    # Macht aus "G.011803001.02.02" -> "G.011803001"
                    if 'objekt' in df.columns:
                        df['hauptprojekt'] = df['objekt'].astype(str).str[:11]
                    
                    # Speichern
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    print(f"   ✅ {len(df)} Zeilen importiert.")
                    imported = True
                    break
                
                except Exception as e:
                    print(f"   ❌ Fehler: {e}")
                    imported = True
                    break

        if not imported:
            print(f"ℹ️  Überspringe: {filename}")

    print("\n🏁 Import fertig!")

if __name__ == "__main__":
    run_import()