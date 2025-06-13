# Azure SQL → Python Flask → Website

## Voraussetzungen
- Python 3.9 oder neuer inkl. Flask und ODBC
- Zugangsdaten zur Azure SQL-Datenbank

## Setup

1. Eine virtuelle Umgebung anlegen und aktivieren:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Abhängigkeiten installieren:

   ```bash
   pip install -r requirements.txt
   ```

3. Datenbankparameter setzen (z.B. über Umgebungsvariablen):

   ```bash
   export INADB_PASSWORD=<dein_passwort>
   # Optional: DB_SERVER, DB_NAME und DB_USER in app.py anpassen
   ```

4. Die Flask‑Anwendung starten:

   ```bash
   python app.py
   ```

