# SWT-Projekt-Gruppe3

# 🚄 Projekt-Analyse-Cockpit

Ein automatisiertes Controlling-Dashboard zur Plausibilisierung von Projektkosten, Obligos und Budgets (analog "Plausi-Check").

![Status](https://img.shields.io/badge/Status-Produktiv-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tech](https://img.shields.io/badge/Backend-SQLite-lightgrey)

## 📋 Über das Projekt

Dieses Tool ersetzt die manuelle Excel-Verarbeitung von SAP-Finanzdaten. Es liest monatliche Exporte (Ist-Kosten, Obligo, Verträge) ein, speichert sie in einer lokalen Datenbank und visualisiert den aktuellen Finanzstatus pro Projekt und PSP-Element.

**Hauptfunktionen:**

* **Automatisiertes Daten-Mapping:** Verknüpft `CJI3` (Ist) mit `CJI5` (Obligo) über die Bestellnummer.
* **Bestell-Matrix:** Zeigt übersichtlich alle Bestellungen pro Monat.
* **PSP-Drilldown:** Listet detailliert auf, welches PSP-Element (`.01`, `.02`...) wie viel Budget verbraucht.
* **Budget-Überwachung:** Vergleicht Vertragsvolumen (LV) mit der Summe aus Ist-Kosten + Rest-Obligo.
* **Robustheit:** Zeigt auch Bestellungen an, die noch keine Ist-Kosten haben (Full Outer Join), und fängt Datenlücken ab ("Ohne Bestellbezug").

---

## 🚀 Installation & Einrichtung

Voraussetzung: [Python](https://www.python.org/) und [Git](https://git-scm.com/) müssen installiert sein.

### 1. Repository klonen

```bash
git clone [https://github.com/IhrUsername/finance-plausi-tool.git](https://github.com/IhrUsername/finance-plausi-tool.git)
cd finance-plausi-tool
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

* **Frontend:** [Streamlit](https://streamlit.io/) (Interaktives Web-Dashboard)
* **Datenverarbeitung:** [Pandas](https://pandas.pydata.org/) (ETL-Prozesse, Pivotisierung)
* **Datenbank:** [SQLite](https://www.sqlite.org/) (Lokale Datei `finanzdaten.db`)
* **Sprache:** Python 3.10+

## ❓Troubleshooting

**Fehler: "Keine Daten gefunden"**

* Liegen Excel-Dateien im Ordner `data/`?
* Haben Sie das Update-Skript (`start_"".bat oder start_"".ps1`) ausgeführt?

**Fehler: Matrix bleibt leer**

* Prüfen Sie im Tool unten den Punkt "🔍 Rohdaten-Check".
* Wenn dort "0 Datensätze" steht: Prüfen Sie, ob die Dateinamen die korrekten Schlagworte enthalten (siehe Tabelle oben).

**Warnung: "Windows hat den PC geschützt" (beim Start der .bat)**

* Klicken Sie auf "Weitere Informationen" -> "Trotzdem ausführen".

## **Kontakt:** Niklas Finder

**Dokumentation:** Siehe Ordner `/documentation` für das technische IT-Konzept.
