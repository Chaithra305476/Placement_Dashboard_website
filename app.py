from flask import Flask, render_template, request, redirect, session, url_for
from auth import register_user, login_user
import os
from db import get_connection
import csv
from flask import Response
import io

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
@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('role') != 'student':
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            cursor.execute("""
                UPDATE students SET name=%s, branch=%s, cgpa=%s, skills=%s
                WHERE id=%s
            """, (request.form['name'], request.form['branch'],
                  request.form['cgpa'], request.form['skills'],
                  session['user_id']))
            conn.commit()
            session['name'] = request.form['name']
            cursor.execute("SELECT * FROM students WHERE id=%s", (session['user_id'],))
            student = cursor.fetchone()
            return render_template('student/profile.html', student=student, success="Profile updated successfully!")
        cursor.execute("SELECT * FROM students WHERE id=%s", (session['user_id'],))
        student = cursor.fetchone()
        return render_template('student/profile.html', student=student)
    except Exception as e:
        return render_template('student/profile.html', student={}, error=str(e))
    finally:
        cursor.close()
        conn.close()
# ─── Student Dashboard ──────────────────────────────
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT j.id, c.name as company_name, j.role, j.date, j.cgpa_cutoff
            FROM job_drives j
            JOIN companies c ON j.company_id = c.id
        """)
        drives = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) as count FROM applications
            WHERE student_id = %s
        """, (session['user_id'],))
        applied_count = cursor.fetchone()['count']

        cursor.execute("SELECT placed FROM students WHERE id = %s", (session['user_id'],))
        student = cursor.fetchone()
        placed = student['placed'] if student else False

        return render_template('student/dashboard.html',
            name=session['name'],
            drives=drives,
            applied_count=applied_count,
            placed=placed
        )
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()
# ─── Company Dashboard ──────────────────────────────
@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect('/login')
    return render_template('company/dashboard.html', name=session['name'])
@app.route('/company/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'company':
        return redirect('/login')
    if request.method == 'POST':
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO job_drives (company_id, role, date, cgpa_cutoff)
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], request.form['role'], request.form['date'], request.form['cgpa_cutoff']))
            conn.commit()
            return render_template('company/post_job.html', success="Job drive posted successfully!")
        except Exception as e:
            return render_template('company/post_job.html', error=str(e))
        finally:
            cursor.close()
            conn.close()
    return render_template('company/post_job.html')
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
@app.route('/admin/reports')
def admin_reports():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM students WHERE placed = TRUE")
        total_placed = cursor.fetchone()['count']

        total_unplaced = total_students - total_placed
        placement_rate = round((total_placed / total_students * 100), 1) if total_students > 0 else 0

        cursor.execute("""
            SELECT branch,
                COUNT(*) as total,
                SUM(placed) as placed,
                COUNT(*) - SUM(placed) as unplaced
            FROM students
            GROUP BY branch
        """)
        branch_report = cursor.fetchall()

        cursor.execute("""
            SELECT c.name as company_name, j.role, j.date, j.cgpa_cutoff
            FROM job_drives j
            JOIN companies c ON j.company_id = c.id
        """)
        drives = cursor.fetchall()

        return render_template('admin/reports.html',
            total_students=total_students,
            total_placed=total_placed,
            total_unplaced=total_unplaced,
            placement_rate=placement_rate,
            branch_report=branch_report,
            drives=drives
        )
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()
@app.route('/admin/export')
def export_csv():
    if session.get('role') != 'admin':
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email, branch, cgpa, skills, placed FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name', 'email', 'branch', 'cgpa', 'skills', 'placed'])
    writer.writeheader()
    writer.writerows(students)

    return Response(output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=placement_report.csv"})

if __name__ == '__main__':
    app.run(debug=True)