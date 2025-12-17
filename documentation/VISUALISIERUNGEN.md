# Dokumentation: Datenvisualisierungen im Projekt-Analyse-Cockpit

## Überblick

Das Projekt-Analyse-Cockpit wurde um mehrere interaktive Visualisierungen erweitert, die eine umfassende Analyse der Projektfinanzen ermöglichen. Diese Visualisierungen basieren auf dem Framework Plotly für Python und sind in die bestehende Streamlit-Anwendung integriert.

---

## 1. Budget-Ampel pro PSP-Element

### Zweck

Die Budget-Ampel visualisiert die prozentuale Auslastung des Budgets für jedes PSP-Element und ermöglicht eine schnelle Identifikation kritischer Bereiche.

### Funktionsweise

- **Datengrundlage**: Gesamtaufwand (Ist-Kosten + Obligo) pro PSP-Element wird ins Verhältnis zum Gesamtbudget gesetzt
- **Farbcodierung**:
  - Grün: Auslastung unter 80% (im Rahmen)
  - Orange: Auslastung zwischen 80% und 100% (Warnung)
  - Rot: Auslastung über 100% (Budget überschritten)
- **Schwellwertlinien**: Vertikale gestrichelte Linien markieren die 80%- und 100%-Schwellen zur besseren Orientierung

### Technische Implementation

```python
# Berechnung der Auslastung in Prozent
df_ampel['Auslastung %'] = (df_ampel['Gesamtaufwand'] / total_budget * 100)

# Farbzuweisung basierend auf Schwellwerten
def get_color(prozent):
    if prozent > 100:
        return '#d32f2f'  # Rot
    elif prozent > 80:
        return '#ffa726'  # Orange
    else:
        return '#66bb6a'  # Grün
```

### Ausgabe

- Horizontales Balkendiagramm mit prozentualer Auslastung
- Zusammenfassung: Anzahl der PSP-Elemente in jeder Kategorie (kritisch/Warnung/ok)

---

## 2. Kostenentwicklung über Zeit

### Zweck

Visualisiert die zeitliche Entwicklung der Ist-Kosten und zeigt sowohl monatliche als auch kumulative Werte.

### Funktionsweise

- **Monatliche Kosten**: Dargestellt als Balkendiagramm (primäre Y-Achse)
- **Kumulative Kosten**: Dargestellt als Linie (sekundäre Y-Achse)
- **Datenvorbereitung**: Perioden werden numerisch sortiert, um eine chronologisch korrekte Darstellung zu gewährleisten

### Technische Implementation

```python
# Sortierung nach Periode
df_timeline['periode_num'] = pd.to_numeric(df_timeline['periode'], errors='coerce')
df_timeline = df_timeline.sort_values('periode_num')

# Berechnung kumulativer Werte
df_timeline['Kumuliert'] = df_timeline['wert'].cumsum()

# Dual-Achsen-Chart
fig.add_trace(go.Bar(..., yaxis='y'))  # Monatlich
fig.add_trace(go.Scatter(..., yaxis='y2'))  # Kumuliert
```

### Ausgabe

- Kombiniertes Balken-Linien-Diagramm
- Identifikation des teuersten Monats
- Anzeige der Gesamtsumme (kumuliert)

---

## 3. Ist vs. Obligo Verhältnis

### Zweck

Zeigt die Verteilung zwischen bereits bezahlten Kosten (Ist) und noch offenen Verpflichtungen (Obligo).

### Funktionsweise

- **Donut-Chart**: Ringdiagramm mit zentralem Loch für moderne Optik
- **Prozentuale Aufteilung**: Automatische Berechnung der Anteile
- **Farbcodierung**:
  - Blau: Ist-Kosten
  - Orange: Obligo

### Technische Implementation

```python
# Datenaufbereitung
labels = ['Bereits bezahlt (Ist)', 'Noch offen (Obligo)']
values = [total_ist, total_obligo]

# Donut-Chart mit hole-Parameter
fig = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    hole=0.4,  # 40% Loch in der Mitte
    marker=dict(colors=colors)
)])
```

### Ausgabe

- Donut-Chart mit Prozentangaben
- Metriken für jeden Bereich (Ist/Obligo/Gesamt) mit Prozentanzeige

---

## 4. Kostenverteilung pro PSP-Bereich

### Zweck

Aggregiert PSP-Elemente nach Bereichen (z.B. .01, .02, .03) und zeigt die Kostenverteilung in einem gestapelten Balkendiagramm.

### Funktionsweise

- **Bereichsextraktion**: PSP-Elemente werden auf die Bereichsebene reduziert
  - Beispiel: G.011803005.01.03 wird zu .01
- **Aggregation**: Summierung aller Ist-Kosten und Obligo-Werte pro Bereich
- **Gestapelte Darstellung**: Ist-Kosten (blau) und Obligo (orange) werden übereinander dargestellt

### Technische Implementation

```python
# Extraktion des Bereichs aus PSP-String
def extract_bereich(psp):
    parts = psp.split('.')
    if len(parts) >= 3:
        return f".{parts[2]}"
    return psp

# Gruppierung und Aggregation
df_bereiche = df_psp_viz.groupby('bereich').agg({
    'wert': 'sum',
    'obligo_wert': 'sum',
    'Gesamtaufwand': 'sum'
}).reset_index()

# Gestapeltes Balkendiagramm
fig.update_layout(barmode='stack')
```

### Ausgabe

- Horizontales gestapeltes Balkendiagramm
- Top 3 teuerste Bereiche mit Prozentanteil am Gesamtaufwand
- Hover-Informationen mit detaillierten Beträgen

---

## Technologie-Stack

### Verwendete Bibliotheken

- **Plotly**: Interaktive Visualisierungen mit umfangreichen Anpassungsmöglichkeiten
- **Pandas**: Datenmanipulation und -aggregation
- **Streamlit**: Web-Framework für die Darstellung

### Vorteile von Plotly

- Interaktivität: Zoom, Pan, Hover-Informationen
- Responsive Design: Automatische Anpassung an Bildschirmgröße
- Export-Funktionen: Charts können als PNG heruntergeladen werden
- Professionelle Optik: Produktionsreife Visualisierungen ohne zusätzliches Styling

---

## Design-Prinzipien

### Farbschema

- **Konsistenz**: Durchgängige Verwendung von Blau für Ist-Kosten und Orange für Obligo
- **Ampelfarben**: Grün/Orange/Rot für Status-Visualisierungen
- **Barrierefreiheit**: Ausreichender Kontrast für gute Lesbarkeit

### Layout

- **Responsive Höhe**: Diagramme passen sich dynamisch an die Anzahl der Datenpunkte an
  ```python
  height = max(300, len(df) * 60)  # Mindestens 300px, sonst 60px pro Zeile
  ```
- **Einheitliche Struktur**: Jede Visualisierung folgt dem Schema: Diagramm → Insights → Divider

### Interaktivität

- **Hover-Informationen**: Detaillierte Daten bei Mausüberfahrung
- **Kategoriale Achsen**: Korrekte Sortierung und Darstellung von Text-Labels
- **Unified Hover**: Bei Multi-Trace-Charts werden alle relevanten Werte gleichzeitig angezeigt

---

## Datenfluss

### 1. Datenbeschaffung

```
Datenbank (SQLite) → SQL-Abfragen → Pandas DataFrames
```

### 2. Datenverarbeitung

```
Rohdaten → Bereinigung (clean_number) → Aggregation → Visualisierung
```

### 3. Typische Transformationen

- Umwandlung von Text-Zahlen (z.B. "1.000,00") in numerische Werte
- Gruppierung nach PSP-Elementen oder Perioden
- Berechnung abgeleiteter Werte (Gesamtaufwand, Prozentanteile)

---

## Performance-Optimierungen

### Effiziente Datenverarbeitung

- Verwendung von Pandas-Gruppierungen statt Schleifen
- Vektorisierte Operationen für Berechnungen
- Lazy Evaluation bei bedingten Visualisierungen

### Beispiel: Bedingte Visualisierung

```python
if not df_psp_stats.empty and total_budget > 0:
    # Visualisierung wird nur erstellt wenn Daten vorhanden
```

---

## Fehlerbehandlung

### Robustheit

- Prüfung auf leere DataFrames vor Visualisierung
- Fallback-Nachrichten bei fehlenden Daten
- Numerische Konvertierung mit error='coerce' für fehlerhafte Daten

### Beispiel

```python
df_timeline['periode_num'] = pd.to_numeric(df_timeline['periode'], errors='coerce')
df_timeline = df_timeline.dropna(subset=['periode_num'])  # Ungültige Einträge entfernen
```

---

## Wartung und Erweiterung

### Code-Struktur

Jede Visualisierung ist in einem eigenständigen Block organisiert:

1. Überschrift mit `st.subheader()`
2. Datenprüfung und -vorbereitung
3. Chart-Erstellung mit Plotly
4. Darstellung mit `st.plotly_chart()`
5. Zusätzliche Insights oder Metriken
6. Abschluss mit `st.divider()`

### Erweiterungsmöglichkeiten

- Hinzufügen weiterer Aggregationsebenen
- Export-Funktionen für Charts
- Filteroptionen für Zeiträume
- Vergleich zwischen Projekten

---

## Literatur und Referenzen

- Plotly (2024): Plotly Python Documentation
- Streamlit (2024): Streamlit Documentation
- McKinney, W. (2022): Python for Data Analysis

---

**Version**: 1.0  
**Datum**: Dezember 2025  
**Entwicklungsumgebung**: Python 3.9, Streamlit 1.x, Plotly 5.x
