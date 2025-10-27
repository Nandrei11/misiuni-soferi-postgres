import os
from urllib.parse import urlparse
import pg8000
import ssl
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024_postgres_pg8000_ssl'

print("=" * 50)
print("🚀 APLICAȚIA PORNIT - MISIUNI ȘOFERI CU SSL")
print("=" * 50)

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    print(f"📡 DATABASE_URL: {database_url}")
    
    if not database_url:
        raise Exception("❌ DATABASE_URL nu este setat!")
    
    url = urlparse(database_url)
    host = url.hostname
    port = url.port or 5432
    database = url.path[1:]
    username = url.username
    
    print(f"🔗 Conectare la: {host}:{port}/{database} ca {username}")
    
    try:
        # Conexiune cu SSL pentru Render PostgreSQL
        conn = pg8000.connect(
            host=host,
            port=port,
            database=database,
            user=url.username,
            password=url.password,
            timeout=30,
            ssl_context=True  # FORȚEAZĂ SSL
        )
        print("✅ CONEXIUNE REUȘITĂ la PostgreSQL cu SSL!")
        return conn
    except Exception as e:
        print(f"❌ EROARE CONEXIUNE: {e}")
        raise

def init_db():
    try:
        print("🔄 Inițializare baza de date...")
        conn = get_db_connection()
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
        print("✅ Tabela 'drivers' creată/verificată")
        
        # Tabela vehicule
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id VARCHAR(50) PRIMARY KEY,
                tip VARCHAR(100) NOT NULL,
                nr_inmatriculare VARCHAR(20) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        print("✅ Tabela 'vehicles' creată/verificată")
        
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
        print("✅ Tabela 'missions' creată/verificată")
        
        # Tabela admin
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL
            )
        ''')
        print("✅ Tabela 'admin' creată/verificată")
        
        # Verifică dacă există deja date
        cur.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        result = cur.fetchone()
        
        if result[0] == 0:
            print("👤 Adăugare utilizator admin...")
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
        print("✅ BAZA DE DATE INIȚIALIZATĂ CU SUCCES!")
        
    except Exception as e:
        print(f"⚠️  Aplicația continuă fără inițializarea bazei: {e}")

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

@app.route('/update_mission/<mission_id>', methods=['POST'])
@admin_required
def update_mission(mission_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE missions 
        SET sofer_id = %s, vehicle_id = %s, data_inceput = %s, data_sfarsit = %s,
            destinatie = %s, distanta = %s, persoana_contact = %s
        WHERE id = %s
    ''', (
        request.form.get('sofer'),
        request.form.get('vehicul'),
        request.form.get('data_inceput'),
        request.form.get('data_sfarsit'),
        request.form.get('destinatie'),
        int(request.form.get('distanta')),
        request.form.get('persoana_contact'),
        mission_id
    ))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_mission/<mission_id>')
@admin_required
def delete_mission(mission_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM missions WHERE id = %s', (mission_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/get_mission_data/<mission_id>')
@admin_required
def get_mission_data(mission_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM missions WHERE id = %s', (mission_id,))
    mission = cur.fetchone()
    cur.close()
    conn.close()
    
    if mission:
        mission_dict = {
            'id': mission[0],
            'sofer_id': mission[1],
            'vehicle_id': mission[2],
            'data_inceput': mission[3].strftime('%Y-%m-%d'),
            'data_sfarsit': mission[4].strftime('%Y-%m-%d'),
            'destinatie': mission[5],
            'distanta': mission[6],
            'persoana_contact': mission[7]
        }
        return jsonify({'success': True, 'mission': mission_dict})
    
    return jsonify({'success': False, 'error': 'Misiunea nu a fost găsită'})

@app.route('/export_active_missions')
@admin_required
def export_active_missions():
    conn = get_db_connection()
    cur = conn.cursor()
    
    today = date.today()
    cur.execute('''
        SELECT m.*, d.nume, d.prenume, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN drivers d ON m.sofer_id = d.id 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        WHERE m.data_sfarsit >= %s
        ORDER BY m.data_inceput DESC
    ''', (today,))
    active_missions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    text_to_copy = "🚛 *MISIUNI ACTIVE* 🚛\n"
    text_to_copy += "══════════════════\n\n"
    
    for mission in active_missions:
        # CORECT: mission[9] = nume, mission[10] = prenume, mission[11] = tip, mission[12] = nr_inmatriculare
        text_to_copy += f"👤 *Șofer:* {mission[10]} {mission[9]}\n"  # prenume + nume
        text_to_copy += f"🚗 *Vehicul:* {mission[11]} - {mission[12]}\n"  # tip + nr_inmatriculare
        text_to_copy += f"📅 *Perioadă:* {mission[3]} - {mission[4]}\n"  # data_inceput - data_sfarsit
        text_to_copy += f"🎯 *Destinație:* {mission[5]}\n"  # destinatie
        text_to_copy += f"📏 *Distanță:* {mission[6]} km\n"  # distanta
        text_to_copy += f"📞 *Contact:* {mission[7]}\n"  # persoana_contact
        text_to_copy += "────────────────────\n\n"
    
    text_to_copy += "_Trimis din aplicația Misiuni Șoferi_"
    
    return render_template('export.html', export_text=text_to_copy)

# === GESTIONARE ȘOFERI ===
@app.route('/manage_drivers')
@admin_required
def manage_drivers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM drivers ORDER BY prenume, nume')
    drivers = cur.fetchall()
    cur.close()
    conn.close()
    
    drivers_dict = [{'id': d[0], 'nume': d[1], 'prenume': d[2]} for d in drivers]
    return render_template('manage_drivers.html', drivers=drivers_dict)

@app.route('/add_driver', methods=['POST'])
@admin_required
def add_driver():
    driver_id = f"sofer{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO drivers (id, nume, prenume, created_at)
        VALUES (%s, %s, %s, %s)
    ''', (
        driver_id,
        request.form.get('nume'),
        request.form.get('prenume'),
        datetime.now()
    ))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 'driver_id': driver_id})

@app.route('/update_driver/<driver_id>', methods=['POST'])
@admin_required
def update_driver(driver_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE drivers 
        SET nume = %s, prenume = %s
        WHERE id = %s
    ''', (
        request.form.get('nume'),
        request.form.get('prenume'),
        driver_id
    ))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_driver/<driver_id>')
@admin_required
def delete_driver(driver_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM drivers WHERE id = %s', (driver_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('manage_drivers'))

@app.route('/get_driver_data/<driver_id>')
@admin_required
def get_driver_data(driver_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM drivers WHERE id = %s', (driver_id,))
    driver = cur.fetchone()
    cur.close()
    conn.close()
    
    if driver:
        driver_dict = {'id': driver[0], 'nume': driver[1], 'prenume': driver[2]}
        return jsonify({'success': True, 'driver': driver_dict})
    
    return jsonify({'success': False, 'error': 'Șoferul nu a fost găsit'})

# === GESTIONARE VEHICULE ===
@app.route('/manage_vehicles')
@admin_required
def manage_vehicles():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vehicles ORDER BY tip')
    vehicles = cur.fetchall()
    cur.close()
    conn.close()
    
    vehicles_dict = [{'id': v[0], 'tip': v[1], 'nr_inmatriculare': v[2]} for v in vehicles]
    return render_template('manage_vehicles.html', vehicles=vehicles_dict)

@app.route('/add_vehicle', methods=['POST'])
@admin_required
def add_vehicle():
    vehicle_id = f"vehicle{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO vehicles (id, tip, nr_inmatriculare, created_at)
        VALUES (%s, %s, %s, %s)
    ''', (
        vehicle_id,
        request.form.get('tip'),
        request.form.get('nr_inmatriculare'),
        datetime.now()
    ))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 'vehicle_id': vehicle_id})

@app.route('/update_vehicle/<vehicle_id>', methods=['POST'])
@admin_required
def update_vehicle(vehicle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE vehicles 
        SET tip = %s, nr_inmatriculare = %s
        WHERE id = %s
    ''', (
        request.form.get('tip'),
        request.form.get('nr_inmatriculare'),
        vehicle_id
    ))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_vehicle/<vehicle_id>')
@admin_required
def delete_vehicle(vehicle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM vehicles WHERE id = %s', (vehicle_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('manage_vehicles'))

@app.route('/get_vehicle_data/<vehicle_id>')
@admin_required
def get_vehicle_data(vehicle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vehicles WHERE id = %s', (vehicle_id,))
    vehicle = cur.fetchone()
    cur.close()
    conn.close()
    
    if vehicle:
        vehicle_dict = {'id': vehicle[0], 'tip': vehicle[1], 'nr_inmatriculare': vehicle[2]}
        return jsonify({'success': True, 'vehicle': vehicle_dict})
    
    return jsonify({'success': False, 'error': 'Vehiculul nu a fost găsit'})

@app.route('/driver/<driver_id>')
def driver_view(driver_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    today = date.today()
    cur.execute('''
        SELECT m.*, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        WHERE m.sofer_id = %s AND m.data_sfarsit >= %s
        ORDER BY m.data_inceput DESC
    ''', (driver_id, today))
    missions = cur.fetchall()
    
    cur.execute('SELECT * FROM drivers WHERE id = %s', (driver_id,))
    driver = cur.fetchone()
    
    cur.close()
    conn.close()
    
    missions_dict = []
    for mission in missions:
        missions_dict.append({
            'id': mission[0],
            'data_inceput': mission[3].strftime('%Y-%m-%d'),
            'data_sfarsit': mission[4].strftime('%Y-%m-%d'),
            'destinatie': mission[5],
            'distanta': mission[6],
            'persoana_contact': mission[7],
            'tip': mission[11],
            'nr_inmatriculare': mission[12]
        })
    
    driver_info = {'id': driver[0], 'nume': driver[1], 'prenume': driver[2]} if driver else {}
    
    return render_template('driver_view.html', 
                         missions=missions_dict,
                         driver_info=driver_info)

if __name__ == '__main__':
    # Inițializează baza de date
    print("🔄 Inițializare baza de date...")
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌍 Aplicația rulează pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
