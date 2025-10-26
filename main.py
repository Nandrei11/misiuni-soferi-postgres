import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024'

print("🚀 Aplicația a pornit! Se conectează la PostgreSQL...")

# Încearcă să importe psycopg2
try:
    import psycopg2
    print("✅ psycopg2 importat cu succes")
    
    # Funcție pentru conexiune la baza de date
    def get_db_connection():
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            print("🔗 Conectare la PostgreSQL...")
            conn = psycopg2.connect(database_url)
            return conn
        else:
            print("⚠️  DATABASE_URL nu este setat, folosesc SQLite")
            return None
            
except ImportError as e:
    print(f"❌ psycopg2 nu este instalat: {e}")
    def get_db_connection():
        print("⚠️  psycopg2 nu este disponibil, folosesc SQLite")
        return None

# Funcție simplă pentru inițializare
def init_simple_db():
    print("✅ Aplicația rulează în modul simplu")

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
        if password == 'admin123':
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
    # Date mock pentru testare
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

@app.route('/create_mission', methods=['POST'])
@admin_required
def create_mission():
    return jsonify({'success': True, 'mission_id': 'mission001', 'message': 'Demo - Misiune creată'})

@app.route('/manage_drivers')
@admin_required
def manage_drivers():
    drivers = [
        {'id': 'sofer001', 'nume': 'Popescu', 'prenume': 'Ion'},
        {'id': 'sofer002', 'nume': 'Ionescu', 'prenume': 'Vasile'}
    ]
    return render_template('manage_drivers.html', drivers=drivers)

@app.route('/manage_vehicles')
@admin_required
def manage_vehicles():
    vehicles = [
        {'id': 'vehicle001', 'tip': 'Duba', 'nr_inmatriculare': 'B-123-ABC'},
        {'id': 'vehicle002', 'tip': 'Camion', 'nr_inmatriculare': 'B-456-DEF'}
    ]
    return render_template('manage_vehicles.html', vehicles=vehicles)

@app.route('/export_active_missions')
@admin_required
def export_active_missions():
    text_to_copy = "🚛 *MISIUNI ACTIVE* 🚛\n══════════════════\n\n"
    text_to_copy += "👤 *Șofer:* Popescu Ion\n"
    text_to_copy += "🚗 *Vehicul:* Duba - B-123-ABC\n"
    text_to_copy += "📅 *Perioadă:* 2024-01-01 - 2024-01-02\n"
    text_to_copy += "🎯 *Destinație:* București\n"
    text_to_copy += "📏 *Distanță:* 100 km\n"
    text_to_copy += "📞 *Contact:* Manager - 0722 222 222\n"
    text_to_copy += "────────────────────\n\n"
    text_to_copy += "_Trimis din aplicația Misiuni Șoferi_"
    
    return render_template('export.html', export_text=text_to_copy)

@app.route('/driver/<driver_id>')
def driver_view(driver_id):
    missions = [
        {
            'tip': 'Duba',
            'nr_inmatriculare': 'B-123-ABC',
            'data_inceput': '2024-01-01',
            'data_sfarsit': '2024-01-02',
            'destinatie': 'București',
            'distanta': 100,
            'persoana_contact': 'Manager - 0722 222 222'
        }
    ]
    
    driver_info = {'id': driver_id, 'nume': 'Popescu', 'prenume': 'Ion'}
    
    return render_template('driver_view.html', 
                         missions=missions,
                         driver_info=driver_info)

if __name__ == '__main__':
    # Inițializează aplicația
    init_simple_db()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Serverul rulează pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
