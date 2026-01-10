# SWT-Projekt-Gruppe3

**Repository:** [https://github.com/yiNk083/SWT-Projekt-Gruppe3](https://github.com/yiNk083/SWT-Projekt-Gruppe3)
*(Hinweis: Dies ist das originale Projekt-Repository.)*

# 🚄 Projekt-Analyse-Cockpit

Ein automatisiertes Controlling-Dashboard zur Plausibilisierung von Projektkosten, Obligos und Budgets (analog "Plausi-Check").

![Status](https://img.shields.io/badge/Status-Produktiv-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tech](https://img.shields.io/badge/Backend-SQLite-lightgrey)

## 📋 Über das Projekt

Dieses Tool ersetzt die manuelle Excel-Verarbeitung von SAP-Finanzdaten. Es liest monatliche Exporte (Ist-Kosten, Obligo, Verträge) ein, speichert sie in einer lokalen Datenbank und visualisiert den aktuellen Finanzstatus pro Projekt und PSP-Element.

**Hauptfunktionen:**

* **Dashboard-Visualisierung:** Interaktive Diagramme für Budgetverläufe und Kostenverteilung (Plotly).
* **Budget-Ampel:** Zeigt sofort, welche PSP-Elemente kritisch sind (Grün/Gelb/Rot).
* **Ist vs. Obligo:** Donut-Chart zur Analyse des Verhältnisses von bezahlten Rechnungen zu offenen Bestellungen.
* **Zeitverlauf:** Analyse der Kostenentwicklung über die Monate (Kumulierte Kurve).
* **Automatisiertes Mapping:** Verknüpft `CJI3` (Ist) mit `CJI5` (Obligo) via Full Outer Join.
* **Bestell-Matrix:** Detaillierte Tabelle aller Bestellungen inkl. "Ohne Bestellbezug".

---

## 🚀 Installation & Einrichtung

Voraussetzung: [Python](https://www.python.org/) und [Git](https://git-scm.com/) müssen installiert sein.

### 1. Repository klonen

```bash
git clone [https://github.com/yiNk083/SWT-Projekt-Gruppe3.git](https://github.com/yiNk083/SWT-Projekt-Gruppe3.git)
cd SWT-Projekt-Gruppe3
```

### 2. Umgebung einrichten (nur beim ersten Mal)

#### Virtuelle Umgebung erstellen

python -m venv .venv

PowerShell für Skripte freischalten (falls nötig)

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

#### Umgebung aktivieren

.\.venv\Scripts\Activate.ps1

#### Abhängigkeiten installieren

pip install -r requirements.txt

## 📂 Daten-Import (Wichtig!)

Aus Datenschutzgründen enthält dieses Repository  **keine Finanzdaten** . Der Ordner `data/` wird von Git ignoriert.

1. Exportieren Sie die aktuellen Daten aus SAP.
2. Legen Sie die Dateien in den Ordner `data/` ab.
3. Die Dateinamen müssen bestimmte Schlagworte enthalten, damit der Importer sie erkennt:

| **Datentyp**         | **Kennung im Dateinamen** | **SAP-Quelle**    |
| -------------------------- | ------------------------------- | ----------------------- |
| **Ist-Kosten**       | `CJI3`                        | Transaktion CJI3        |
| **Obligo**           | `CJI5` *oder* `CNB`       | Transaktion CJI5 / CNB2 |
| **Budget/Verträge** | `LV-Übersicht`               | Export LV-Liste         |
| **Journal**          | `Journal`                     | Detail-Export           |

## ▶️ Nutzung (Täglicher Betrieb)

### Starten (Windows)

Doppelklicken Sie einfach auf die Start-Datei im Hauptordner:
👉 **`start_projektanalyse.bat`** (oder mit Rechtsklick über PowerShell `start_projekt-analyse-cockpit.ps1`)

*Das Skript führt automatisch den Daten-Import durch und öffnet danach den Browser.*

### Manuell Starten (für Entwickler)

**PowerShell**

```
# 1. Datenbank aktualisieren
python src/db_importer.py

# 2. Oberfläche starten
streamlit run src/app.py
```

Das Tool ist erreichbar unter: `http://localhost:8501`

## 🛠️ Technologie-Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Web-Interface)
* **Visualisierung:** [Plotly](https://plotly.com/) (Interaktive Charts & Graphen)
* **Datenverarbeitung:** [Pandas](https://pandas.pydata.org/) (ETL & Berechnung)
* **Datenbank:** [SQLite](https://www.sqlite.org/) (Lokale Speicherung)
* **Monitoring:** [Sentry](https://sentry.io/) (Error Tracking SDK)
* **Sprache:** Python 3.10+

## 🏗️ Projektstruktur

Die Ordnerstruktur trennt sauber zwischen Rohdaten, Quellcode, Tests und Dokumentation:

```
SWT-Projekt-Gruppe3/
├── .venv/              # [Lokal] Virtuelle Python-Umgebung (nicht im Git)
├── data/               # Eingang: Hier liegen die SAP-Exporte (.xlsx/.csv)
├── documentation/      # Projektdokumentation
│   ├── img/            # Screenshots (z.B. Test-Coverage, Dashboard)
│   └── KONZEPT.md      # Detailliertes technisches Konzept
├── src/                # Quellcode (Source)
│   ├── app.py          # Frontend: Das Streamlit-Dashboard
│   ├── db_importer.py  # Backend: ETL-Prozess & Datenbank-Erstellung
│   └── logo.png        # Bilddatei für das UI-Branding
├── tests/              # Qualitätssicherung
│   └── test_logic.py   # Unit-Tests für Logik & Datenbank
├── finanzdaten.db      # [Generiert] Die lokale SQLite-Datenbank
├── README.md           # Diese Anleitung
├── requirements.txt    # Liste aller Python-Abhängigkeiten
└── start_projekt.bat   # One-Click-Starter für Windows-Nutzer (Alternativ über PowerShell)
```

## ❓Troubleshooting

**Fehler: "Keine Daten gefunden"**

* Liegen Excel-Dateien im Ordner `data/`?
* Haben Sie das Update-Skript (`start_"".bat oder start_"".ps1`) ausgeführt?

**Fehler: Matrix bleibt leer**

* Prüfen Sie im Tool unten den Punkt "🔍 Rohdaten-Check".
* Wenn dort "0 Datensätze" steht: Prüfen Sie, ob die Dateinamen die korrekten Schlagworte enthalten (siehe Tabelle oben).

**Warnung: "Windows hat den PC geschützt" (beim Start der .bat)**

* Klicken Sie auf "Weitere Informationen" -> "Trotzdem ausführen".

## ✅ Tests & Qualitätssicherung

Das Projekt setzt auf `pytest` für Unit- und Integrationstests. Wir prüfen dabei kritische Logik (z.B. Währungsumrechnung), Datenbank-Integrität und UI-Stabilität.

**Verfügbare Befehle:**

| Befehl                         | Beschreibung                                                   |
| :----------------------------- | :------------------------------------------------------------- |
| `pytest`                     | Führt alle Tests aus (Logik & DB).                            |
| `pytest -v`                  | Zeigt detaillierte Ergebnisse pro Testfall an (Verbose).       |
| `pytest --cov=src`           | Prüft die Testabdeckung (wie viel % des Codes sind getestet). |
| `pytest tests/test_logic.py` | Führt nur die Logik-Tests aus (schneller Durchlauf).          |

*Der aktuelle Coverage-Report liegt als Screenshot unter `/documentation/img/test_coverage.png`.*

## **Kontakt:** Gruppe 3

* **Rubtsova, Alina**
* **Finder, Niklas Christopher**
* **Nassif, Mohamad Yaman**
* **Kenfack Momo, Olidia Merveille**
* **Beier, Marc**
* **Pinekenstein, Dimitri**

---

**Dokumentation:** Siehe Ordner `/documentation` für das technische IT-Konzept.

## 📄 Lizenz

Dieses Projekt wurde im Rahmen des Moduls "Softwaretechnik-Projekt" erstellt und ist für akademische Zwecke bestimmt.
