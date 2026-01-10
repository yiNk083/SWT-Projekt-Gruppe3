import pandas as pd
from sqlalchemy import create_engine
import os
import glob

# --- KONFIGURATION ---
DB_NAME = 'finanzdaten.db'

# Mapping: (Erkennungs-Text im Dateinamen, Tabellenname in DB, Header-Zeile)
FILE_MAPPING = [
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

def clean_currency_string(value):
    """
    Bereinigt Währungsstrings und konvertiert sie in Float.
    Behandelt deutsches Format (1.000,00) korrekt.
    
    Args:
        value: Der Rohwert aus der Excel/CSV (str, float, oder None)
    
    Returns:
        float: Der bereinigte Zahlenwert oder 0.0 bei Fehler
    """
    if pd.isna(value) or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).strip()
    
    # Deutsches Format erkennen: Wenn Komma vorhanden, Punkte entfernen und Komma ersetzen
    if ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def run_import():
    """
    Hauptfunktion des ETL-Prozesses (Extract, Transform, Load).
    1. Löscht alte Datenbank (Clean State).
    2. Sucht Dateien im /data Ordner.
    3. Bereinigt Zahlenformate.
    4. Generiert Hauptprojekt-Logik.
    5. Speichert Daten in SQLite.
    """
    # Pfade relativ zum Skript bestimmen
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, DB_NAME)
    data_dir = os.path.join(base_dir, 'data')

    # 1. Alte DB löschen (Vermeidung von Duplikaten)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"🗑️  Alte Datenbank gelöscht: {db_path}")
        except PermissionError:
            print("❌ FEHLER: Datenbank ist gesperrt. Bitte Anwendung schließen.")
            return

    engine = create_engine(f'sqlite:///{db_path}')
    print(f"🔌 Starte Import in: {db_path}")

    all_files = glob.glob(os.path.join(data_dir, "*.*"))
    
    if not all_files:
        print("⚠️  Keine Dateien im 'data'-Ordner gefunden!")
        return

    # 2. Dateien iterieren und verarbeiten
    for filepath in all_files:
        filename = os.path.basename(filepath)
        imported = False
        
        for pattern, table_name, header_row in FILE_MAPPING:
            if pattern.lower() in filename.lower():
                print(f"🔄 Verarbeite '{filename}' -> Tabelle '{table_name}'...")
                
                try:
                    # Fallunterscheidung Excel vs. CSV
                    if filename.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(filepath, header=header_row, dtype=str)
                    elif filename.lower().endswith('.csv'):
                        # 'thousands=None' verhindert Fehlinterpretation von Punkten
                        df = pd.read_csv(filepath, header=header_row, dtype=str, sep=';', encoding='latin1', thousands=None)
                    else:
                        continue
                    
                    # Spaltennamen normalisieren (Snake_Case)
                    df.columns = [str(c).strip().replace(' ', '_').replace('.', '').lower() for c in df.columns]
                    
                    # A) Finanzspalten bereinigen
                    finance_keywords = ['wert', 'betrag', 'kosten', 'obligo', 'budget', 'auftragswert']
                    for col in df.columns:
                        if any(kw in col for kw in finance_keywords):
                            df[col] = df[col].apply(clean_currency_string)
                    
                    # B) Hauptprojekt ableiten (für Gruppierung im Dashboard)
                    if 'objekt' in df.columns:
                        df['hauptprojekt'] = df['objekt'].astype(str).str[:11]
                    
                    # C) In DB speichern
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    print(f"   ✅ {len(df)} Zeilen importiert.")
                    imported = True
                    break
                
                except Exception as e:
                    print(f"   ❌ Fehler beim Import von {filename}: {e}")
                    imported = True
                    break

        if not imported:
            print(f"ℹ️  Datei übersprungen (kein Mapping): {filename}")

    print("\n🏁 Import vollständig abgeschlossen!")

if __name__ == "__main__":
    run_import()