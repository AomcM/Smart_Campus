# SmartCampus — Campus Management System
Python + Flask + SQLite web application.

## Setup

```bash
pip install flask
python app.py
```

Open http://localhost:5000

## Demo accounts

| Username  | Password    | Role             |
|-----------|-------------|------------------|
| admin     | admin123    | Administrator    |
| teacher1  | teacher123  | Teacher          |
| student1  | student123  | Student          |
| resto     | resto123    | Restaurant Staff |

## Features by role

### Admin
- Dashboard with statistics
- Full CRUD: Students, Teachers, Modules, Rooms
- Schedule (weekly timetable grid) — add/remove sessions
- Grades — add/delete grades for any student
- Attendance — mark/delete attendance records
- Restaurant — manage menu & orders
- Reports — grade averages, attendance breakdown, top students

### Teacher
- Dashboard with own modules
- View schedule, enter grades, mark attendance

### Student
- Dashboard with personal grades
- View schedule, own grades, own attendance
- Place restaurant orders

### Restaurant Staff
- Dashboard with order counts
- Manage menu items (add/remove)
- Process orders (Pending → Ready → Served)

## Project structure

```
smartcampus/
├── app.py              # Flask routes
├── database.py         # SQLite schema + seed data
├── requirements.txt
└── templates/
    ├── base.html                   # Layout with sidebar
    ├── login.html
    ├── dashboard_admin.html
    ├── dashboard_teacher.html
    ├── dashboard_student.html
    ├── dashboard_restaurant.html
    ├── students.html / student_form.html
    ├── teachers.html / teacher_form.html
    ├── modules.html  / module_form.html
    ├── rooms.html    / room_form.html
    ├── schedule.html
    ├── grades.html
    ├── attendance.html
    ├── restaurant.html
    └── reports.html
