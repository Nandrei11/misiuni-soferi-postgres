import os
from urllib.parse import urlparse
import pg8000
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024_postgres_pg8000'

print("🚀 Aplicația a pornit! Se conectează la PostgreSQL cu pg8000...")

# Funcție pentru conexiune la baza de date cu pg8000
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL nu este setat!")
    
    print(f"📡 URL baza de date: {database_url}")
    
    # Parsează URL-ul bazei de date
    url = urlparse(database_url)
    
    # Extrage componentele din URL
    host = url.hostname
    port = url.port or 5432
    database = url.path[1:]  # Elimină '/' din față
    username = url.username
    password = url.password
    
    print(f"🔗 Conectare la: {host}:{port}/{database} ca {username}")
    
    try:
        # Creează conexiunea cu pg8000
        conn = pg8000.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=30  # timeout de 30 de secunde
        )
        print("✅ Conexiune reușită la baza de date!")
        return conn
    except Exception as e:
        print(f"❌ Eroare conexiune: {e}")
        raise

# Inițializare bază de date
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("📦 Creare tabele dacă nu există...")
        
        # Tabela șoferi
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id VARCHAR(50) PRIMARY KEY,
                nume VARCHAR(100) NOT NULL,
                prenume VARCHAR(100) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        print("✅ Tabela 'drivers' verificată/creată")
        
        # Tabela vehicule
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id VARCHAR(50) PRIMARY KEY,
                tip VARCHAR(100) NOT NULL,
                nr_inmatriculare VARCHAR(20) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        print("✅ Tabela 'vehicles' verificată/creată")
        
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
        print("✅ Tabela 'missions' verificată/creată")
        
        # Tabela admin
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL
            )
        ''')
        print("✅ Tabela 'admin' verificată/creată")
        
        # Verifică dacă există deja date
        cur.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        result = cur.fetchone()
        
        if result[0] == 0:
            print("👤 Adăugare utilizator admin...")
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
            print("✅ Date inițiale adăugate")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Baza de date PostgreSQL inițializată cu succes cu pg8000!")
        
    except Exception as e:
        print(f"❌ Eroare la inițializarea bazei de date: {e}")
        # Nu mai ridica excepția ca să permită aplicației să ruleze
        print("⚠️  Aplicația va continua, dar baza de date nu este inițializată")

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
        
        try:
            conn = get_db_connection()
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
        except Exception as e:
            return render_template('login.html', error=f'Eroare baza de date: {e}')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
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
    except Exception as e:
        return f"Eroare la accesarea bazei de date: {e}"

# [RESTUL CODULUI RĂMÂNE LA FEL CA ÎN MESAJUL ANTERIOR...]
# Pentru brevitate, păstrez doar funcțiile modificate

@app.route('/create_mission', methods=['POST'])
@admin_required
def create_mission():
    try:
        mission_id = f"mission{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO missions (id, sofer_id, vehicle_id, data_inceput, data_sfarsit, 
                                destinatie, distanta, persoana_contact, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            mission_id,
            request.form.get('sofer'),
            request.form.get('vehicul'),
            request.form.get('data_inceput'),
            request.form.get('data_sfarsit'),
            request.form.get('destinatie'),
            int(request.form.get('distanta')),
            request.form.get('persoana_contact'),
            'active',
            datetime.now()
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'mission_id': mission_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# [TOATE CELELALTE FUNCȚII RĂMÂN LA FEL CA ÎN MESAJUL ANTERIOR]

if __name__ == '__main__':
    # Inițializează baza de date
    print("🔄 Inițializare baza de date...")
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌍 Aplicația rulează pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
