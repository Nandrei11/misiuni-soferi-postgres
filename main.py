import os
import psycopg2
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024_postgres'

print("🚀 Aplicația a pornit! Testez conexiunea PostgreSQL...")

# Testează conexiunea la PostgreSQL
def test_postgresql():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL nu este setat")
            return False
            
        print("🔗 Încerc conexiunea la PostgreSQL...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Testează conexiunea
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Conectat la PostgreSQL: {version[0]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Eroare conexiune PostgreSQL: {e}")
        return False

# Funcție pentru conexiune la baza de date
def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL nu este setat!")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        return None

# Inițializare bază de date
def init_db():
    conn = get_db_connection()
    if not conn:
        print("⚠️  Nu pot inițializa baza de date - folosesc modul demo")
        return False
        
    try:
        cur = conn.cursor()
        
        # Tabela șoferi
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id VARCHAR(50) PRIMARY KEY,
                nume VARCHAR(100) NOT NULL,
                prenume VARCHAR(100) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        
        # Tabela vehicule
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id VARCHAR(50) PRIMARY KEY,
                tip VARCHAR(100) NOT NULL,
                nr_inmatriculare VARCHAR(20) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        
        # Tabela misiuni
        cur.execute('''
            CREATE TABLE IF NOT EXISTS missions (
                id VARCHAR(50) PRIMARY KEY,
                sofer_id VARCHAR(50) NOT NULL,
                vehicle_id VARCHAR(50) NOT NULL,
                data_inceput DATE NOT NULL,
                data_sfarsit DATE NOT NULL,
                destinatie TEXT NOT NULL,
                distanta INTEGER NOT NULL,
                persoana_contact TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP
            )
        ''')
        
        # Tabela admin
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL
            )
        ''')
        
        # Verifică dacă există deja date
        cur.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            # Inserează admin
            cur.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")
            
            # Șoferi inițiali
            drivers_data = [
                ('sofer001', 'Popescu', 'Ion'),
                ('sofer002', 'Ionescu', 'Vasile')
            ]
            for driver_id, nume, prenume in drivers_data:
                cur.execute(
                    "INSERT INTO drivers (id, nume, prenume, created_at) VALUES (%s, %s, %s, %s)",
                    (driver_id, nume, prenume, datetime.now())
                )
            
            # Vehicule inițiale
            vehicles_data = [
                ('vehicle001', 'Duba', 'B-123-ABC'),
                ('vehicle002', 'Camion', 'B-456-DEF')
            ]
            for vehicle_id, tip, nr_inmatriculare in vehicles_data:
                cur.execute(
                    "INSERT INTO vehicles (id, tip, nr_inmatriculare, created_at) VALUES (%s, %s, %s, %s)",
                    (vehicle_id, tip, nr_inmatriculare, datetime.now())
                )
            
            print("✅ Date inițiale inserate în PostgreSQL!")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Baza de date PostgreSQL inițializată cu succes!")
        return True
        
    except Exception as e:
        print(f"❌ Eroare la inițializarea bazei de date: {e}")
        return False

# Testează conexiunea la start
postgresql_working = test_postgresql()
if postgresql_working:
    init_db()
else:
    print("⚠️  Aplicația rulează în modul demo fără PostgreSQL")

# Decorator pentru verificare admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        
        if not postgresql_working:
            # Modul demo
            if password == 'admin123':
                session['is_admin'] = True
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('login.html', error='Parolă incorectă')
        
        # Modul PostgreSQL
        conn = get_db_connection()
        if not conn:
            return render_template('login.html', error='Eroare de conexiune la baza de date')
            
        cur = conn.cursor()
        cur.execute('SELECT * FROM admin WHERE username = %s', ('admin',))
        admin = cur.fetchone()
        cur.close()
        conn.close()
        
        if admin and admin[1] == password:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Parolă incorectă')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    if not postgresql_working:
        # Date demo
        drivers = [
            {'id': 'sofer001', 'nume': 'Popescu', 'prenume': 'Ion'},
            {'id': 'sofer002', 'nume': 'Ionescu', 'prenume': 'Vasile'}
        ]
        
        vehicles = [
            {'id': 'vehicle001', 'tip': 'Duba', 'nr_inmatriculare': 'B-123-ABC'},
            {'id': 'vehicle002', 'tip': 'Camion', 'nr_inmatriculare': 'B-456-DEF'}
        ]
        
        active_missions = []
        completed_missions = []
        
        return render_template('admin_dashboard.html', 
                             active_missions=active_missions,
                             completed_missions=completed_missions,
                             drivers=drivers,
                             vehicles=vehicles,
                             today=date.today().isoformat())
    
    # Modul PostgreSQL
    conn = get_db_connection()
    if not conn:
        return "❌ Eroare de conexiune la baza de date", 500
        
    cur = conn.cursor()
    
    # Obține șoferi
    cur.execute('SELECT * FROM drivers ORDER BY prenume, nume')
    drivers = cur.fetchall()
    
    # Obține vehicule
    cur.execute('SELECT * FROM vehicles ORDER BY tip')
    vehicles = cur.fetchall()
    
    # Obține misiuni cu join
    cur.execute('''
        SELECT m.*, d.nume, d.prenume, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN drivers d ON m.sofer_id = d.id 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        ORDER BY m.data_inceput DESC
    ''')
    missions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    today = date.today()
    
    # Convertim la liste de dicționare pentru template
    def mission_to_dict(mission):
        return {
            'id': mission[0],
            'sofer_id': mission[1],
            'vehicle_id': mission[2],
            'data_inceput': mission[3].strftime('%Y-%m-%d'),
            'data_sfarsit': mission[4].strftime('%Y-%m-%d'),
            'destinatie': mission[5],
            'distanta': mission[6],
            'persoana_contact': mission[7],
            'status': mission[8],
            'nume': mission[9],
            'prenume': mission[10],
            'tip': mission[11],
            'nr_inmatriculare': mission[12]
        }
    
    # Separa misiunile active de cele istorice
    active_missions = []
    completed_missions = []
    
    for mission in missions:
        mission_dict = mission_to_dict(mission)
        if mission[4] >= today:  # data_sfarsit
            active_missions.append(mission_dict)
        else:
            completed_missions.append(mission_dict)
    
    # Convertim șoferi și vehicule la dicționare
    drivers_dict = [{'id': d[0], 'nume': d[1], 'prenume': d[2]} for d in drivers]
    vehicles_dict = [{'id': v[0], 'tip': v[1], 'nr_inmatriculare': v[2]} for v in vehicles]
    
    return render_template('admin_dashboard.html', 
                         active_missions=active_missions,
                         completed_missions=completed_missions,
                         drivers=drivers_dict,
                         vehicles=vehicles_dict,
                         today=today.isoformat())

# ... (adaugă aici toate celelalte rute din versiunea anterioară)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Serverul rulează pe portul {port}")
    print(f"📊 PostgreSQL funcțional: {postgresql_working}")
    app.run(host='0.0.0.0', port=port, debug=False)
