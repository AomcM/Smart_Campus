"""
SmartCampus — Database layer (SQLite via sqlite3)
Creates all tables and provides helper functions.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "smartcampus.db")


def get_db():
    """Return a connection with row_factory set to dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables (if they don't exist) and seed sample data."""
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        -- Users / Auth
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('admin','teacher','student','restaurantStaff')),
            name        TEXT    NOT NULL
        );

        -- Students
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            level       TEXT    NOT NULL,
            speciality  TEXT    NOT NULL,
            user_id     INTEGER REFERENCES users(id)
        );

        -- Teachers
        CREATE TABLE IF NOT EXISTS teachers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            department  TEXT    NOT NULL,
            user_id     INTEGER REFERENCES users(id)
        );

        -- Modules
        CREATE TABLE IF NOT EXISTS modules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            title       TEXT    NOT NULL,
            credits     INTEGER NOT NULL DEFAULT 3,
            semester    INTEGER NOT NULL DEFAULT 1,
            teacher_id  INTEGER REFERENCES teachers(id)
        );

        -- Rooms
        CREATE TABLE IF NOT EXISTS rooms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,
            capacity    INTEGER NOT NULL DEFAULT 30,
            type        TEXT    NOT NULL DEFAULT 'TD',
            status      TEXT    NOT NULL DEFAULT 'available'
                        CHECK(status IN ('available','occupied','maintenance'))
        );

        -- Sessions (timetable slots)
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            day         INTEGER NOT NULL,   -- 0=Monday … 5=Saturday
            slot        INTEGER NOT NULL,   -- 0..3 (time bands)
            module_id   INTEGER NOT NULL REFERENCES modules(id),
            room_id     INTEGER NOT NULL REFERENCES rooms(id),
            type        TEXT    NOT NULL DEFAULT 'Cours'
        );

        -- Grades
        CREATE TABLE IF NOT EXISTS grades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id),
            module_id   INTEGER NOT NULL REFERENCES modules(id),
            value       REAL    NOT NULL,
            type        TEXT    NOT NULL DEFAULT 'Exam'
        );

        -- Attendance
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id),
            session_id  INTEGER NOT NULL REFERENCES sessions(id),
            status      TEXT    NOT NULL DEFAULT 'present'
                        CHECK(status IN ('present','absent','late','excused')),
            date        TEXT    NOT NULL
        );

        -- Meals (restaurant menu items)
        CREATE TABLE IF NOT EXISTS meals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en     TEXT    NOT NULL,
            name_fr     TEXT    NOT NULL,
            price       REAL    NOT NULL DEFAULT 0,
            type        TEXT    NOT NULL CHECK(type IN ('breakfast','lunch','dinner'))
        );

        -- Orders (restaurant)
        -- teacher_user_id is set when a teacher (not a student) places an order
        -- student_id is 0 for teacher orders (no real student row)
        CREATE TABLE IF NOT EXISTS orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id       INTEGER REFERENCES students(id),
            teacher_user_id  INTEGER,
            meal_id          INTEGER NOT NULL REFERENCES meals(id),
            orderer_name     TEXT    NOT NULL DEFAULT '',
            status           TEXT    NOT NULL DEFAULT 'pending'
                             CHECK(status IN ('pending','ready','served','not_served')),
            time             TEXT    NOT NULL
        );
    """)

    # ── Seed data (only if tables are empty) ──────────────────────────
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.executescript("""
            INSERT INTO users (username, password, role, name) VALUES
              ('admin',      'admin123',   'admin',           'Administrator'),
              ('teacher1',   'teacher123', 'teacher',         'Teacher A'),
              ('student1',   'student123', 'student',         'Student A'),
              ('student2',   'student123', 'student',         'Student B'),
              ('resto',      'resto123',   'restaurantStaff', 'Restaurant Staff');

            INSERT INTO students (code, first_name, last_name, email, level, speciality, user_id) VALUES
              ('S001', 'Ahmed',  'Benali',  'ahmed.benali@campus.edu',  'L2', 'GL', 3),
              ('S002', 'Fatima', 'Zahra',   'fatima.zahra@campus.edu',  'L3', 'SI', 4),
              ('S003', 'Yassir', 'Moussaoui','yassir.m@campus.edu',    'L1', 'GL', NULL),
              ('S004', 'Sara',   'El Idrissi','sara.e@campus.edu',     'L2', 'RT', NULL);

            INSERT INTO teachers (code, first_name, last_name, email, department, user_id) VALUES
              ('T001', 'Mohammed', 'Alami',   'm.alami@campus.edu',   'CS', 2),
              ('T002', 'Nadia',    'Tazi',    'n.tazi@campus.edu',    'Math', NULL),
              ('T003', 'Hassan',   'Cherkaoui','h.cherkaoui@campus.edu','IS', NULL);

            INSERT INTO modules (code, title, credits, semester, teacher_id) VALUES
              ('POO',  'Object-Oriented Programming', 6, 1, 1),
              ('GL',   'Software Engineering',        5, 2, 1),
              ('MATH', 'Mathematics for IT',          4, 1, 2),
              ('BD',   'Databases',                   5, 2, 3);

            INSERT INTO rooms (code, capacity, type, status) VALUES
              ('A-101',  40, 'Amphi', 'available'),
              ('B-203',  25, 'TD',    'occupied'),
              ('C-LAB1', 20, 'Lab',   'available'),
              ('B-204',  25, 'TD',    'maintenance');

            INSERT INTO sessions (day, slot, module_id, room_id, type) VALUES
              (0, 0, 1, 1, 'Cours'),
              (1, 1, 2, 2, 'TD'),
              (2, 0, 1, 3, 'TP'),
              (3, 2, 2, 1, 'Cours'),
              (0, 2, 3, 1, 'Cours'),
              (4, 1, 4, 2, 'TD');

            INSERT INTO grades (student_id, module_id, value, type) VALUES
              (1, 1, 14.5, 'Exam'),
              (1, 2, 12.0, 'TD'),
              (2, 1, 16.0, 'Exam'),
              (2, 2, 15.5, 'Exam'),
              (3, 1, 11.0, 'TD'),
              (4, 2, 13.5, 'Exam');

            INSERT INTO attendance (student_id, session_id, status, date) VALUES
              (1, 1, 'present', '2026-05-04'),
              (2, 1, 'absent',  '2026-05-04'),
              (1, 2, 'late',    '2026-05-05'),
              (2, 2, 'present', '2026-05-05'),
              (3, 1, 'present', '2026-05-04'),
              (4, 3, 'excused', '2026-05-06');

            INSERT INTO meals (name_en, name_fr, price, type) VALUES
              ('Breakfast set',  'Petit-déjeuner', 30, 'breakfast'),
              ('Lunch menu',     'Menu déjeuner',  50, 'lunch'),
              ('Dinner menu',    'Menu dîner',     50, 'dinner'),
              ('Coffee & snack', 'Café & snack',   15, 'breakfast');

            INSERT INTO orders (student_id, teacher_user_id, meal_id, orderer_name, status, time) VALUES
              (1, NULL, 2, 'Ahmed Benali',  'pending', '12:30'),
              (2, NULL, 2, 'Fatima Zahra',  'ready',   '12:35'),
              (3, NULL, 1, 'Yassir Moussaoui', 'served', '08:05');
        """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")
