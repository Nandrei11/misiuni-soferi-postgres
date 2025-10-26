import os
from urllib.parse import urlparse
import pg8000
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024_postgres_pg8000'

print("=" * 50)
print("🚀 APLICAȚIA PORNIT - MISIUNI ȘOFERI")
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
        conn = pg8000.connect(
            host=host,
            port=port,
            database=database,
            user=url.username,
            password=url.password,
            timeout=30
        )
        print("✅ CONEXIUNE REUȘITĂ la PostgreSQL!")
        return conn
    except Exception as e:
        print(f"❌ EROARE CONEXIUNE: {e}")
        raise

def init_db():
    try:
        print("🔄 Inițializare baza de date...")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tabelele tale existente...
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id VARCHAR(50) PRIMARY KEY,
                nume VARCHAR(100) NOT NULL,
                prenume VARCHAR(100) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id VARCHAR(50) PRIMARY KEY,
                tip VARCHAR(100) NOT NULL,
                nr_inmatriculare VARCHAR(20) NOT NULL,
                created_at TIMESTAMP
            )
        ''')
        
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
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL
            )
        ''')
        
        cur.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")
            print("✅ Admin creat: admin / admin123")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ BAZA DE DATE INIȚIALIZATĂ CU SUCCES!")
        
    except Exception as e:
        print(f"⚠️  Aplicația continuă fără inițializarea bazei: {e}")

# [RESTUL CODULUI TĂU EXISTENT - exact ca în versiunea anterioară]
# ... toate route-urile și funcțiile tale existente ...

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

# ... adaugă aici TOATE celelalte route-uri pe care le ai ...

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"🌍 Aplicația rulează pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
