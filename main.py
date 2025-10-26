from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret_key_2024'

print("🚀 Aplicația a pornit!")

@app.route('/')
def index():
    return "✅ Aplicația funcționează! Mergi la /login"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['is_admin'] = True
            return redirect('/admin')
        else:
            return render_template('login.html', error='Parolă incorectă')
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect('/login')
    return "✅ Panou Admin - Aplicația funcționează cu PostgreSQL!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)