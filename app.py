from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'smartlearning_secret_2024'

# Register AI blueprint
from ai_routes import ai_bp
app.register_blueprint(ai_bp)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ── In-memory data store (replace with MongoDB in production) ──────────────
study_materials = [
    {"id": 1, "semester": 3, "subject": "Data Structures", "unit": 1, "title": "Arrays & Linked Lists", "filename": None, "uploaded": "2024-01-10"},
    {"id": 2, "semester": 3, "subject": "Data Structures", "unit": 2, "title": "Stacks & Queues", "filename": None, "uploaded": "2024-01-12"},
    {"id": 3, "semester": 4, "subject": "Operating Systems", "unit": 1, "title": "Process Management", "filename": None, "uploaded": "2024-01-15"},
    {"id": 4, "semester": 4, "subject": "DBMS", "unit": 1, "title": "ER Diagrams & Normalization", "filename": None, "uploaded": "2024-01-18"},
    {"id": 5, "semester": 5, "subject": "Computer Networks", "unit": 3, "title": "TCP/IP & OSI Model", "filename": None, "uploaded": "2024-01-20"},
]

quizzes = {
    "Data Structures": [
        {"q": "Which data structure uses LIFO order?", "options": ["Queue", "Stack", "Array", "Tree"], "answer": 1},
        {"q": "Time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"], "answer": 1},
        {"q": "Which is NOT a linear data structure?", "options": ["Array", "Stack", "Queue", "Tree"], "answer": 3},
    ],
    "Operating Systems": [
        {"q": "Which scheduling algorithm gives minimum waiting time?", "options": ["FCFS", "SJF", "Round Robin", "Priority"], "answer": 1},
        {"q": "What does PCB stand for?", "options": ["Process Control Block", "Program Counter Base", "Process Counter Block", "Program Control Base"], "answer": 0},
    ],
    "DBMS": [
        {"q": "What does ACID stand for?", "options": ["Atomicity, Consistency, Isolation, Durability", "Access, Control, Integrity, Data", "Atomic, Concurrent, Isolated, Durable", "None"], "answer": 0},
        {"q": "Which normal form removes transitive dependency?", "options": ["1NF", "2NF", "3NF", "BCNF"], "answer": 2},
    ],
}

feedbacks = []
complaints = []
quiz_scores = []

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    stats = {
        "materials": len(study_materials),
        "subjects": len(set(m["subject"] for m in study_materials)),
        "quizzes": sum(len(v) for v in quizzes.values()),
        "feedbacks": len(feedbacks),
    }
    recent_materials = study_materials[-5:][::-1]
    return render_template('index.html', stats=stats, recent_materials=recent_materials)

@app.route('/study-material')
def study_material():
    semester = request.args.get('semester', type=int)
    subject  = request.args.get('subject', '')
    filtered = study_materials
    if semester:
        filtered = [m for m in filtered if m['semester'] == semester]
    if subject:
        filtered = [m for m in filtered if m['subject'].lower() == subject.lower()]
    subjects  = sorted(set(m['subject'] for m in study_materials))
    semesters = sorted(set(m['semester'] for m in study_materials))
    return render_template('study_material.html', materials=filtered, subjects=subjects, semesters=semesters,
                           selected_sem=semester, selected_sub=subject)

@app.route('/quiz')
def quiz_home():
    subjects = list(quizzes.keys())
    return render_template('quiz_home.html', subjects=subjects)

@app.route('/quiz/<subject>')
def quiz(subject):
    questions = quizzes.get(subject, [])
    return render_template('quiz.html', subject=subject, questions=questions)

@app.route('/quiz/<subject>/submit', methods=['POST'])
def quiz_submit(subject):
    questions = quizzes.get(subject, [])
    score = 0
    results = []
    for i, q in enumerate(questions):
        user_ans = request.form.get(f'q{i}', type=int)
        correct  = (user_ans == q['answer'])
        if correct:
            score += 1
        results.append({"question": q['q'], "correct": correct,
                         "user": q['options'][user_ans] if user_ans is not None else "Not answered",
                         "answer": q['options'][q['answer']]})
    pct = round(score / len(questions) * 100) if questions else 0
    quiz_scores.append({"subject": subject, "score": score, "total": len(questions), "pct": pct, "date": datetime.now().strftime("%d %b %Y")})
    return render_template('quiz_result.html', subject=subject, score=score, total=len(questions), pct=pct, results=results)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        entry = {
            "name": request.form.get('name', 'Anonymous'),
            "type": request.form.get('type'),
            "message": request.form.get('message'),
            "rating": request.form.get('rating', '5'),
            "date": datetime.now().strftime("%d %b %Y"),
            "status": "Pending"
        }
        if entry['type'] == 'complaint':
            complaints.append(entry)
        else:
            feedbacks.append(entry)
        flash('Thank you! Your submission has been received.', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html', feedbacks=feedbacks[-5:])

@app.route('/admin')
def admin():
    return render_template('admin.html', materials=study_materials, feedbacks=feedbacks,
                           complaints=complaints, scores=quiz_scores)

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    sem     = request.form.get('semester', type=int)
    subject = request.form.get('subject')
    unit    = request.form.get('unit', type=int)
    title   = request.form.get('title')
    file    = request.files.get('pdf')
    fname   = None
    if file and file.filename.endswith('.pdf'):
        fname = f"{subject.replace(' ','_')}_{unit}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    study_materials.append({
        "id": len(study_materials) + 1,
        "semester": sem, "subject": subject, "unit": unit,
        "title": title, "filename": fname,
        "uploaded": datetime.now().strftime("%Y-%m-%d")
    })
    flash('Material uploaded successfully!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
