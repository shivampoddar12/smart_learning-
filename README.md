# Smart Learning – AI-Based Web Learning Platform
### B.Tech Minor Project

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

## Project Structure

```
smart_learning/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── static/
│   └── uploads/           # Uploaded PDF files stored here
└── templates/
    ├── base.html          # Base layout (nav, dark mode, styling)
    ├── index.html         # Homepage with hero + features
    ├── study_material.html # Browse/filter study materials
    ├── quiz_home.html     # Quiz subject selection
    ├── quiz.html          # MCQ quiz page
    ├── quiz_result.html   # Quiz results & review
    ├── feedback.html      # Feedback & complaint form
    └── admin.html         # Admin panel (upload, manage, view)
```

## Features Implemented
- ✅ Homepage with hero section, stats, and feature cards
- ✅ Study Material browser (semester/subject filter)
- ✅ MCQ Quizzes with instant scoring and review
- ✅ Feedback & Complaint system with star rating
- ✅ Admin Panel (upload materials, view feedback, quiz scores)
- ✅ Dark Mode (toggle, persisted in localStorage)
- ✅ Responsive design (mobile-friendly)

## Coming Next
- AI-based topic explanations (LLM API)
- Language translation
- Student login/register
- MongoDB integration
- AI chatbot
