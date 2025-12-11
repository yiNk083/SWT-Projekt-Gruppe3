@echo off
echo =============================================
echo   Projekt-Analyse-Cockpit wird gestartet...
echo =============================================
echo.

echo 1. Suche nach neuen Dateien und aktualisiere Datenbank...
.\.venv\Scripts\python.exe src\db_importer.py

echo.
echo 2. Starte die Benutzeroberfläche...
.\.venv\Scripts\python.exe -m streamlit run src/app.py

pause