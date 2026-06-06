"""
SmartCampus — Flask Application
Routes follow REST-ish conventions:
  GET  /api/<resource>          → list
  POST /api/<resource>          → create
  PUT  /api/<resource>/<id>     → update
  DELETE /api/<resource>/<id>   → delete

Pages are server-rendered via Jinja2 templates.
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from database import get_db, init_db
import functools

app = Flask(__name__)
app.secret_key = "smartcampus-secret-2026"  # change in production
app.jinja_env.globals.update(enumerate=enumerate, zip=zip)

# ─────────────────────────── Helpers ────────────────────────────────

def login_required(roles=None):
    """Decorator: require login, optionally restrict to given roles."""
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in first.", "warning")
                return redirect(url_for("login"))
            if roles and session.get("role") not in roles:
                flash("Access denied.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def row_to_dict(row):
    """Convert sqlite3.Row to plain dict."""
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ─────────────────────────── Auth ───────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()
        user = row_to_dict(
            db.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()
        )
        db.close()
        if user:
            session["user_id"] = user["id"]
            session["role"]    = user["role"]
            session["name"]    = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────── Dashboard ──────────────────────────────

@app.route("/dashboard")
@login_required()
def dashboard():
    db   = get_db()
    role = session["role"]
    stats = {}

    if role == "admin":
        stats["students"]  = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        stats["teachers"]  = db.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
        stats["modules"]   = db.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        stats["rooms"]     = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        recent_grades = rows_to_list(db.execute(
            """SELECT g.value, g.type, s.first_name||' '||s.last_name AS student,
                      m.title AS module
               FROM grades g
               JOIN students s ON s.id=g.student_id
               JOIN modules  m ON m.id=g.module_id
               ORDER BY g.id DESC LIMIT 5"""
        ).fetchall())
        db.close()
        return render_template("dashboard_admin.html",
                               stats=stats, recent_grades=recent_grades)

    if role == "teacher":
        user_id = session["user_id"]
        teacher = row_to_dict(db.execute(
            "SELECT * FROM teachers WHERE user_id=?", (user_id,)
        ).fetchone())
        my_modules = []
        if teacher:
            my_modules = rows_to_list(db.execute(
                "SELECT * FROM modules WHERE teacher_id=?", (teacher["id"],)
            ).fetchall())
        db.close()
        return render_template("dashboard_teacher.html",
                               teacher=teacher, my_modules=my_modules)

    if role == "student":
        user_id = session["user_id"]
        student = row_to_dict(db.execute(
            "SELECT * FROM students WHERE user_id=?", (user_id,)
        ).fetchone())
        my_grades = []
        if student:
            my_grades = rows_to_list(db.execute(
                """SELECT g.value, g.type, m.title, m.code
                   FROM grades g JOIN modules m ON m.id=g.module_id
                   WHERE g.student_id=? ORDER BY m.code""",
                (student["id"],)
            ).fetchall())
        db.close()
        return render_template("dashboard_student.html",
                               student=student, my_grades=my_grades)

    if role == "restaurantStaff":
        stats["pending"] = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status='pending'"
        ).fetchone()[0]
        stats["ready"] = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status='ready'"
        ).fetchone()[0]
        stats["served"] = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status='served'"
        ).fetchone()[0]
        db.close()
        return render_template("dashboard_restaurant.html", stats=stats)

    db.close()
    return render_template("dashboard_admin.html", stats=stats)


# ─────────────────────────── Students ───────────────────────────────

@app.route("/students")
@login_required(roles=["admin"])
def students():
    q  = request.args.get("q", "")
    db = get_db()
    if q:
        rows = rows_to_list(db.execute(
            """SELECT * FROM students
               WHERE first_name LIKE ? OR last_name LIKE ?
                  OR code LIKE ? OR email LIKE ?""",
            (f"%{q}%",)*4
        ).fetchall())
    else:
        rows = rows_to_list(db.execute("SELECT * FROM students ORDER BY last_name").fetchall())
    db.close()
    return render_template("students.html", students=rows, q=q)


@app.route("/students/add", methods=["GET", "POST"])
@login_required(roles=["admin"])
def student_add():
    if request.method == "POST":
        f = request.form
        db = get_db()
        try:
            db.execute(
                """INSERT INTO students (code,first_name,last_name,email,level,speciality)
                   VALUES (?,?,?,?,?,?)""",
                (f["code"], f["first_name"], f["last_name"],
                 f["email"], f["level"], f["speciality"])
            )
            db.commit()
            flash("Student added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("students"))
    return render_template("student_form.html", student=None)


@app.route("/students/edit/<int:sid>", methods=["GET", "POST"])
@login_required(roles=["admin"])
def student_edit(sid):
    db = get_db()
    student = row_to_dict(db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone())
    if not student:
        db.close()
        flash("Student not found.", "danger")
        return redirect(url_for("students"))
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                """UPDATE students SET code=?,first_name=?,last_name=?,
                   email=?,level=?,speciality=? WHERE id=?""",
                (f["code"], f["first_name"], f["last_name"],
                 f["email"], f["level"], f["speciality"], sid)
            )
            db.commit()
            flash("Student updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("students"))
    db.close()
    return render_template("student_form.html", student=student)


@app.route("/students/delete/<int:sid>", methods=["POST"])
@login_required(roles=["admin"])
def student_delete(sid):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (sid,))
    db.commit()
    db.close()
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


# ─────────────────────────── Teachers ───────────────────────────────

@app.route("/teachers")
@login_required(roles=["admin"])
def teachers():
    q  = request.args.get("q", "")
    db = get_db()
    if q:
        rows = rows_to_list(db.execute(
            """SELECT * FROM teachers
               WHERE first_name LIKE ? OR last_name LIKE ?
                  OR code LIKE ? OR department LIKE ?""",
            (f"%{q}%",)*4
        ).fetchall())
    else:
        rows = rows_to_list(db.execute("SELECT * FROM teachers ORDER BY last_name").fetchall())
    db.close()
    return render_template("teachers.html", teachers=rows, q=q)


@app.route("/teachers/add", methods=["GET", "POST"])
@login_required(roles=["admin"])
def teacher_add():
    if request.method == "POST":
        f = request.form
        db = get_db()
        try:
            db.execute(
                """INSERT INTO teachers (code,first_name,last_name,email,department)
                   VALUES (?,?,?,?,?)""",
                (f["code"], f["first_name"], f["last_name"], f["email"], f["department"])
            )
            db.commit()
            flash("Teacher added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("teachers"))
    return render_template("teacher_form.html", teacher=None)


@app.route("/teachers/edit/<int:tid>", methods=["GET", "POST"])
@login_required(roles=["admin"])
def teacher_edit(tid):
    db = get_db()
    teacher = row_to_dict(db.execute("SELECT * FROM teachers WHERE id=?", (tid,)).fetchone())
    if not teacher:
        db.close()
        flash("Teacher not found.", "danger")
        return redirect(url_for("teachers"))
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                """UPDATE teachers SET code=?,first_name=?,last_name=?,
                   email=?,department=? WHERE id=?""",
                (f["code"], f["first_name"], f["last_name"],
                 f["email"], f["department"], tid)
            )
            db.commit()
            flash("Teacher updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("teachers"))
    db.close()
    return render_template("teacher_form.html", teacher=teacher)


@app.route("/teachers/delete/<int:tid>", methods=["POST"])
@login_required(roles=["admin"])
def teacher_delete(tid):
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id=?", (tid,))
    db.commit()
    db.close()
    flash("Teacher deleted.", "success")
    return redirect(url_for("teachers"))


# ─────────────────────────── Modules ────────────────────────────────

@app.route("/modules")
@login_required(roles=["admin", "teacher"])
def modules():
    db = get_db()
    rows = rows_to_list(db.execute(
        """SELECT m.*, t.first_name||' '||t.last_name AS teacher_name
           FROM modules m LEFT JOIN teachers t ON t.id=m.teacher_id
           ORDER BY m.code"""
    ).fetchall())
    db.close()
    return render_template("modules.html", modules=rows)


@app.route("/modules/add", methods=["GET", "POST"])
@login_required(roles=["admin"])
def module_add():
    db = get_db()
    teachers_list = rows_to_list(db.execute("SELECT * FROM teachers ORDER BY last_name").fetchall())
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                """INSERT INTO modules (code,title,credits,semester,teacher_id)
                   VALUES (?,?,?,?,?)""",
                (f["code"], f["title"], int(f["credits"]),
                 int(f["semester"]), f.get("teacher_id") or None)
            )
            db.commit()
            flash("Module added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("modules"))
    db.close()
    return render_template("module_form.html", module=None, teachers=teachers_list)


@app.route("/modules/edit/<int:mid>", methods=["GET", "POST"])
@login_required(roles=["admin"])
def module_edit(mid):
    db = get_db()
    module = row_to_dict(db.execute("SELECT * FROM modules WHERE id=?", (mid,)).fetchone())
    teachers_list = rows_to_list(db.execute("SELECT * FROM teachers ORDER BY last_name").fetchall())
    if not module:
        db.close()
        flash("Module not found.", "danger")
        return redirect(url_for("modules"))
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                """UPDATE modules SET code=?,title=?,credits=?,semester=?,teacher_id=?
                   WHERE id=?""",
                (f["code"], f["title"], int(f["credits"]),
                 int(f["semester"]), f.get("teacher_id") or None, mid)
            )
            db.commit()
            flash("Module updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("modules"))
    db.close()
    return render_template("module_form.html", module=module, teachers=teachers_list)


@app.route("/modules/delete/<int:mid>", methods=["POST"])
@login_required(roles=["admin"])
def module_delete(mid):
    db = get_db()
    db.execute("DELETE FROM modules WHERE id=?", (mid,))
    db.commit()
    db.close()
    flash("Module deleted.", "success")
    return redirect(url_for("modules"))


# ─────────────────────────── Rooms ──────────────────────────────────

@app.route("/rooms")
@login_required(roles=["admin"])
def rooms():
    db = get_db()
    rows = rows_to_list(db.execute("SELECT * FROM rooms ORDER BY code").fetchall())
    db.close()
    return render_template("rooms.html", rooms=rows)


@app.route("/rooms/add", methods=["GET", "POST"])
@login_required(roles=["admin"])
def room_add():
    if request.method == "POST":
        f = request.form
        db = get_db()
        try:
            db.execute(
                """INSERT INTO rooms (code,capacity,type,status)
                   VALUES (?,?,?,?)""",
                (f["code"], int(f["capacity"]), f["type"], f.get("status", "available"))
            )
            db.commit()
            flash("Room added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("rooms"))
    return render_template("room_form.html", room=None)


@app.route("/rooms/edit/<int:rid>", methods=["GET", "POST"])
@login_required(roles=["admin"])
def room_edit(rid):
    db = get_db()
    room = row_to_dict(db.execute("SELECT * FROM rooms WHERE id=?", (rid,)).fetchone())
    if not room:
        db.close()
        flash("Room not found.", "danger")
        return redirect(url_for("rooms"))
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                "UPDATE rooms SET code=?,capacity=?,type=?,status=? WHERE id=?",
                (f["code"], int(f["capacity"]), f["type"], f["status"], rid)
            )
            db.commit()
            flash("Room updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            db.close()
        return redirect(url_for("rooms"))
    db.close()
    return render_template("room_form.html", room=room)


@app.route("/rooms/delete/<int:rid>", methods=["POST"])
@login_required(roles=["admin"])
def room_delete(rid):
    db = get_db()
    db.execute("DELETE FROM rooms WHERE id=?", (rid,))
    db.commit()
    db.close()
    flash("Room deleted.", "success")
    return redirect(url_for("rooms"))


# ─────────────────────────── Schedule ───────────────────────────────

DAYS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SLOTS = ["08:00–10:00", "10:15–12:15", "13:00–15:00", "15:15–17:15"]


@app.route("/schedule")
@login_required()
def schedule():
    db = get_db()
    sessions = rows_to_list(db.execute(
        """SELECT s.*, m.title AS module_title, m.code AS module_code,
                  r.code AS room_code, t.first_name||' '||t.last_name AS teacher_name
           FROM sessions s
           JOIN modules m ON m.id=s.module_id
           JOIN rooms   r ON r.id=s.room_id
           LEFT JOIN teachers t ON t.id=m.teacher_id"""
    ).fetchall())
    modules_list = rows_to_list(db.execute("SELECT * FROM modules ORDER BY title").fetchall())
    rooms_list   = rows_to_list(db.execute("SELECT * FROM rooms   ORDER BY code").fetchall())
    db.close()
    # Build grid[day][slot] = session | None
    grid = {d: {s: None for s in range(len(SLOTS))} for d in range(len(DAYS))}
    for sess in sessions:
        grid[sess["day"]][sess["slot"]] = sess
    return render_template("schedule.html",
                           grid=grid, days=DAYS, slots=SLOTS,
                           modules=modules_list, rooms=rooms_list)


@app.route("/schedule/add", methods=["POST"])
@login_required(roles=["admin"])
def session_add():
    f         = request.form
    day       = int(f["day"])
    slot      = int(f["slot"])
    module_id = int(f["module_id"])
    room_id   = int(f["room_id"])
    db = get_db()
    try:
        # Conflict: same slot already has a session (any module)
        slot_taken = db.execute(
            "SELECT id FROM sessions WHERE day=? AND slot=?", (day, slot)
        ).fetchone()
        if slot_taken:
            flash("That time slot is already occupied. Please choose a different day or slot.", "danger")
            db.close()
            return redirect(url_for("schedule"))
        db.execute(
            "INSERT INTO sessions (day,slot,module_id,room_id,type) VALUES (?,?,?,?,?)",
            (day, slot, module_id, room_id, f.get("type", "Cours"))
        )
        db.commit()
        flash("Session added.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("schedule"))


@app.route("/schedule/delete/<int:sid>", methods=["POST"])
@login_required(roles=["admin"])
def session_delete(sid):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE id=?", (sid,))
    db.commit()
    db.close()
    flash("Session removed.", "success")
    return redirect(url_for("schedule"))


# ─────────────────────────── Grades ─────────────────────────────────

@app.route("/grades")
@login_required(roles=["admin", "teacher", "student"])
def grades():
    db   = get_db()
    role = session["role"]
    filter_student = request.args.get("student_id", "")
    filter_module  = request.args.get("module_id",  "")

    if role == "student":
        student = row_to_dict(db.execute(
            "SELECT * FROM students WHERE user_id=?", (session["user_id"],)
        ).fetchone())
        if student:
            rows = rows_to_list(db.execute(
                """SELECT g.*, m.title, m.code AS module_code,
                          s.first_name||' '||s.last_name AS student_name
                   FROM grades g
                   JOIN modules  m ON m.id=g.module_id
                   JOIN students s ON s.id=g.student_id
                   WHERE g.student_id=?
                   ORDER BY m.code""", (student["id"],)
            ).fetchall())
        else:
            rows = []
    else:
        # Build dynamic WHERE clause for admin/teacher filters
        conditions = []
        params     = []
        if filter_student:
            conditions.append("g.student_id=?")
            params.append(int(filter_student))
        if filter_module:
            conditions.append("g.module_id=?")
            params.append(int(filter_module))
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = rows_to_list(db.execute(
            f"""SELECT g.*, m.title, m.code AS module_code,
                      s.first_name||' '||s.last_name AS student_name
               FROM grades g
               JOIN modules  m ON m.id=g.module_id
               JOIN students s ON s.id=g.student_id
               {where}
               ORDER BY s.last_name, m.code""",
            params
        ).fetchall())

    students_list = rows_to_list(db.execute("SELECT * FROM students ORDER BY last_name").fetchall())
    modules_list  = rows_to_list(db.execute("SELECT * FROM modules ORDER BY code").fetchall())
    db.close()
    return render_template("grades.html", grades=rows,
                           students=students_list, modules=modules_list,
                           filter_student=filter_student, filter_module=filter_module)


@app.route("/grades/add", methods=["POST"])
@login_required(roles=["admin", "teacher"])
def grade_add():
    f         = request.form
    student_id = int(f["student_id"])
    module_id  = int(f["module_id"])
    value      = float(f["value"])
    grade_type = f.get("type", "Exam")
    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM grades WHERE student_id=? AND module_id=? AND type=?",
            (student_id, module_id, grade_type)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE grades SET value=? WHERE id=?",
                (value, existing["id"])
            )
            db.commit()
            flash("Grade updated (existing record for this student/module/type was overwritten).", "warning")
        else:
            db.execute(
                "INSERT INTO grades (student_id,module_id,value,type) VALUES (?,?,?,?)",
                (student_id, module_id, value, grade_type)
            )
            db.commit()
            flash("Grade saved.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("grades"))


@app.route("/grades/delete/<int:gid>", methods=["POST"])
@login_required(roles=["admin", "teacher"])
def grade_delete(gid):
    db = get_db()
    db.execute("DELETE FROM grades WHERE id=?", (gid,))
    db.commit()
    db.close()
    flash("Grade deleted.", "success")
    return redirect(url_for("grades"))


# ─────────────────────────── Attendance ─────────────────────────────

@app.route("/attendance")
@login_required(roles=["admin", "teacher", "student"])
def attendance():
    db   = get_db()
    role = session["role"]
    if role == "student":
        student = row_to_dict(db.execute(
            "SELECT * FROM students WHERE user_id=?", (session["user_id"],)
        ).fetchone())
        if student:
            rows = rows_to_list(db.execute(
                """SELECT a.*, s.first_name||' '||s.last_name AS student_name,
                          m.title AS module_title, a.date
                   FROM attendance a
                   JOIN students st ON st.id=a.student_id
                   JOIN sessions  s2 ON s2.id=a.session_id
                   JOIN modules   m  ON m.id=s2.module_id
                   JOIN students  s  ON s.id=a.student_id
                   WHERE a.student_id=? ORDER BY a.date DESC""",
                (student["id"],)
            ).fetchall())
        else:
            rows = []
    else:
        rows = rows_to_list(db.execute(
            """SELECT a.*, s.first_name||' '||s.last_name AS student_name,
                      m.title AS module_title
               FROM attendance a
               JOIN students s  ON s.id=a.student_id
               JOIN sessions s2 ON s2.id=a.session_id
               JOIN modules  m  ON m.id=s2.module_id
               ORDER BY a.date DESC"""
        ).fetchall())
    students_list = rows_to_list(db.execute("SELECT * FROM students ORDER BY last_name").fetchall())
    sessions_list = rows_to_list(db.execute(
        """SELECT s.id, m.code||' ('||s.type||')' AS label
           FROM sessions s JOIN modules m ON m.id=s.module_id"""
    ).fetchall())
    db.close()
    from datetime import date
    return render_template("attendance.html", records=rows,
                           students=students_list, sessions=sessions_list,
                           now=date.today().isoformat())


@app.route("/attendance/add", methods=["POST"])
@login_required(roles=["admin", "teacher"])
def attendance_add():
    f  = request.form
    db = get_db()
    try:
        db.execute(
            "INSERT INTO attendance (student_id,session_id,status,date) VALUES (?,?,?,?)",
            (int(f["student_id"]), int(f["session_id"]),
             f.get("status", "present"), f["date"])
        )
        db.commit()
        flash("Attendance saved.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("attendance"))


@app.route("/attendance/delete/<int:aid>", methods=["POST"])
@login_required(roles=["admin", "teacher"])
def attendance_delete(aid):
    db = get_db()
    db.execute("DELETE FROM attendance WHERE id=?", (aid,))
    db.commit()
    db.close()
    flash("Record deleted.", "success")
    return redirect(url_for("attendance"))


@app.route("/attendance/edit/<int:aid>", methods=["POST"])
@login_required(roles=["admin", "teacher"])
def attendance_edit(aid):
    new_status = request.form.get("status")
    if new_status not in ("present", "absent", "late", "excused"):
        flash("Invalid status.", "danger")
        return redirect(url_for("attendance"))
    db = get_db()
    db.execute("UPDATE attendance SET status=? WHERE id=?", (new_status, aid))
    db.commit()
    db.close()
    flash("Attendance status updated.", "success")
    return redirect(url_for("attendance"))


# ─────────────────────────── Restaurant ─────────────────────────────

@app.route("/restaurant")
@login_required()
def restaurant():
    db   = get_db()
    role = session["role"]
    uid  = session["user_id"]
    meals_list = rows_to_list(db.execute("SELECT * FROM meals ORDER BY type,name_en").fetchall())

    ORDER_QUERY = """
        SELECT o.*, m.name_en, m.name_fr, m.type AS meal_type
        FROM orders o
        JOIN meals m ON m.id=o.meal_id
        {where}
        ORDER BY o.id DESC
    """

    if role == "student":
        student = row_to_dict(db.execute("SELECT * FROM students WHERE user_id=?", (uid,)).fetchone())
        if student:
            orders_list = rows_to_list(db.execute(
                ORDER_QUERY.format(where="WHERE o.student_id=?"), (student["id"],)
            ).fetchall())
        else:
            orders_list = []
        own_student_id = student["id"] if student else None

    elif role == "teacher":
        orders_list = rows_to_list(db.execute(
            ORDER_QUERY.format(where="WHERE o.teacher_user_id=?"), (uid,)
        ).fetchall())
        own_student_id = None

    else:
        # admin / restaurantStaff: all orders with orderer name
        orders_list = rows_to_list(db.execute(
            ORDER_QUERY.format(where=""), ()
        ).fetchall())
        own_student_id = None

    students_list = rows_to_list(db.execute("SELECT * FROM students ORDER BY last_name").fetchall())
    db.close()
    return render_template("restaurant.html",
                           meals=meals_list, orders=orders_list,
                           students=students_list,
                           own_student_id=own_student_id)


@app.route("/restaurant/order/add", methods=["POST"])
@login_required(roles=["admin", "restaurantStaff", "student", "teacher"])
def order_add():
    f    = request.form
    role = session["role"]
    uid  = session["user_id"]
    db   = get_db()
    try:
        if role == "student":
            student = row_to_dict(db.execute(
                "SELECT * FROM students WHERE user_id=?", (uid,)
            ).fetchone())
            if not student:
                flash("Student profile not found.", "danger")
                db.close()
                return redirect(url_for("restaurant"))
            db.execute(
                """INSERT INTO orders (student_id, teacher_user_id, meal_id, orderer_name, status, time)
                   VALUES (?,?,?,?,?,?)""",
                (student["id"], None, int(f["meal_id"]),
                 f"{student['first_name']} {student['last_name']}",
                 "pending", f.get("time", "12:00"))
            )

        elif role == "teacher":
            teacher = row_to_dict(db.execute(
                "SELECT * FROM teachers WHERE user_id=?", (uid,)
            ).fetchone())
            name = f"{teacher['first_name']} {teacher['last_name']}" if teacher else session["name"]
            db.execute(
                """INSERT INTO orders (student_id, teacher_user_id, meal_id, orderer_name, status, time)
                   VALUES (?,?,?,?,?,?)""",
                (None, uid, int(f["meal_id"]), name, "pending", f.get("time", "12:00"))
            )

        else:
            # admin / restaurantStaff: pick any student
            student_id = int(f["student_id"])
            student = row_to_dict(db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone())
            name = f"{student['first_name']} {student['last_name']}" if student else "Unknown"
            db.execute(
                """INSERT INTO orders (student_id, teacher_user_id, meal_id, orderer_name, status, time)
                   VALUES (?,?,?,?,?,?)""",
                (student_id, None, int(f["meal_id"]), name, "pending", f.get("time", "12:00"))
            )

        db.commit()
        flash("Order placed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("restaurant"))


@app.route("/restaurant/order/status/<int:oid>", methods=["POST"])
@login_required(roles=["admin", "restaurantStaff"])
def order_status(oid):
    status = request.form.get("status", "pending")
    if status not in ("pending", "ready", "served", "not_served"):
        flash("Invalid status.", "danger")
        return redirect(url_for("restaurant"))
    db = get_db()
    db.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    db.commit()
    db.close()
    flash("Order status updated.", "success")
    return redirect(url_for("restaurant"))


@app.route("/restaurant/meal/add", methods=["POST"])
@login_required(roles=["admin", "restaurantStaff"])
def meal_add():
    f  = request.form
    db = get_db()
    try:
        db.execute(
            "INSERT INTO meals (name_en,name_fr,price,type) VALUES (?,?,?,?)",
            (f["name_en"], f["name_fr"], float(f["price"]), f["type"])
        )
        db.commit()
        flash("Meal added to menu.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("restaurant"))


@app.route("/restaurant/meal/delete/<int:mid>", methods=["POST"])
@login_required(roles=["admin", "restaurantStaff"])
def meal_delete(mid):
    db = get_db()
    db.execute("DELETE FROM meals WHERE id=?", (mid,))
    db.commit()
    db.close()
    flash("Meal removed.", "success")
    return redirect(url_for("restaurant"))


# ─────────────────────────── Reports ────────────────────────────────

@app.route("/reports")
@login_required(roles=["admin"])
def reports():
    db = get_db()
    # Avg grade per module
    module_avgs = rows_to_list(db.execute(
        """SELECT m.title, m.code, AVG(g.value) AS avg, COUNT(g.id) AS count
           FROM grades g JOIN modules m ON m.id=g.module_id
           GROUP BY m.id ORDER BY avg DESC"""
    ).fetchall())
    # Attendance summary
    att_summary = rows_to_list(db.execute(
        """SELECT status, COUNT(*) AS cnt FROM attendance GROUP BY status"""
    ).fetchall())
    # Top students
    top_students = rows_to_list(db.execute(
        """SELECT s.first_name||' '||s.last_name AS name, AVG(g.value) AS avg
           FROM grades g JOIN students s ON s.id=g.student_id
           GROUP BY s.id ORDER BY avg DESC LIMIT 5"""
    ).fetchall())
    db.close()
    return render_template("reports.html",
                           module_avgs=module_avgs,
                           att_summary=att_summary,
                           top_students=top_students)


# ─────────────────────────── Run ────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
