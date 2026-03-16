# Smart Learning v2 — Setup Guide

## What's new in v2
- ✅ MongoDB integration (with in-memory fallback)
- ✅ Student register / login / logout / profile
- ✅ Password hashing (PBKDF2-SHA256)
- ✅ Session-based authentication
- ✅ AI features: Explain, Questions, SmartBot, Translate

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export OPENAI_API_KEY=sk-...          # required for AI features
export MONGO_URI=mongodb://localhost:27017/  # optional (falls back to memory)
export SECRET_KEY=your-secret-key     # optional (has default)

# 3. Run
python app_v2.py

# 4. Open browser
http://localhost:5000
```

## Routes

| Route | Description |
|---|---|
| `/` | Home — stats, recent materials |
| `/study-material` | Browse PDFs by semester/subject |
| `/quiz` | MCQ quiz list |
| `/feedback` | Feedback & complaint form |
| `/admin` | Admin panel (upload, manage) |
| `/auth/register` | Student registration |
| `/auth/login` | Login |
| `/auth/logout` | Logout |
| `/auth/profile` | My profile |
| `/ai/explain` | AI topic explanation |
| `/ai/questions` | AI question generator |
| `/ai/chat` | SmartBot chatbot |
| `/ai/translate` | Language translation |

## MongoDB Collections

| Collection | Purpose |
|---|---|
| `materials` | Study PDFs (semester, subject, unit) |
| `quizzes` | Question banks per subject |
| `feedbacks` | Student feedback |
| `complaints` | Student complaints |
| `scores` | Quiz results |
| `users` | Registered student accounts |

## Without MongoDB
The app runs fine without MongoDB — all data is stored in memory (resets on restart).
Set MONGO_URI to connect to a real database for persistent data.

## MongoDB Atlas (Free Cloud DB)
1. Sign up at https://mongodb.com/atlas
2. Create a free cluster
3. Get connection string
4. Set: `export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/"`
