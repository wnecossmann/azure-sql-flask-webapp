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

@app.route('/api/weas')
def get_weas():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT WEAID, Bezeichnung FROM WEA ORDER BY Bezeichnung")
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/api/betriebsdaten/<int:wea_id>')
def get_betriebsdaten(wea_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT BetriebsdatenID, Datum, Ertrag_kWh, Betriebsstunden, Stoerung
        FROM WEA_Betriebsdaten
        WHERE WEAID=?
        ORDER BY Datum DESC
    """, (wea_id,))
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/api/betriebsdaten', methods=['POST'])
def post_betriebsdaten():
    data = request.get_json()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO WEA_Betriebsdaten (WEAID, Datum, Ertrag_kWh, Betriebsstunden, Stoerung)
        VALUES (?, ?, ?, ?, ?)
    """, (data['WEAID'], data['Datum'], data['Ertrag_kWh'], data['Betriebsstunden'], data['Stoerung']))
    conn.commit()
    return jsonify({'status': 'success'})

@app.route('/api/betriebsdaten')
def get_betriebsdaten_all():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            s.Bezeichnung AS Standort,
            j.Jahr,
            m.Monat,
            b.KWh_EVU,
            b.Stromeigenverbrauch,
            b.Windmittel,
            b.Grundvergütung,
            b.SDLBonus,
            b.Kosten_Erlös_DV_Euro,
            b.Bemerkungen,
            b.Standort_BetriebsdatenID
        FROM Standort_Betriebsdaten b
        INNER JOIN Standort s ON b.StandortID = s.StandortID
        INNER JOIN Jahr j ON b.JahrID = j.JahrID
        INNER JOIN Monat m ON b.MonatID = m.MonatID
        ORDER BY s.Bezeichnung, j.Jahr DESC, m.MonatID DESC
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    return jsonify(result)


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

@app.route('/betriebsdaten')
def betriebsdaten_html():
    return send_from_directory(app.static_folder, 'betriebsdaten.html')

@app.route('/fonds')
def fonds_html():
    return send_from_directory(app.static_folder, 'fonds.html')

@app.route('/api/update_betriebsdaten', methods=['POST'])
def update_betriebsdaten():
    data = request.get_json()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Standort_Betriebsdaten
            SET KWh_EVU=?, Stromeigenverbrauch=?, Windmittel=?, Grundvergütung=?, SDLBonus=?, Kosten_Erlös_DV_Euro=?, Bemerkungen=?
            WHERE Standort_BetriebsdatenID=?
        """, (
            data.get('KWh_EVU'), data.get('Stromeigenverbrauch'), data.get('Windmittel'),
            data.get('Grundvergütung'), data.get('SDLBonus'), data.get('Kosten_Erlös_DV_Euro'), data.get('Bemerkungen'),
            data.get('Standort_BetriebsdatenID')
        ))
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        return jsonify({'status':'error', 'error':str(e)}), 400

# --- Hilfs-APIs für Auswahlfelder ---
@app.route('/api/standorte')
def standorte():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT StandortID, Bezeichnung FROM Standort ORDER BY Bezeichnung")
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/api/jahre')
def jahre():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT JahrID, Jahr FROM Jahr ORDER BY Jahr DESC")
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/api/monate')
def monate():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT MonatID, Monat FROM Monat ORDER BY MonatID")
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

@app.route('/api/weas/<int:standort_id>')
def weas_by_standort(standort_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.WEAID, w.Bezeichnung 
        FROM WEA w
        INNER JOIN WEA_Standort ws ON ws.WEAID = w.WEAID
        WHERE ws.StandortID = ?
        ORDER BY w.Bezeichnung
    """, (standort_id,))
    return jsonify([dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()])

# --- BDEWEA: Daten anzeigen & speichern ---
@app.route('/api/bdewea', methods=['GET'])
def bdewea_get():
    standort_id = request.args.get('standort_id')
    jahr_id = request.args.get('jahr_id')
    monat_id = request.args.get('monat_id')
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.BDEID, w.WEAID, w.Bezeichnung AS WEA, b.AnlagenMessung, b.geeichteMessung, b.Verfügbarkeit, b.Windmittel, b.Bemerkungen
        FROM BDEWEA b
        INNER JOIN WEA w ON w.WEAID = b.WEAID
        INNER JOIN WEA_Standort ws ON ws.WEAID = w.WEAID
        WHERE ws.StandortID = ? AND b.JahrID = ? AND b.MonatID = ?
        ORDER BY w.Bezeichnung
    """, (standort_id, jahr_id, monat_id))
    columns = [c[0] for c in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])

@app.route('/api/bdewea', methods=['POST'])
def bdewea_save():
    data = request.get_json()
    conn = get_conn()
    cursor = conn.cursor()
    # Prüfen, ob schon Datensatz für (WEA, Jahr, Monat) existiert → UPDATE sonst INSERT
    cursor.execute("""
        SELECT BDEID FROM BDEWEA WHERE WEAID=? AND JahrID=? AND MonatID=?
    """, (data['WEAID'], data['JahrID'], data['MonatID']))
    row = cursor.fetchone()
    if row:
        # Update
        cursor.execute("""
            UPDATE BDEWEA SET AnlagenMessung=?, geeichteMessung=?, Verfügbarkeit=?, Windmittel=?, Bemerkungen=?
            WHERE BDEID=?
        """, (
            data.get('AnlagenMessung'),
            data.get('geeichteMessung'),
            data.get('Verfügbarkeit'),
            data.get('Windmittel'),
            data.get('Bemerkungen'),
            row[0]
        ))
    else:
        # Insert
        cursor.execute("""
            INSERT INTO BDEWEA (WEAID, JahrID, MonatID, AnlagenMessung, geeichteMessung, Verfügbarkeit, Windmittel, Bemerkungen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['WEAID'],
            data['JahrID'],
            data['MonatID'],
            data.get('AnlagenMessung'),
            data.get('geeichteMessung'),
            data.get('Verfügbarkeit'),
            data.get('Windmittel'),
            data.get('Bemerkungen'),
        ))
    conn.commit()
    return jsonify({'status': 'success'})

# --- Beispiel: HTML ausliefern (einfaches Frontend) ---
@app.route('/bdewea')
def bdewea_html():
    return send_from_directory(app.static_folder, 'bdewea.html')


# --- 1. Stammdaten (DropDown-Listen) ---

@app.route("/api/standorte")
def standorte():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT StandortID, Bezeichnung FROM Standort ORDER BY Bezeichnung")
    data = [{"StandortID": x[0], "Bezeichnung": x[1]} for x in cur.fetchall()]
    return jsonify(data)

@app.route("/api/weas/<int:standort_id>")
def weas(standort_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.WEAID, w.Bezeichnung
        FROM WEA w
        INNER JOIN WEA_Standort ws ON ws.WEAID = w.WEAID
        WHERE ws.StandortID = ?
        ORDER BY w.Bezeichnung
    """, standort_id)
    data = [{"WEAID": x[0], "Bezeichnung": x[1]} for x in cur.fetchall()]
    return jsonify(data)

@app.route("/api/jahre")
def jahre():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT JahrID, Jahr FROM Jahr ORDER BY Jahr DESC")
    data = [{"JahrID": x[0], "Jahr": x[1]} for x in cur.fetchall()]
    return jsonify(data)

@app.route("/api/monate")
def monate():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MonatID, Monat FROM Monat ORDER BY MonatID")
    data = [{"MonatID": x[0], "Monat": x[1]} for x in cur.fetchall()]
    return jsonify(data)

# --- 2. Betriebsdaten Standort (kWh EVU) ---

@app.route("/api/standort_betriebsdaten", methods=["GET", "POST"])
def standort_betriebsdaten():
    if request.method == "GET":
        # Für Vorbelegung: suche nach vorhandenem Eintrag
        standort_id = request.args.get("standort_id")
        jahr_id = request.args.get("jahr_id")
        monat_id = request.args.get("monat_id")
        if not (standort_id and jahr_id and monat_id):
            return jsonify({})
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT Standort_BetriebsdatenID, kWh_EVU
            FROM Standort_Betriebsdaten
            WHERE StandortID = ? AND JahrID = ? AND MonatID = ?
        """, (standort_id, jahr_id, monat_id))
        row = cur.fetchone()
        if row:
            return jsonify({"Standort_BetriebsdatenID": row[0], "kWh_EVU": row[1]})
        else:
            return jsonify({})
    elif request.method == "POST":
        # Insert oder Update: falls schon Eintrag, dann Update
        data = request.get_json()
        standort_id = data["StandortID"]
        jahr_id = data["JahrID"]
        monat_id = data["MonatID"]
        kwh_evu = data.get("kWh_EVU")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT Standort_BetriebsdatenID
            FROM Standort_Betriebsdaten
            WHERE StandortID = ? AND JahrID = ? AND MonatID = ?
        """, (standort_id, jahr_id, monat_id))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE Standort_Betriebsdaten SET kWh_EVU = ?
                WHERE Standort_BetriebsdatenID = ?
            """, (kwh_evu, row[0]))
        else:
            cur.execute("""
                INSERT INTO Standort_Betriebsdaten (StandortID, JahrID, MonatID, kWh_EVU)
                VALUES (?, ?, ?, ?)
            """, (standort_id, jahr_id, monat_id, kwh_evu))
        conn.commit()
        return jsonify({"status": "success"})

# --- 3. Betriebsdaten pro WEA (BDEWEA) ---

@app.route("/api/bdewea", methods=["POST"])
def bdewea():
    data = request.get_json()
    wea_id = data["WEAID"]
    jahr_id = data["JahrID"]
    monat_id = data["MonatID"]
    anlagenmessung = data.get("AnlagenMessung")
    geeichte_messung = data.get("geeichteMessung")
    verfuegbarkeit = data.get("Verfügbarkeit")
    windmittel = data.get("Windmittel")
    bemerkungen = data.get("Bemerkungen")
    conn = get_conn()
    cur = conn.cursor()
    # Update falls vorhanden, sonst Insert:
    cur.execute("""
        SELECT BDEID FROM BDEWEA WHERE WEAID = ? AND JahrID = ? AND MonatID = ?
    """, (wea_id, jahr_id, monat_id))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE BDEWEA
            SET AnlagenMessung=?, geeichteMessung=?, Verfügbarkeit=?, Windmittel=?, Bemerkungen=?
            WHERE BDEID=?
        """, (anlagenmessung, geeichte_messung, verfuegbarkeit, windmittel, bemerkungen, row[0]))
    else:
        cur.execute("""
            INSERT INTO BDEWEA (WEAID, JahrID, MonatID, AnlagenMessung, geeichteMessung, Verfügbarkeit, Windmittel, Bemerkungen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (wea_id, jahr_id, monat_id, anlagenmessung, geeichte_messung, verfuegbarkeit, windmittel, bemerkungen))
    conn.commit()
    return jsonify({"status": "success"})

# --- Optional: Alle Einträge anzeigen (Debug/Review) ---

@app.route("/api/bdewea_liste")
def bdewea_liste():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.BDEID, w.Bezeichnung, j.Jahr, m.Monat, b.AnlagenMessung, b.geeichteMessung, b.Verfügbarkeit, b.Windmittel, b.Bemerkungen
        FROM BDEWEA b
        INNER JOIN WEA w ON w.WEAID = b.WEAID
        INNER JOIN Jahr j ON j.JahrID = b.JahrID
        INNER JOIN Monat m ON m.MonatID = b.MonatID
        ORDER BY j.Jahr DESC, m.MonatID DESC, w.Bezeichnung
    """)
    data = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
    return jsonify(data)



if __name__ == '__main__':
    app.run(debug=True)
