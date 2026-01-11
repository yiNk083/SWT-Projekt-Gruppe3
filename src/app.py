import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import plotly.graph_objects as go
import sentry_sdk 

# --- SENTRY MONITORING ---
# Für Abgabe via ZIP ist der Key hardcodiert
sentry_sdk.init(
    dsn="https://b9a777fa97d28f7260385b4052a44486@o4510688530137088.ingest.de.sentry.io/4510688535576656",
    traces_sample_rate=1.0, # Erfasst 100% der Transaktionen für Debugging
)

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

def get_bereich_from_psp(psp):
    """Extrahiert den Bereich (z.B. .01, .02) aus PSP für die Charts"""
    if not isinstance(psp, str):
        return "Unbekannt"
    parts = psp.split('.')
    if len(parts) >= 3:
        return f".{parts[2]}"  # z.B. .01, .02, .03
    return psp

# --- SEITENLEISTE ---

logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)

st.sidebar.header("Filter & Navigation")

# 1. Projekt-Liste laden (NEU: Nutzt die optimierte Spalte 'hauptprojekt')
try:
    # Wir laden direkt die Hauptprojekte aus der DB
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
    st.sidebar.error(f"Datenbank-Fehler (bitte Importer prüfen): {e}")
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
    # 1. DATEN LADEN (NEU: Filtert auf Hauptprojekt)
    # ---------------------------------------------------------
    
    # A) IST-KOSTEN
    # Wir suchen exakt nach dem Hauptprojekt oder allem was damit anfängt
    query_ist = f"""
    SELECT objekt as psp, einkaufsbeleg as bestellung, bezeichnung as text, "wert/bwähr" as wert, periode
    FROM ist_kosten 
    WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
    """
    df_ist = pd.read_sql(query_ist, engine)

    # B) OBLIGO
    try:
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, bezeichnung as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 
        WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
        """
        df_obligo = pd.read_sql(query_obligo, engine)
    except:
        # Fallback falls Bezeichnung fehlt
        query_obligo = f"""
        SELECT objekt as psp, "nr_referenzbeleg" as bestellung, '' as text_obligo, "wert/bwähr" as obligo_wert
        FROM obligo_cji5 
        WHERE hauptprojekt = '{selected_project}' OR objekt LIKE '{selected_project}%'
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
    # 2. KEINE BEREINIGUNG MEHR NÖTIG
    # ---------------------------------------------------------
    # Da der Importer jetzt Floats liefert, müssen wir hier nichts mehr cleansen.
    # Zur Sicherheit stellen wir nur sicher, dass es Zahlen sind (falls DB leer war)
    
    if not df_ist.empty:
        df_ist['wert'] = pd.to_numeric(df_ist['wert'], errors='coerce').fillna(0)
    
    if not df_obligo.empty:
        df_obligo['obligo_wert'] = pd.to_numeric(df_obligo['obligo_wert'], errors='coerce').fillna(0)
    
    if not df_budget.empty:
        df_budget['betrag'] = pd.to_numeric(df_budget['betrag'], errors='coerce').fillna(0)

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
    # 4. PSP-STRUKTUR ÜBERSICHT
    # ---------------------------------------------------------
    st.subheader("📑 PSP-Elemente im Projekt")
    
    # Aggregation
    if not df_ist.empty:
        psp_ist = df_ist.groupby('psp')['wert'].sum().reset_index()
    else:
        psp_ist = pd.DataFrame(columns=['psp', 'wert'])
        
    if not df_obligo.empty:
        psp_obligo = df_obligo.groupby('psp')['obligo_wert'].sum().reset_index()
    else:
        psp_obligo = pd.DataFrame(columns=['psp', 'obligo_wert'])

    # Merge
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
    # 5. DIAGRAMME & VISUALISIERUNGEN
    # ---------------------------------------------------------

    # 5A. BUDGET-AMPEL
    st.subheader("🚥 Budget-Ampel pro PSP-Element")
    
    if not df_psp_stats.empty and total_budget > 0:
        df_ampel = df_psp_stats.copy()
        df_ampel['Auslastung %'] = (df_ampel['Gesamtaufwand'] / total_budget * 100)
        df_ampel = df_ampel.sort_values('Auslastung %', ascending=False)
        
        def get_color(prozent):
            if prozent > 100: return '#d32f2f'  # Rot
            elif prozent > 80: return '#ffa726'  # Orange
            else: return '#66bb6a'  # Grün
        
        df_ampel['color'] = df_ampel['Auslastung %'].apply(get_color)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_ampel['psp'],
            x=df_ampel['Auslastung %'],
            orientation='h',
            marker=dict(color=df_ampel['color']),
            text=df_ampel['Auslastung %'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))
        
        fig.add_vline(x=100, line_dash="dash", line_color="red")
        fig.update_layout(title="Budget-Auslastung", height=max(300, len(df_ampel) * 50))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Budget-Daten für Ampel verfügbar (oder Budget ist 0).")

    st.divider()

    # 5B. ZEITVERLAUF
    st.subheader("📈 Kostenentwicklung über Zeit")
    
    if not df_ist.empty and 'periode' in df_ist.columns:
        df_timeline = df_ist.groupby('periode')['wert'].sum().reset_index()
        df_timeline['periode_num'] = pd.to_numeric(df_timeline['periode'], errors='coerce')
        df_timeline = df_timeline.sort_values('periode_num')
        df_timeline['Kumuliert'] = df_timeline['wert'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_timeline['periode'], y=df_timeline['wert'], name='Monatlich', marker_color='lightblue'))
        fig.add_trace(go.Scatter(x=df_timeline['periode'], y=df_timeline['Kumuliert'], name='Kumuliert', line=dict(color='darkblue', width=3), yaxis='y2'))
        
        fig.update_layout(
            yaxis=dict(title="Monatlich (€)"),
            yaxis2=dict(title="Kumuliert (€)", overlaying='y', side='right'),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Zeitverlaufsdaten verfügbar.")

    st.divider()

    # 5C. IST VS OBLIGO
    st.subheader("⚖️ Ist vs. Obligo")
    if total_ist > 0 or total_obligo > 0:
        fig = go.Figure(data=[go.Pie(
            labels=['Ist (Bezahlt)', 'Obligo (Offen)'], 
            values=[total_ist, total_obligo], 
            hole=0.4,
            marker=dict(colors=['#1f77b4', '#ff7f0e'])
        )])
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 5D. KOSTENVERTEILUNG PRO BEREICH
    st.subheader("📊 Kostenverteilung pro PSP-Bereich")
    if not df_psp_stats.empty:
        df_psp_viz = df_psp_stats.copy()
        df_psp_viz['bereich'] = df_psp_viz['psp'].apply(get_bereich_from_psp)
        
        df_bereiche = df_psp_viz.groupby('bereich').agg({'wert': 'sum', 'obligo_wert': 'sum'}).reset_index()
        df_bereiche['Gesamt'] = df_bereiche['wert'] + df_bereiche['obligo_wert']
        df_bereiche = df_bereiche.sort_values('Gesamt')

        fig = go.Figure()
        fig.add_trace(go.Bar(y=df_bereiche['bereich'], x=df_bereiche['wert'], name='Ist', orientation='h', marker_color='#1f77b4'))
        fig.add_trace(go.Bar(y=df_bereiche['bereich'], x=df_bereiche['obligo_wert'], name='Obligo', orientation='h', marker_color='#ff7f0e'))
        
        fig.update_layout(barmode='stack', title="Kosten pro Bereich", height=max(300, len(df_bereiche) * 60))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # 6. MATRIX (ZUSAMMENGEFASST)
    # ---------------------------------------------------------
    st.subheader("📋 Bestell-Matrix (Zusammengefasst)")

    if not df_ist.empty:
        # Daten vorbereiten
        df_ist['bestellung'] = df_ist['bestellung'].fillna('').astype(str).str.strip().replace(['', 'nan', 'None'], 'Sonstiges / Ohne Bestellung')
        df_ist['text'] = df_ist['text'].fillna('Unbekannt')

        # Pivot Tabelle
        pivot_ist = df_ist.pivot_table(index='bestellung', columns='periode', values='wert', aggfunc='sum', fill_value=0)
        pivot_ist['Summe Ist'] = pivot_ist.sum(axis=1)
        pivot_ist = pivot_ist.reset_index()
        
        # Text mapping
        text_map = df_ist.groupby('bestellung')['text'].first()
        pivot_ist['text'] = pivot_ist['bestellung'].map(text_map)
        
        # Obligo dazu holen
        if not df_obligo.empty:
            df_obligo['bestellung'] = df_obligo['bestellung'].fillna('').astype(str).str.strip()
            grp_obligo = df_obligo.groupby('bestellung').agg({'obligo_wert': 'sum', 'text_obligo': 'first'}).reset_index()
        else:
            grp_obligo = pd.DataFrame(columns=['bestellung', 'obligo_wert', 'text_obligo'])

        # Merge
        final_df = pd.merge(pivot_ist, grp_obligo, on='bestellung', how='outer')
        final_df = final_df.fillna(0)
        
        # Text korrigieren (Falls Ist leer war, nimm Obligo-Text)
        if 'text' not in final_df.columns: final_df['text'] = ""
        # Wir müssen sicherstellen, dass 'text_obligo' existiert bevor wir darauf zugreifen
        if 'text_obligo' in final_df.columns:
             # Einfacher Weg: Wenn Text 0 oder leer ist, nimm text_obligo
             final_df['text'] = final_df.apply(lambda row: row['text_obligo'] if (row['text'] == 0 or row['text'] == "") else row['text'], axis=1)

        # Auftragswert
        final_df['Auftragswert (Kalk.)'] = final_df['Summe Ist'] + final_df['obligo_wert']

        # Sortieren ("Sonstiges" nach unten)
        final_df['sort_helper'] = final_df['bestellung'].apply(lambda x: 'ZZZ' if 'Sonstiges' in x else x)
        final_df = final_df.sort_values('sort_helper').drop(columns=['sort_helper'])

        # Spalten für Anzeige
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
        st.info("Bitte wählen Sie ein Projekt aus (oder keine Daten vorhanden).")

else:
    st.info("👈 Bitte wählen Sie ein Projekt in der Seitenleiste aus.")