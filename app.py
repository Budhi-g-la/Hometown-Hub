
import os
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATABASE = "hometown_hub.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    conn = get_db()
    posts = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC"
    ).fetchall()
    events = conn.execute(
        "SELECT * FROM events ORDER BY event_date"
    ).fetchall()
    conn.close()
    return render_template("index.html", posts=posts, events=events)


@app.route("/create-post", methods=["POST"])
def create_post():
    name = request.form.get("name", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if name and title and content:
        conn = get_db()
        conn.execute(
            "INSERT INTO posts (name, title, content) VALUES (?, ?, ?)",
            (name, title, content)
        )
        conn.commit()
        conn.close()
        flash("Your post was published!", "success")
    else:
        flash("Please fill in all post fields.", "danger")

    return redirect(url_for("index"))


@app.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    name = request.form.get("name", "").strip()
    content = request.form.get("content", "").strip()

    if name and content:
        conn = get_db()
        conn.execute(
            "INSERT INTO comments (post_id, name, content) VALUES (?, ?, ?)",
            (post_id, name, content)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        correct_username = os.environ.get("ADMIN_USERNAME", "admin")
        correct_password = os.environ.get("ADMIN_PASSWORD", "admin123")

        if username == correct_username and password == correct_password:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect username or password.", "danger")

    return render_template("admin_login.html")


@app.route("/admin")
@admin_required
def admin():
    conn = get_db()
    posts = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC"
    ).fetchall()
    events = conn.execute(
        "SELECT * FROM events ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("admin.html", posts=posts, events=events)


@app.route("/admin/delete/<int:post_id>", methods=["POST"])
@admin_required
def delete_post(post_id):
    conn = get_db()
    conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    flash("Post deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/add-event", methods=["POST"])
@admin_required
def add_event():
    title = request.form.get("title", "").strip()
    event_date = request.form.get("event_date", "").strip()
    description = request.form.get("description", "").strip()

    if title:
        conn = get_db()
        conn.execute(
            "INSERT INTO events (title, event_date, description) VALUES (?, ?, ?)",
            (title, event_date, description)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("admin"))


@app.route("/admin/delete-event/<int:event_id>", methods=["POST"])
@admin_required
def delete_event(event_id):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
