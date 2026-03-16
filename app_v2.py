"""
app_v2.py — Smart Learning v2
MongoDB + Login System + AI Features
Run: python app_v2.py
Set env vars: OPENAI_API_KEY, MONGO_URI (optional, falls back to in-memory)
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os, database as db_layer
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smartlearning_secret_2024_v2")
app.config["UPLOAD_FOLDER"]       = "static/uploads"
app.config["MAX_CONTENT_LENGTH"]  = 16 * 1024 * 1024

# ── Register blueprints ─────────────────────────────────────────────────────
from auth      import auth_bp, get_current_user, login_required, admin_required
from ai_routes import ai_bp
app.register_blueprint(auth_bp)
app.register_blueprint(ai_bp)

# ── Context processor — inject user into every template ────────────────────
@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


# ════════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    stats            = db_layer.get_stats()
    recent_materials = db_layer.get_recent_materials(5)
    return render_template("index.html", stats=stats, recent_materials=recent_materials)


# ════════════════════════════════════════════════════════════════════════════
# STUDY MATERIALS
# ════════════════════════════════════════════════════════════════════════════
@app.route("/study-material")
def study_material():
    semester = request.args.get("semester", type=int)
    subject  = request.args.get("subject", "")
    materials = db_layer.get_materials(semester=semester, subject=subject)
    subjects  = db_layer.get_all_subjects()
    semesters = db_layer.get_all_semesters()
    return render_template("study_material.html",
                           materials=materials, subjects=subjects,
                           semesters=semesters,
                           selected_sem=semester, selected_sub=subject)


# ════════════════════════════════════════════════════════════════════════════
# QUIZ
# ════════════════════════════════════════════════════════════════════════════
@app.route("/quiz")
def quiz_home():
    subjects = db_layer.get_quiz_subjects()
    return render_template("quiz_home.html", subjects=subjects)

@app.route("/quiz/<subject>")
def quiz(subject):
    questions = db_layer.get_quiz_questions(subject)
    return render_template("quiz.html", subject=subject, questions=questions)

@app.route("/quiz/<subject>/submit", methods=["POST"])
def quiz_submit(subject):
    questions = db_layer.get_quiz_questions(subject)
    score, results = 0, []
    for i, q in enumerate(questions):
        user_ans = request.form.get(f"q{i}", type=int)
        correct  = (user_ans == q["answer"])
        if correct: score += 1
        results.append({
            "question": q["q"], "correct": correct,
            "user":   q["options"][user_ans] if user_ans is not None else "Not answered",
            "answer": q["options"][q["answer"]]
        })
    pct     = round(score / len(questions) * 100) if questions else 0
    user_id = session.get("user_id", "anonymous")
    db_layer.save_score(user_id, subject, score, len(questions))
    return render_template("quiz_result.html",
                           subject=subject, score=score,
                           total=len(questions), pct=pct, results=results)


# ════════════════════════════════════════════════════════════════════════════
# FEEDBACK
# ════════════════════════════════════════════════════════════════════════════
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        db_layer.add_feedback(
            name    = request.form.get("name", "Anonymous"),
            ftype   = request.form.get("type", "feedback"),
            message = request.form.get("message", ""),
            rating  = request.form.get("rating", "5"),
        )
        flash("Thank you! Your submission has been received.", "success")
        return redirect(url_for("feedback"))
    feedbacks = db_layer.get_feedbacks(5)
    return render_template("feedback.html", feedbacks=feedbacks)


# ════════════════════════════════════════════════════════════════════════════
# ADMIN
# ════════════════════════════════════════════════════════════════════════════
@app.route("/admin")
def admin():
    materials  = db_layer.get_materials()
    feedbacks  = db_layer.get_all_feedbacks()
    complaints = db_layer.get_complaints()
    scores     = db_layer.get_scores()
    users      = db_layer.get_all_users()
    return render_template("admin.html",
                           materials=materials, feedbacks=feedbacks,
                           complaints=complaints, scores=scores, users=users)

@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    sem     = request.form.get("semester", type=int)
    subject = request.form.get("subject", "")
    unit    = request.form.get("unit",    type=int)
    title   = request.form.get("title",   "")
    file    = request.files.get("pdf")
    fname   = None
    if file and file.filename.endswith(".pdf"):
        fname = secure_filename(f"{subject.replace(' ','_')}_{unit}_{file.filename}")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
    db_layer.add_material(sem, subject, unit, title, fname)
    flash("Material uploaded successfully!", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True)
