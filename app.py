"""
MyCoGuard (MCG) - Mushroom Health & Safety Analyzer
=====================================================
Main Flask application: user auth (register / login / forgot password),
image upload, AI-style analysis, and downloadable PDF reports.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""
import os
import uuid
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request,
                    send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import database as db
from classifier import analyze_image, build_reference_features
from report_generator import generate_report_pdf

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE, "static", "img", "uploads")
REPORT_DIR = os.path.join(BASE, "reports")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("MCG_SECRET_KEY", "dev-secret-change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads

SECURITY_QUESTIONS = [
    "What is your favourite mushroom dish?",
    "What was the name of your first pet?",
    "What city were you born in?",
    "What is your mother's maiden name?",
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {"current_user": session.get("username")}


# ---------------------------------------------------------------- AUTH ----

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        security_question = request.form.get("security_question", "")
        security_answer = request.form.get("security_answer", "").strip().lower()

        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if not security_answer:
            errors.append("Please answer the security question (used for password recovery).")
        if db.get_user_by_username(username):
            errors.append("That username is already taken.")
        if db.get_user_by_email(email):
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", questions=SECURITY_QUESTIONS,
                                    form=request.form)

        db.create_user(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            security_question=security_question,
            security_answer_hash=generate_password_hash(security_answer),
        )
        flash("Account created! You can log in now.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", questions=SECURITY_QUESTIONS, form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.get_user_by_username(identifier) or db.get_user_by_email(identifier.lower())
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)

        flash("Invalid username/email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Step 1: look up the account and reveal its security question."""
    user = None
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        user = db.get_user_by_username(identifier) or db.get_user_by_email(identifier.lower())
        if not user:
            flash("No account found with that username or email.", "error")
        else:
            session["reset_user_id"] = user["id"]
            return redirect(url_for("reset_password"))
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Step 2: answer the security question and set a new password."""
    user_id = session.get("reset_user_id")
    if not user_id:
        flash("Please start the password reset process again.", "error")
        return redirect(url_for("forgot_password"))

    user = db.get_user_by_id(user_id)
    if not user:
        session.pop("reset_user_id", None)
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        answer = request.form.get("security_answer", "").strip().lower()
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not check_password_hash(user["security_answer_hash"], answer):
            flash("That answer doesn't match our records.", "error")
        elif len(new_password) < 6:
            flash("New password must be at least 6 characters.", "error")
        elif new_password != confirm:
            flash("Passwords do not match.", "error")
        else:
            db.update_password(user["id"], generate_password_hash(new_password))
            session.pop("reset_user_id", None)
            flash("Password updated! Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html", question=user["security_question"],
                            username=user["username"])


# ----------------------------------------------------------- DASHBOARD ----

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    reports = db.list_reports(session["user_id"], limit=6)
    return render_template("dashboard.html", reports=reports)


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    file = request.files.get("mushroom_image")
    if not file or file.filename == "":
        flash("Please choose a mushroom photo to analyze.", "error")
        return redirect(url_for("dashboard"))
    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a JPG, PNG or WEBP image.", "error")
        return redirect(url_for("dashboard"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(UPLOAD_DIR, unique_name)
    file.save(saved_path)

    try:
        result = analyze_image(saved_path)
    except Exception as e:
        flash(f"Could not analyze that image: {e}", "error")
        return redirect(url_for("dashboard"))

    match = result["match"]
    pdf_name = f"MCG_Report_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(REPORT_DIR, pdf_name)
    generate_report_pdf(
        pdf_path,
        user=session["username"],
        result=result,
        uploaded_image_path=saved_path,
    )

    report_id = db.save_report(
        user_id=session["user_id"],
        mushroom_name=match["display_name"],
        scientific_name=match["scientific_name"],
        category=result["category"],
        category_label=result["meta"]["label"],
        confidence=result["confidence"],
        image_path=f"img/uploads/{unique_name}",
        pdf_path=pdf_name,
    )

    return redirect(url_for("result", report_id=report_id))


@app.route("/result/<int:report_id>")
@login_required
def result(report_id):
    report = db.get_report(report_id, session["user_id"])
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for("dashboard"))
    return render_template("result.html", report=report)


@app.route("/report/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = db.get_report(report_id, session["user_id"])
    if not report or not report["pdf_path"]:
        flash("Report not found.", "error")
        return redirect(url_for("dashboard"))
    pdf_path = os.path.join(REPORT_DIR, report["pdf_path"])
    if not os.path.exists(pdf_path):
        flash("The report file is missing.", "error")
        return redirect(url_for("dashboard"))
    download_name = f"MyCoGuard_{report['mushroom_name'].replace(' ', '_')}_Report.pdf"
    return send_file(pdf_path, as_attachment=True, download_name=download_name)


@app.route("/history")
@login_required
def history():
    reports = db.list_reports(session["user_id"], limit=200)
    return render_template("history.html", reports=reports)


if __name__ == "__main__":
    db.init_db()
    build_reference_features()
    app.run(debug=True, host="0.0.0.0", port=5000)
