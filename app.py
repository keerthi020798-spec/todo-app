from flask import Flask, request, jsonify, render_template_string
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import os
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

DB_HOST = os.environ.get("DB_HOST", "postgres-service")
DB_NAME = os.environ.get("DB_NAME", "tododb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

def init_db():
    for attempt in range(10):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(3)

PAGE = """
<!DOCTYPE html>
<html>
<head><title>To-Do List</title></head>
<body style="font-family: sans-serif; max-width: 500px; margin: 50px auto;">
    <h2>My To-Do List</h2>
    <form method="post" action="/tasks/add">
        <input type="text" name="title" placeholder="Add a new task" required>
        <button type="submit">+</button>
    </form>
    <ul style="list-style: none; padding: 0;">
    {% for task in tasks %}
        <li style="margin: 10px 0;">
            {% if task[2] %}<s>{{ task[1] }}</s>{% else %}{{ task[1] }}{% endif %}
            <form style="display:inline" method="post" action="/tasks/{{ task[0] }}/complete">
                <button>✓</button>
            </form>
            <form style="display:inline" method="post" action="/tasks/{{ task[0] }}/delete">
                <button>x</button>
            </form>
        </li>
    {% endfor %}
    </ul>
</body>
</html>
"""

@app.route("/")
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, completed FROM tasks ORDER BY id")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(PAGE, tasks=tasks)

@app.route("/tasks", methods=["GET"])
def list_tasks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, completed FROM tasks ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "title": r[1], "completed": r[2]} for r in rows])

@app.route("/tasks/add", methods=["POST"])
def add_task():
    title = request.form.get("title") or request.json.get("title")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
    conn.commit()
    cur.close()
    conn.close()
    return home() if request.form else jsonify({"status": "added"})

@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = TRUE WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return home()

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return home()

@app.route("/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
