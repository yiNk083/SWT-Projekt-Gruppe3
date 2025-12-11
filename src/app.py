import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Finanz-Plausi-Tool", layout="wide")

# Datenbank-Verbindung
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'finanzdaten.db')
engine = create_engine(f'sqlite:///{db_path}')

# --- TITEL & SIDEBAR ---
st.title("📊 Projekt-Controlling & Plausi-Check")

# Wir laden alle PSP-Elemente aus den Ist-Kosten für die Auswahlbox
@st.cache_data
def load_psp_liste():
    try:
        # Hole eindeutige Objekte aus der Ist-Kosten Tabelle
        df = pd.read_sql("SELECT DISTINCT Objekt FROM ist_kosten ORDER BY Objekt", engine)
        return df['objekt'].tolist()
    except Exception as e:
        st.error(f"Fehler beim Laden der PSP-Elemente: {e}")
        return []

alle_psp = load_psp_liste()

# Sidebar Auswahl
st.sidebar.header("Filter")
if alle_psp:
    selected_psp = st.sidebar.selectbox("Wähle ein PSP-Element:", alle_psp)
else:
    st.sidebar.warning("Keine Daten gefunden.")
    selected_psp = None

# --- HAUPTBEREICH ---

if selected_psp:
    st.markdown(f"### Übersicht für: `{selected_psp}`")

    # 1. DATEN LADEN (Ist-Kosten)
    # Wir holen nur die Daten für das gewählte PSP
    query_ist = f"""
    SELECT 
        k.bezeichnung_des_gegenkontos as kreditor,
        k.bezeichnung as text,
        k.einkaufsbeleg as bestellung,
        k."wert/bwähr" as wert,
        k.periode
    FROM ist_kosten k
    WHERE k.objekt = '{selected_psp}'
    """
    df_ist = pd.read_sql(query_ist, engine)
    
    # Konvertieren: Wert als Zahl (Komma durch Punkt ersetzen falls nötig)
    # Da wir Strings importiert haben, müssen wir aufräumen
    if not df_ist.empty:
        df_ist['wert'] = df_ist['wert'].astype(str).str.replace(',', '.').astype(float)
        
        # 2. KPIs ANZEIGEN
        total_ist = df_ist['wert'].sum()
        anzahl_buchungen = len(df_ist)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Summe Ist-Kosten", f"{total_ist:,.2f} €")
        col2.metric("Anzahl Buchungen", anzahl_buchungen)
        
        # 3. MATRIX (PIVOT)
        st.subheader("Monatliche Verteilung")
        
        # Pivot: Zeilen = Text, Spalten = Periode, Wert = Summe
        pivot_df = df_ist.pivot_table(
            index=['kreditor', 'text'], 
            columns='periode', 
            values='wert', 
            aggfunc='sum',
            fill_value=0
        )
        
        # Spalten sortieren (1, 2, 3... statt 1, 10, 11)
        # Wir versuchen, die Spalten numerisch zu sortieren
        cols = sorted(pivot_df.columns, key=lambda x: int(x) if str(x).isdigit() else 99)
        pivot_df = pivot_df[cols]
        
        # Zeilensumme hinzufügen
        pivot_df['Gesamt'] = pivot_df.sum(axis=1)
        
        st.dataframe(pivot_df.style.format("{:,.2f}"), use_container_width=True)

        # 4. DETAILS (Rohdaten)
        with st.expander("Details (Einzelposten) ansehen"):
            st.dataframe(df_ist)
            
    else:
        st.info("Keine Ist-Kosten für dieses PSP-Element gefunden.")

else:
    st.info("👈 Bitte wählen Sie links ein PSP-Element aus.")