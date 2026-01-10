import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.graph_objects as go

# --- KONFIGURATION ---
APP_NAME = "Projekt-Analyse-Cockpit"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🚄")

# Datenbank-Verbindung (Relativer Pfad)
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'finanzdaten.db')
engine = create_engine(f'sqlite:///{db_path}')

# --- HILFSFUNKTIONEN ---

def format_currency(val):
    """Formatiert Zahlen als Euro-Währung (DE-Format)."""
    if pd.isna(val):
        val = 0
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def get_bereich_from_psp(psp):
    """
    Extrahiert den Bereich aus einem PSP-Element für Visualisierungen.
    Beispiel: 'G.011803001.02.02' -> '.02'
    """
    if not isinstance(psp, str):
        return "Unbekannt"
    parts = psp.split('.')
    if len(parts) >= 3:
        return f".{parts[2]}" 
    return psp

# --- UI: SEITENLEISTE ---

logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)

st.sidebar.header("Filter & Navigation")

# Projekt-Auswahl laden
# Wir nutzen die performante SQL-Abfrage auf die 'hauptprojekt'-Spalte
try:
    query_all = """
    SELECT DISTINCT hauptprojekt FROM ist_kosten WHERE hauptprojekt IS NOT NULL
    UNION
    SELECT DISTINCT hauptprojekt FROM obligo_cji5 WHERE hauptprojekt IS NOT NULL
    """
    df_projects = pd.read_sql(query_all, engine)
    
    if not df_projects.empty:
        all_projects = sorted(df_projects['hauptprojekt'].dropna().unique().tolist())
    else:
        all_projects = []

except Exception as e:
    st.sidebar.error(f"Datenbank nicht gefunden oder leer. Bitte Import starten.")
    all_projects = []

if all_projects:
    selected_project = st.sidebar.selectbox("Projekt wählen:", all_projects)
else:
    st.sidebar.warning("Keine Projekte verfügbar.")
    selected_project = None

# --- UI: HAUPTBEREICH ---

st.title(f"🚄 {APP_NAME}")

if selected_project:
    st.markdown(f"### Analyse für Projekt: `{selected_project}`")

    # 1. DATENABRUF (SQL)
    # -------------------
    # Wir filtern direkt in der Datenbank, um Performance zu sparen.
    
    # Ist-Kosten
    query_ist = f"""
    SELECT objekt as psp, einkaufsbeleg as bestellung, bezeichnung as text, "wert/bwähr" as wert, periode
    FROM ist_kosten 
    WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
    """
    df_ist = pd.read_sql(query_ist, engine)

    # Obligo (mit Fallback, falls Bezeichnungen fehlen)
    try:
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, bezeichnung as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 
        WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
        """
        df_obligo = pd.read_sql(query_obligo, engine)
    except:
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, '' as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 
        WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
        """
        df_obligo = pd.read_sql(query_obligo, engine)

    # Budget / Verträge
    try:
        query_budget = f"""
        SELECT betrag, bezeichnung, "planungelement" as psp_budget
        FROM vertraege_uebersicht 
        WHERE "planungelement" LIKE '%{selected_project}%' OR "projektnummer" LIKE '%{selected_project}%'
        """
        df_budget = pd.read_sql(query_budget, engine)
    except:
        df_budget = pd.DataFrame()

    # Typ-Konvertierung zur Sicherheit
    if not df_ist.empty: df_ist['wert'] = pd.to_numeric(df_ist['wert'], errors='coerce').fillna(0)
    if not df_obligo.empty: df_obligo['obligo_wert'] = pd.to_numeric(df_obligo['obligo_wert'], errors='coerce').fillna(0)
    if not df_budget.empty: df_budget['betrag'] = pd.to_numeric(df_budget['betrag'], errors='coerce').fillna(0)

    # 2. KPI BERECHNUNG
    # -----------------
    total_ist = df_ist['wert'].sum()
    total_obligo = df_obligo['obligo_wert'].sum()
    total_budget = df_budget['betrag'].sum()
    verfuegbar = total_budget - (total_ist + total_obligo)

    # Anzeige KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gesamt-Budget", format_currency(total_budget))
    c2.metric("Ist-Kosten", format_currency(total_ist))
    c3.metric("Obligo", format_currency(total_obligo))
    c4.metric("Verfügbar", format_currency(verfuegbar), 
              delta="Achtung" if verfuegbar < 0 else "OK", 
              delta_color="inverse" if verfuegbar < 0 else "normal")

    st.divider()

    # 3. DETAILS & CHARTS
    # -------------------
    
    # 3a. PSP Tabelle
    st.subheader("📑 PSP-Elemente im Projekt")
    
    # Aggregation
    psp_ist = df_ist.groupby('psp')['wert'].sum().reset_index() if not df_ist.empty else pd.DataFrame(columns=['psp', 'wert'])
    psp_obligo = df_obligo.groupby('psp')['obligo_wert'].sum().reset_index() if not df_obligo.empty else pd.DataFrame(columns=['psp', 'obligo_wert'])
    
    df_psp_stats = pd.merge(psp_ist, psp_obligo, on='psp', how='outer').fillna(0)
    df_psp_stats['Gesamtaufwand'] = df_psp_stats['wert'] + df_psp_stats['obligo_wert']
    
    if not df_psp_stats.empty:
        st.dataframe(
            df_psp_stats.rename(columns={'wert': 'Ist', 'obligo_wert': 'Obligo'}).style.format("{:,.2f}"),
            use_container_width=True
        )
    else:
        st.info("Keine Detail-Daten verfügbar.")

    st.divider()

    # 3b. Ampel-Chart (Budget vs. Kosten pro PSP)
    st.subheader("🚥 Budget-Ampel pro PSP-Element")
    if not df_psp_stats.empty and total_budget > 0:
        df_ampel = df_psp_stats.copy()
        df_ampel['Auslastung %'] = (df_ampel['Gesamtaufwand'] / total_budget * 100)
        df_ampel = df_ampel.sort_values('Auslastung %', ascending=False)
        
        def get_color(prozent):
            if prozent > 100: return '#d32f2f'  # Rot
            elif prozent > 80: return '#ffa726'  # Orange
            else: return '#66bb6a'  # Grün
            
        fig = go.Figure(go.Bar(
            y=df_ampel['psp'], x=df_ampel['Auslastung %'], orientation='h',
            marker=dict(color=df_ampel['Auslastung %'].apply(get_color)),
            text=df_ampel['Auslastung %'].apply(lambda x: f"{x:.1f}%"), textposition='outside'
        ))
        fig.add_vline(x=100, line_dash="dash", line_color="red")
        fig.update_layout(height=max(300, len(df_ampel)*50), xaxis_title="Auslastung (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    # 3c. Zeitverlauf
    st.subheader("📈 Kostenentwicklung")
    if not df_ist.empty and 'periode' in df_ist.columns:
        df_time = df_ist.groupby('periode')['wert'].sum().reset_index()
        df_time['periode_num'] = pd.to_numeric(df_time['periode'], errors='coerce')
        df_time = df_time.sort_values('periode_num')
        df_time['Kumuliert'] = df_time['wert'].cumsum()
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_time['periode'], y=df_time['wert'], name='Monat'))
        fig2.add_trace(go.Scatter(x=df_time['periode'], y=df_time['Kumuliert'], name='Kumuliert', yaxis='y2'))
        fig2.update_layout(yaxis2=dict(overlaying='y', side='right'), hovermode='x unified')
        st.plotly_chart(fig2, use_container_width=True)

    # 3d. Matrix (Bestellungen)
    st.subheader("📋 Bestell-Matrix")
    if not df_ist.empty:
        # Datenvorbereitung für Pivot
        df_ist['bestellung'] = df_ist['bestellung'].fillna('').astype(str).str.strip().replace(['', 'nan', 'None'], 'Sonstiges')
        pivot = df_ist.pivot_table(index='bestellung', columns='periode', values='wert', aggfunc='sum', fill_value=0)
        pivot['Summe Ist'] = pivot.sum(axis=1)
        pivot = pivot.reset_index()
        
        # Merge mit Obligo
        if not df_obligo.empty:
            df_obligo['bestellung'] = df_obligo['bestellung'].fillna('').astype(str).str.strip()
            obl_grp = df_obligo.groupby('bestellung')['obligo_wert'].sum().reset_index()
            final = pd.merge(pivot, obl_grp, on='bestellung', how='outer').fillna(0)
        else:
            final = pivot
            final['obligo_wert'] = 0
            
        final['Gesamt'] = final['Summe Ist'] + final['obligo_wert']
        st.dataframe(final.style.format("{:,.2f}"), use_container_width=True)

else:
    st.info("Bitte wählen Sie links ein Projekt aus.")