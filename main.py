from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024'

print("🚀 Aplicația a pornit cu Python 3.11 și SQLite!")

# Încarcă baza de date JSON
def load_db(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_db(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Inițializare baza de date
def init_db():
    if not os.path.exists('users.json'):
        save_db('users.json', {
            'admin': {'password': 'admin123', 'type': 'admin'},
            'sofer001': {'password': '', 'type': 'driver', 'nume': 'Popescu', 'prenume': 'Ion', 'created_at': datetime.now().isoformat()},
            'sofer002': {'password': '', 'type': 'driver', 'nume': 'Ionescu', 'prenume': 'Vasile', 'created_at': datetime.now().isoformat()}
        })
    
    if not os.path.exists('vehicles.json'):
        save_db('vehicles.json', {
            'vehicle001': {'tip': 'Duba', 'nr_inmatriculare': 'B-123-ABC', 'sofer': 'sofer001', 'created_at': datetime.now().isoformat()},
            'vehicle002': {'tip': 'Camion', 'nr_inmatriculare': 'B-456-DEF', 'sofer': 'sofer002', 'created_at': datetime.now().isoformat()}
        })
    
    if not os.path.exists('missions.json'):
        save_db('missions.json', {})
    
    print("✅ Baza de date JSON inițializată!")

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
        users = load_db('users.json')
        
        if users.get('admin', {}).get('password') == password:
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
    missions = load_db('missions.json')
    drivers = {k: v for k, v in load_db('users.json').items() if v.get('type') == 'driver'}
    vehicles = load_db('vehicles.json')
    
    today = date.today().isoformat()
    
    # Separa misiunile active de cele istorice
    active_missions = {}
    completed_missions = {}
    
    for mid, mission in missions.items():
        if mission.get('data_sfarsit', '') < today:
            completed_missions[mid] = mission
        else:
            active_missions[mid] = mission
    
    # Sortează misiunile istorice descrescător
    completed_missions = dict(sorted(
        completed_missions.items(), 
        key=lambda x: x[1].get('data_inceput', ''), 
        reverse=True
    ))
    
    return render_template('admin_dashboard.html', 
                         active_missions=active_missions,
                         completed_missions=completed_missions,
                         drivers=drivers,
                         vehicles=vehicles,
                         today=today)

@app.route('/create_mission', methods=['POST'])
@admin_required
def create_mission():
    mission_data = {
        'sofer': request.form.get('sofer'),
        'vehicul': request.form.get('vehicul'),
        'data_inceput': request.form.get('data_inceput'),
        'data_sfarsit': request.form.get('data_sfarsit'),
        'destinatie': request.form.get('destinatie'),
        'distanta': request.form.get('distanta'),
        'persoana_contact': request.form.get('persoana_contact'),
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    
    missions = load_db('missions.json')
    mission_id = f"mission{len(missions) + 1:03d}"
    missions[mission_id] = mission_data
    save_db('missions.json', missions)
    
    return jsonify({'success': True, 'mission_id': mission_id})

@app.route('/update_mission/<mission_id>', methods=['POST'])
@admin_required
def update_mission(mission_id):
    missions = load_db('missions.json')
    
    if mission_id in missions:
        missions[mission_id].update({
            'sofer': request.form.get('sofer'),
            'vehicul': request.form.get('vehicul'),
            'data_inceput': request.form.get('data_inceput'),
            'data_sfarsit': request.form.get('data_sfarsit'),
            'destinatie': request.form.get('destinatie'),
            'distanta': request.form.get('distanta'),
            'persoana_contact': request.form.get('persoana_contact'),
            'updated_at': datetime.now().isoformat()
        })
        
        save_db('missions.json', missions)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Misiunea nu a fost găsită'})

@app.route('/delete_mission/<mission_id>')
@admin_required
def delete_mission(mission_id):
    missions = load_db('missions.json')
    if mission_id in missions:
        del missions[mission_id]
        save_db('missions.json', missions)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/get_mission_data/<mission_id>')
@admin_required
def get_mission_data(mission_id):
    missions = load_db('missions.json')
    
    if mission_id in missions:
        return jsonify({'success': True, 'mission': missions[mission_id]})
    
    return jsonify({'success': False, 'error': 'Misiunea nu a fost găsită'})

@app.route('/export_active_missions')
@admin_required
def export_active_missions():
    missions = load_db('missions.json')
    drivers = load_db('users.json')
    vehicles = load_db('vehicles.json')
    
    today = date.today().isoformat()
    active_missions = {mid: m for mid, m in missions.items() if m.get('data_sfarsit', '') >= today}
    
    text_to_copy = "🚛 *MISIUNI ACTIVE* 🚛\n"
    text_to_copy += "══════════════════\n\n"
    
    for mission_id, mission in active_missions.items():
        driver_id = mission['sofer']
        driver_info = drivers.get(driver_id, {'prenume': 'Necunoscut', 'nume': ''})
        
        vehicle_id = mission['vehicul']
        vehicle_info = vehicles.get(vehicle_id, {'tip': 'Necunoscut', 'nr_inmatriculare': ''})
        
        text_to_copy += f"👤 *Șofer:* {driver_info.get('prenume', '')} {driver_info.get('nume', '')}\n"
        text_to_copy += f"🚗 *Vehicul:* {vehicle_info.get('tip', '')} - {vehicle_info.get('nr_inmatriculare', '')}\n"
        text_to_copy += f"📅 *Perioadă:* {mission['data_inceput']} - {mission['data_sfarsit']}\n"
        text_to_copy += f"🎯 *Destinație:* {mission['destinatie']}\n"
        text_to_copy += f"📏 *Distanță:* {mission['distanta']} km\n"
        text_to_copy += f"📞 *Contact:* {mission['persoana_contact']}\n"
        text_to_copy += "────────────────────\n\n"
    
    text_to_copy += "_Trimis din aplicația Misiuni Șoferi_"
    
    return render_template('export.html', export_text=text_to_copy)

# === GESTIONARE ȘOFERI ===
@app.route('/manage_drivers')
@admin_required
def manage_drivers():
    drivers = {k: v for k, v in load_db('users.json').items() if v.get('type') == 'driver'}
    return render_template('manage_drivers.html', drivers=drivers)

@app.route('/add_driver', methods=['POST'])
@admin_required
def add_driver():
    nume = request.form.get('nume')
    prenume = request.form.get('prenume')
    
    users = load_db('users.json')
    driver_id = f"sofer{len([u for u in users.values() if u.get('type') == 'driver']) + 1:03d}"
    
    users[driver_id] = {
        'password': '',
        'type': 'driver',
        'nume': nume,
        'prenume': prenume,
        'created_at': datetime.now().isoformat()
    }
    
    save_db('users.json', users)
    return jsonify({'success': True, 'driver_id': driver_id})

@app.route('/update_driver/<driver_id>', methods=['POST'])
@admin_required
def update_driver(driver_id):
    users = load_db('users.json')
    
    if driver_id in users:
        users[driver_id].update({
            'nume': request.form.get('nume'),
            'prenume': request.form.get('prenume'),
            'updated_at': datetime.now().isoformat()
        })
        
        save_db('users.json', users)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Șoferul nu a fost găsit'})

@app.route('/delete_driver/<driver_id>')
@admin_required
def delete_driver(driver_id):
    users = load_db('users.json')
    if driver_id in users:
        del users[driver_id]
        save_db('users.json', users)
    
    return redirect(url_for('manage_drivers'))

@app.route('/get_driver_data/<driver_id>')
@admin_required
def get_driver_data(driver_id):
    users = load_db('users.json')
    
    if driver_id in users:
        return jsonify({'success': True, 'driver': users[driver_id]})
    
    return jsonify({'success': False, 'error': 'Șoferul nu a fost găsit'})

# === GESTIONARE VEHICULE ===
@app.route('/manage_vehicles')
@admin_required
def manage_vehicles():
    vehicles = load_db('vehicles.json')
    return render_template('manage_vehicles.html', vehicles=vehicles)

@app.route('/add_vehicle', methods=['POST'])
@admin_required
def add_vehicle():
    tip = request.form.get('tip')
    nr_inmatriculare = request.form.get('nr_inmatriculare')
    
    vehicles = load_db('vehicles.json')
    vehicle_id = f"vehicle{len(vehicles) + 1:03d}"
    
    vehicles[vehicle_id] = {
        'tip': tip,
        'nr_inmatriculare': nr_inmatriculare,
        'sofer': '',
        'created_at': datetime.now().isoformat()
    }
    
    save_db('vehicles.json', vehicles)
    return jsonify({'success': True, 'vehicle_id': vehicle_id})

@app.route('/update_vehicle/<vehicle_id>', methods=['POST'])
@admin_required
def update_vehicle(vehicle_id):
    vehicles = load_db('vehicles.json')
    
    if vehicle_id in vehicles:
        vehicles[vehicle_id].update({
            'tip': request.form.get('tip'),
            'nr_inmatriculare': request.form.get('nr_inmatriculare'),
            'updated_at': datetime.now().isoformat()
        })
        
        save_db('vehicles.json', vehicles)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Vehiculul nu a fost găsit'})

@app.route('/delete_vehicle/<vehicle_id>')
@admin_required
def delete_vehicle(vehicle_id):
    vehicles = load_db('vehicles.json')
    if vehicle_id in vehicles:
        del vehicles[vehicle_id]
        save_db('vehicles.json', vehicles)
    
    return redirect(url_for('manage_vehicles'))

@app.route('/get_vehicle_data/<vehicle_id>')
@admin_required
def get_vehicle_data(vehicle_id):
    vehicles = load_db('vehicles.json')
    
    if vehicle_id in vehicles:
        return jsonify({'success': True, 'vehicle': vehicles[vehicle_id]})
    
    return jsonify({'success': False, 'error': 'Vehiculul nu a fost găsit'})

@app.route('/driver/<driver_id>')
def driver_view(driver_id):
    missions = load_db('missions.json')
    drivers = load_db('users.json')
    vehicles = load_db('vehicles.json')
    
    today = date.today().isoformat()
    driver_missions = {mid: m for mid, m in missions.items() 
                      if m.get('sofer') == driver_id and m.get('data_sfarsit', '') >= today}
    driver_info = drivers.get(driver_id, {})
    
    return render_template('driver_view.html', 
                         missions=driver_missions,
                         driver_info=driver_info,
                         vehicles=vehicles)

if __name__ == '__main__':
    # Inițializează baza de date
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Serverul rulează pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
