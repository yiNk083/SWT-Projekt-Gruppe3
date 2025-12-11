import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# --- KONFIGURATION ---
APP_NAME = "Projekt-Analyse-Cockpit"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🚄")

# Datenbank-Verbindung
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'finanzdaten.db')
engine = create_engine(f'sqlite:///{db_path}')

# --- HILFSFUNKTIONEN ---

def format_currency(val):
    if pd.isna(val):
        val = 0
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_number(series):
    # Wandelt Text "1.000,00" -> Zahl 1000.0
    return pd.to_numeric(series.astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

def get_project_from_psp(psp_string):
    # Macht aus G.011803001.03.03 -> G.011803001 (Hauptprojekt)
    if not isinstance(psp_string, str):
        return "Unbekannt"
    parts = psp_string.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return psp_string

# --- SEITENLEISTE ---

logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)

st.sidebar.header("Filter & Navigation")

# 1. Projekt-Liste laden
try:
    # Wir suchen alle Projekte aus allen relevanten Tabellen
    query_all = """
    SELECT DISTINCT Objekt as psp FROM ist_kosten
    UNION
    SELECT DISTINCT Objekt as psp FROM obligo_cji5
    """
    df_all_psps = pd.read_sql(query_all, engine)
    
    # Projektnummern extrahieren
    raw_psps = df_all_psps['psp'].dropna().astype(str).tolist()
    all_projects = sorted(list(set([get_project_from_psp(p) for p in raw_psps])))
except Exception as e:
    st.sidebar.error(f"Datenbank-Fehler: {e}")
    all_projects = []

if all_projects:
    selected_project = st.sidebar.selectbox("Projekt wählen:", all_projects)
else:
    st.sidebar.warning("Keine Projekte gefunden.")
    selected_project = None

# --- HAUPTBEREICH ---

st.title(f"🚄 {APP_NAME}")

if selected_project:
    
    st.markdown(f"### Analyse für Projekt: `{selected_project}`")

    # ---------------------------------------------------------
    # 1. DATEN LADEN
    # ---------------------------------------------------------
    
    # A) IST-KOSTEN
    query_ist = f"""
    SELECT objekt as psp, einkaufsbeleg as bestellung, bezeichnung as text, "wert/bwähr" as wert, periode
    FROM ist_kosten 
    WHERE objekt LIKE '{selected_project}%'
    """
    df_ist = pd.read_sql(query_ist, engine)

    # B) OBLIGO
    # Fallback, falls Spalte 'bezeichnung' fehlt
    try:
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, bezeichnung as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 WHERE objekt LIKE '{selected_project}%'
        """
        df_obligo = pd.read_sql(query_obligo, engine)
    except:
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, '' as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 WHERE objekt LIKE '{selected_project}%'
        """
        df_obligo = pd.read_sql(query_obligo, engine)

    # C) BUDGET
    try:
        query_budget = f"""
        SELECT betrag, bezeichnung, "planungelement" as psp_budget
        FROM vertraege_uebersicht 
        WHERE "planungelement" LIKE '%{selected_project}%' OR "projektnummer" LIKE '%{selected_project}%'
        """
        df_budget = pd.read_sql(query_budget, engine)
    except:
        df_budget = pd.DataFrame()

    # ---------------------------------------------------------
    # 2. ZAHLEN BEREINIGEN
    # ---------------------------------------------------------

    if not df_ist.empty:
        df_ist['wert'] = clean_number(df_ist['wert'])
    
    if not df_obligo.empty:
        df_obligo['obligo_wert'] = clean_number(df_obligo['obligo_wert'])
    
    if not df_budget.empty:
        df_budget['betrag'] = clean_number(df_budget['betrag'])

    # ---------------------------------------------------------
    # 3. KPI DASHBOARD (GESAMTSUMMEN)
    # ---------------------------------------------------------

    total_ist = df_ist['wert'].sum() if not df_ist.empty else 0.0
    total_obligo = df_obligo['obligo_wert'].sum() if not df_obligo.empty else 0.0
    total_budget = df_budget['betrag'].sum() if not df_budget.empty else 0.0
    verfuegbar = total_budget - (total_ist + total_obligo)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gesamt-Budget", format_currency(total_budget))
    c2.metric("Ist-Kosten", format_currency(total_ist))
    c3.metric("Obligo", format_currency(total_obligo))
    c4.metric("Verfügbar", format_currency(verfuegbar), 
              delta="Achtung" if verfuegbar < 0 else "OK", 
              delta_color="inverse" if verfuegbar < 0 else "normal")

    st.divider()

    # ---------------------------------------------------------
    # 4. PSP-STRUKTUR ÜBERSICHT (NEU!)
    # ---------------------------------------------------------
    st.subheader("📑 PSP-Elemente im Projekt")
    
    # Wir aggregieren Ist-Kosten pro PSP
    if not df_ist.empty:
        psp_ist = df_ist.groupby('psp')['wert'].sum().reset_index()
    else:
        psp_ist = pd.DataFrame(columns=['psp', 'wert'])
        
    # Wir aggregieren Obligo pro PSP
    if not df_obligo.empty:
        psp_obligo = df_obligo.groupby('psp')['obligo_wert'].sum().reset_index()
    else:
        psp_obligo = pd.DataFrame(columns=['psp', 'obligo_wert'])

    # Merge PSP Stats
    df_psp_stats = pd.merge(psp_ist, psp_obligo, on='psp', how='outer').fillna(0)
    df_psp_stats['Gesamtaufwand'] = df_psp_stats['wert'] + df_psp_stats['obligo_wert']
    
    # Tabelle anzeigen
    if not df_psp_stats.empty:
        st.dataframe(
            df_psp_stats.rename(columns={'wert': 'Ist', 'obligo_wert': 'Obligo'}).style.format({
                'Ist': "{:,.2f}", 
                'Obligo': "{:,.2f}", 
                'Gesamtaufwand': "{:,.2f}"
            }),
            use_container_width=True
        )
    else:
        st.info("Keine PSP-Details verfügbar.")

    st.divider()

    # ---------------------------------------------------------
    # 5. MATRIX (ZUSAMMENGEFASST)
    # ---------------------------------------------------------
    st.subheader("📋 Bestell-Matrix (Zusammengefasst)")

    # Vorbereitung Ist
    if not df_ist.empty:
        # Fülle leere Bestellnummern
        df_ist['bestellung'] = df_ist['bestellung'].fillna('').astype(str).str.strip()
        df_ist['bestellung'] = df_ist['bestellung'].replace(['', 'nan', 'None'], 'Sonstiges / Ohne Bestellung')
        df_ist['text'] = df_ist['text'].fillna('Unbekannt')

        # GRUPPIERUNG: Wir gruppieren NUR noch nach Bestellung für die Zeilen
        # Text nehmen wir den häufigsten (mode) oder ersten
        # Pivot: Zeile=Bestellung, Spalte=Periode
        pivot_ist = df_ist.pivot_table(
            index='bestellung', 
            columns='periode', 
            values='wert', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Wir holen uns separat den Text zur Bestellung (z.B. der erste Eintrag)
        text_map = df_ist.groupby('bestellung')['text'].first()
        
        pivot_ist['Summe Ist'] = pivot_ist.sum(axis=1)
        pivot_ist = pivot_ist.reset_index()
        
        # Text wieder anfügen
        pivot_ist['text'] = pivot_ist['bestellung'].map(text_map)
        
    else:
        pivot_ist = pd.DataFrame(columns=['bestellung', 'Summe Ist', 'text'])

    # Vorbereitung Obligo
    if not df_obligo.empty:
        df_obligo['bestellung'] = df_obligo['bestellung'].fillna('').astype(str).str.strip()
        grp_obligo = df_obligo.groupby('bestellung').agg({
            'obligo_wert': 'sum',
            'text_obligo': 'first'
        }).reset_index()
    else:
        grp_obligo = pd.DataFrame(columns=['bestellung', 'obligo_wert', 'text_obligo'])

    # Merge (Outer)
    final_df = pd.merge(pivot_ist, grp_obligo, on='bestellung', how='outer')

    # Aufräumen
    final_df['Summe Ist'] = final_df['Summe Ist'].fillna(0)
    final_df['obligo_wert'] = final_df['obligo_wert'].fillna(0)
    
    # Texte mergen
    if 'text' not in final_df.columns: final_df['text'] = ""
    final_df['text'] = final_df['text'].fillna(final_df['text_obligo']).fillna("Ohne Bezeichnung")
    
    # Auftragswert
    final_df['Auftragswert (Kalk.)'] = final_df['Summe Ist'] + final_df['obligo_wert']

    # Sortierung und Spalten
    # "Sonstiges" nach unten
    final_df['sort_helper'] = final_df['bestellung'].apply(lambda x: 'ZZZ' if 'Sonstiges' in x else x)
    final_df = final_df.sort_values('sort_helper').drop(columns=['sort_helper'])

    # Spalten ordnen
    display_df = final_df.rename(columns={'obligo_wert': 'Rest-Obligo'})
    
    month_cols = sorted([c for c in display_df.columns if str(c).isdigit()], key=lambda x: int(x))
    cols_order = ['bestellung', 'text'] + month_cols + ['Summe Ist', 'Rest-Obligo', 'Auftragswert (Kalk.)']
    
    final_cols = [c for c in cols_order if c in display_df.columns]
    
    st.dataframe(
        display_df[final_cols].style.format(precision=2, thousands=".", decimal=","),
        height=600,
        use_container_width=True 
    )

else:
    st.info("👈 Bitte wählen Sie ein Projekt aus.")