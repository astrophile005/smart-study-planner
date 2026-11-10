
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("study.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()



@app.route("/")
def home():
    search = request.args.get("search", "")
    priority = request.args.get("priority", "")
    status = request.args.get("status", "")

    conn = get_db_connection()

    query = """
        SELECT * FROM tasks
        WHERE (title LIKE ? OR subject LIKE ?)
    """
    params = ['%' + search + '%', '%' + search + '%']

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    if status == "pending":
        query += " AND completed = 0"
    elif status == "completed":
        query += " AND completed = 1"

    query += " ORDER BY due_date"

    tasks = conn.execute(query, params).fetchall()

    # Overall dashboard analytics
    all_tasks = conn.execute(
        "SELECT * FROM tasks"
    ).fetchall()

    overdue_count = sum(
        1 for task in all_tasks
        if not task["completed"] and task["due_date"] < date.today().isoformat()
    )

    high_count = sum(
        1 for task in all_tasks if task["priority"] == "High"
    )

    medium_count = sum(
        1 for task in all_tasks if task["priority"] == "Medium"
    )

    low_count = sum(
        1 for task in all_tasks if task["priority"] == "Low"
    )

    total = len(tasks)
    completed = sum(task["completed"] for task in tasks)
    pending = total - completed

    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        pending=pending,
        completed=completed,
        overdue_count=overdue_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        search=search,
        priority=priority,
        status=status,
        today=date.today().isoformat()
    )





@app.route("/add", methods=["POST"])
def add_task():
    title = request.form["title"]
    subject = request.form["subject"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO tasks (title, subject, due_date, priority)
        VALUES (?, ?, ?, ?)
    """, (title, subject, due_date, priority))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    conn = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        conn.execute("""
            UPDATE tasks
            SET title = ?, subject = ?, due_date = ?, priority = ?
            WHERE id = ?
        """, (title, subject, due_date, priority, task_id))

        conn.commit()
        conn.close()
        return redirect("/")

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", task=task)

@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE tasks SET completed = 1 WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()
    return redirect("/")


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
