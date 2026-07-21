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
```
"# Smart_Campus" 
"# Smart_Campus" 
<p align="center">
  <a href="https://github.com/Mourad%20Ait%20Oumaach">
    <img src="https://capsule-render.vercel.app/api?type=transparent&fontColor=2ea043&fontSize=54&height=90&width=634&text=Hello!%20I'm%20Mourad" alt="Hello! I&#39;m Mourad" />
  </a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Caveat&weight=600&size=26&pause=1000&color=2f81f7&center=true&vCenter=true&width=505&height=44&lines=here%20is%20my%20smart%20compus%20project" alt="Typing headlines" />
</p>

### 🛠️ Tech Stack

<p align="left">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

### 📊 GitHub Stats

<p align="center">
  <img height="165" src="https://github-readme-stats-five-sigma-99.vercel.app/api?username=Mourad%20Ait%20Oumaach&show_icons=true&theme=tokyonight&title_color=2ea043&icon_color=2ea043&hide_border=true&bg_color=00000000&count_private=true" alt="stats" />
  <img height="165" src="https://github-readme-stats-five-sigma-99.vercel.app/api/top-langs/?username=Mourad%20Ait%20Oumaach&layout=compact&theme=tokyonight&title_color=2ea043&icon_color=2ea043&hide_border=true&bg_color=00000000&langs_count=8" alt="top langs" />
</p>

### 📈 Contribution Graph

<p align="center">
  <img width="100%" src="https://github-readme-activity-graph.vercel.app/graph?username=Mourad%20Ait%20Oumaach&bg_color=00000000&color=2ea043&line=2ea043&point=c9d1d9&area=true&hide_border=true" alt="activity graph" />
</p>

### 💭 Dev Quote

<p align="center">
  <img src="https://quotes-github-readme.vercel.app/api?type=horizontal&theme=tokyonight" alt="Dev quote" />
</p>

---
<p align="center"><i>⭐️ From <a href="https://github.com/Mourad%20Ait%20Oumaach">Mourad Ait Oumaach</a></i></p>
