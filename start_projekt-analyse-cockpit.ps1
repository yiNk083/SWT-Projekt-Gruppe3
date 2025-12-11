Write-Host "================================================" -ForegroundColor Green
Write-Host "   Projekt-Analyse-Cockpit wird gestartet..."
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# 1. Importer laufen lassen
Write-Host "1. Aktualisiere Datenbank..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" src\db_importer.py

# 2. App starten
Write-Host ""
Write-Host "2. Starte Web-Oberfläche..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m streamlit run src/app.py

# Damit das Fenster offen bleibt, falls ein Fehler passiert
Read-Host -Prompt "Drücken Sie Enter zum Beenden"