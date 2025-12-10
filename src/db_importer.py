import pandas as pd
from sqlalchemy import create_engine
import os
import glob

# --- KONFIGURATION ---
# Datenbank-Name (wird im Hauptordner erstellt)
DB_NAME = 'finanzdaten.db'

# Mapping: Welcher Dateiname (Teilstring) gehört zu welcher Tabelle?
# und: In welcher Zeile stehen die Überschriften? (header=0 ist die erste Zeile)
FILE_MAPPING = [
    # (Erkennungs-Text im Dateinamen, Tabellenname in DB, Header-Zeile)
    
    # Kosten & Obligo
    ('CJI3', 'ist_kosten', 0),
    ('CJI5', 'obligo_cji5', 0),
    ('CNB1', 'obligo_banf', 0),
    ('CNB2', 'obligo_bestell', 0),
    
    # Vertragsdaten
    ('LV-Übersicht', 'vertraege_uebersicht', 1),   # Header oft erst in Zeile 2
    ('LV_Kontierung_Aufwand', 'vertraege_aufwand', 0),
    ('LV_Kontierung_Projekt', 'vertraege_projekt', 0),
    
    # Journaldaten (Details)
    ('CON_per', 'journal_con', 0),
    ('SOBJ_per', 'journal_sobj', 0),
    
    # Referenz (Plausi)
    ('Plausi-Check', 'plausi_ref', 7)            # Header weit unten
]

def run_import():
    # 1. Verbindung zur Datenbank herstellen
    # Die DB wird im Hauptverzeichnis des Projekts erstellt (../finanzdaten.db)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_NAME)
    engine = create_engine(f'sqlite:///{db_path}')
    print(f"🔌 Verbinde mit Datenbank: {db_path}...\n")

    # 2. Dateien im data-Ordner finden
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    all_files = glob.glob(os.path.join(data_dir, "*.*")) # Findet alle Dateien
    
    if not all_files:
        print("⚠️  WARNUNG: Keine Dateien im 'data'-Ordner gefunden!")
        return

    # 3. Dateien verarbeiten
    for filepath in all_files:
        filename = os.path.basename(filepath)
        imported = False
        
        # Prüfen, zu welchem Typ die Datei gehört
        for pattern, table_name, header_row in FILE_MAPPING:
            if pattern.lower() in filename.lower():
                print(f"🔄 Verarbeite '{filename}' -> Tabelle '{table_name}'...")
                
                try:
                    # Unterscheidung Excel vs CSV
                    if filename.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(filepath, header=header_row, dtype=str)
                    elif filename.lower().endswith('.csv'):
                        df = pd.read_csv(filepath, header=header_row, dtype=str, sep=';', encoding='latin1')
                    
                    # Spaltennamen bereinigen (Leerzeichen weg, Kleinbuchstaben)
                    # FIX: Spaltennamen erst in String wandeln (für Datums-Spalten)
                    df.columns = [str(c).strip().replace(' ', '_').replace('.', '').lower() for c in df.columns]
                    
                    # In DB speichern (if_exists='replace' überschreibt die Tabelle bei jedem Lauf)
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    print(f"   ✅ Erfolg! {len(df)} Zeilen importiert.")
                    imported = True
                    break # Datei erkannt, nächste Datei
                
                except Exception as e:
                    print(f"   ❌ Fehler beim Import: {e}")
                    imported = True # Fehler behandelt, trotzdem weiter
                    break

        if not imported:
            print(f"ℹ️  Überspringe unbekannte Datei: {filename}")

    print("\n🏁 Import abgeschlossen!")

if __name__ == "__main__":
    run_import()