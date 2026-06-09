from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        role = data['role']
        name = data['name']
        email = data['email']
        password = generate_password_hash(data['password'])

        if role == 'student':
            # If email exists, update instead of insert
            cursor.execute("SELECT id FROM students WHERE email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE students SET name=%s, password=%s, branch=%s, cgpa=%s, skills=%s
                    WHERE email=%s
                """, (name, password, data.get('branch', ''), data.get('cgpa', 0), data.get('skills', ''), email))
            else:
                cursor.execute("""
                    INSERT INTO students (name, email, password, branch, cgpa, skills)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, email, password, data.get('branch', ''), data.get('cgpa', 0), data.get('skills', '')))

        elif role == 'company':
            # If email exists, update instead of insert
            cursor.execute("SELECT id FROM companies WHERE email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE companies SET name=%s, password=%s, industry=%s
                    WHERE email=%s
                """, (name, password, data.get('industry', ''), email))
            else:
                cursor.execute("""
                    INSERT INTO companies (name, email, password, industry)
                    VALUES (%s, %s, %s, %s)
                """, (name, email, password, data.get('industry', '')))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Registration error: {e}")

    finally:
        cursor.close()
        conn.close()


def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check students
        cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            user['role'] = 'student'
            return user

        # Check companies
        cursor.execute("SELECT * FROM companies WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            user['role'] = 'company'
            return user

        # Admin hardcoded
        if email == "admin@placement.com" and password == "admin123":
            return {'id': 0, 'name': 'Admin', 'role': 'admin'}

        return None

    except Exception as e:
        print(f"Login error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()