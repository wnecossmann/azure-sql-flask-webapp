from flask import Flask, jsonify, send_from_directory
import pyodbc
import os

app = Flask(__name__, static_folder='static')

DB_SERVER = 'wne-test.database.windows.net'
DB_NAME = 'inadb'
DB_USER = 'nimda'
DB_PASSWORD = os.environ.get("INADB_PASSWORD", "wNe2018!")

def get_conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD}"
    )

@app.route('/api/daten')
def daten():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 15 * FROM Person")  # Tabelle Person
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
