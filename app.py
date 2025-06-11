from flask import Flask, jsonify, request, send_from_directory
import pyodbc
import os

app = Flask(__name__, static_folder='static')

DB_SERVER = 'wne.database.windows.net'
DB_NAME = 'inadb'
DB_USER = 'nimda'
DB_PASSWORD = os.environ.get("INADB_PASSWORD", "wNe2018!")

def get_conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER};DATABASE={DB_NAME};"
        f"UID={DB_USER};PWD={DB_PASSWORD}"
    )

@app.route('/api/daten')
def daten():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.PersonID, a.Name, a.Vorname, p.Geburtstag, p.Beruf, p.Mail, p.Telefon, 
               a.Straße, a.PLZ, a.Ort
        FROM Person p
        INNER JOIN [Anschrift_Person] ap ON p.PersonID = ap.PersonID
        INNER JOIN Anschrift a ON ap.AnschriftID = a.AnschriftID
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result)

@app.route('/api/update_person', methods=['POST'])
def update_person():
    data = request.get_json()
    person_id = data.get('PersonID')
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Person
            SET Geburtstag=?, Beruf=?, Mail=?, Telefon=?
            WHERE PersonID=?
        """, (data.get('Geburtstag'), data.get('Beruf'), data.get('Mail'), data.get('Telefon'), person_id))

        cursor.execute("""
            UPDATE Anschrift SET Name=?, Vorname=?, Straße=?, PLZ=?, Ort=?
            WHERE AnschriftID=(
                SELECT AnschriftID FROM [Anschrift_Person] WHERE PersonID=?
            )
        """, (data.get('Name'), data.get('Vorname'), data.get('Straße'), data.get('PLZ'), data.get('Ort'), person_id))

        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ausschuettungen')
def ausschuettungen():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fa.ID, j.Jahr, fa.AusschuettungSoll, fa.Ausschuettung, fa.Auszahlung
        FROM Fonds_Ausschuettung fa
        INNER JOIN Jahr j ON fa.JahrID = j.JahrID
        ORDER BY j.Jahr DESC
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result)

@app.route('/api/update_ausschuettung', methods=['POST'])
def update_ausschuettung():
    data = request.get_json()
    aussch_id = data.get('ID')
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Fonds_Ausschuettung
            SET AusschuettungSoll=?, Ausschuettung=?, Auszahlung=?
            WHERE ID=?
        """, (data.get('AusschuettungSoll'), data.get('Ausschuettung'), data.get('Auszahlung'), aussch_id))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/ausschuettungen')
def aussch_html():
    return send_from_directory(app.static_folder, 'ausschuettungen.html')

@app.route('/api/komplementaere')
def komplementaere():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Name FROM Komplementär ORDER BY Name")
    result = [row[0] for row in cursor.fetchall()]
    return jsonify(result)

@app.route('/api/ausschuettungen/<komplementaer>')
def aussch_by_komplementaer(komplementaer):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.Jahr, fa.AusschuettungSoll, fa.Ausschuettung, fa.Auszahlung
        FROM Fonds_Ausschuettung fa
        INNER JOIN Jahr j ON fa.JahrID = j.JahrID
        INNER JOIN Fonds f ON fa.FondsID = f.FondsID
        INNER JOIN Fonds_Komplementär fk ON f.FondsID = fk.FondsID
        INNER JOIN Komplementär k ON fk.KomplementärID = k.KomplementärID
        WHERE k.Name=?
        ORDER BY j.Jahr DESC
    """, (komplementaer,))
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result)

@app.route('/personen')
def personen_html():
    return send_from_directory(app.static_folder, 'person.html')

@app.route('/api/fonds')
def fonds_list():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.FondsID, f.Name, f.Kurz, f.Inbetriebnahme, f.Investitionsvolumen, k.Name AS Komplementär
        FROM Fonds f
        LEFT JOIN Fonds_Komplementär fk ON f.FondsID = fk.FondsID
        LEFT JOIN Komplementär k ON fk.KomplementärID = k.KomplementärID
        ORDER BY f.Name
    """)
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/fonds')
def fonds_html():
    return send_from_directory(app.static_folder, 'fonds.html')





if __name__ == '__main__':
    app.run(debug=True)
