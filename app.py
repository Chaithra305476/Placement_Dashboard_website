from flask import Flask, render_template, request, redirect, session, url_for
from auth import register_user, login_user
import os
from db import get_connection

app = Flask(__name__)
app.secret_key = "placement123"
app.config['UPLOAD_FOLDER'] = 'uploads/offer_letters'

# ─── Home ───────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ─── Register ───────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        register_user(data)
        return redirect('/login')
    return render_template('register.html')

# ─── Login ──────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = login_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            if user['role'] == 'student':
                return redirect('/student/dashboard')
            elif user['role'] == 'company':
                return redirect('/company/dashboard')
            elif user['role'] == 'admin':
                return redirect('/admin/dashboard')
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# ─── Logout ─────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ─── Student Dashboard ──────────────────────────────
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/login')
    return render_template('student/dashboard.html', name=session['name'])

# ─── Company Dashboard ──────────────────────────────
@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect('/login')
    return render_template('company/dashboard.html', name=session['name'])

# ─── Admin Dashboard ────────────────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM companies")
    companies = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) as count FROM students WHERE placed = TRUE")
    total_placed = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM job_drives")
    total_drives = cursor.fetchone()['count']
    cursor.close()
    conn.close()
    return render_template('admin/dashboard.html',
        name=session['name'],
        students=students,
        companies=companies,
        total_students=len(students),
        total_companies=len(companies),
        total_placed=total_placed,
        total_drives=total_drives
    )

if __name__ == '__main__':
    app.run(debug=True)