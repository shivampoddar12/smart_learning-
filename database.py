"""
database.py — MongoDB integration for Smart Learning
Replaces all in-memory lists in app.py with real MongoDB operations.
Uses PyMongo. Falls back to in-memory if MongoDB is not available.
"""
import os
from datetime import datetime
from bson import ObjectId

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = "smart_learning"

# ── Try connecting to MongoDB ───────────────────────────────────────────────
try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import ConnectionFailure
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    _client.admin.command("ping")          # raises if unreachable
    db = _client[DB_NAME]
    MONGO_AVAILABLE = True
    print(f"[DB] Connected to MongoDB at {MONGO_URI} → database: {DB_NAME}")
except Exception as e:
    db = None
    MONGO_AVAILABLE = False
    print(f"[DB] MongoDB unavailable ({e}). Running with in-memory fallback.")


# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA — inserted only when collections are empty
# ══════════════════════════════════════════════════════════════════════════════
_SEED_MATERIALS = [
    {"semester": 3, "subject": "Data Structures",    "unit": 1, "title": "Arrays & Linked Lists",      "filename": None, "uploaded": "2024-01-10"},
    {"semester": 3, "subject": "Data Structures",    "unit": 2, "title": "Stacks & Queues",             "filename": None, "uploaded": "2024-01-12"},
    {"semester": 4, "subject": "Operating Systems",  "unit": 1, "title": "Process Management",          "filename": None, "uploaded": "2024-01-15"},
    {"semester": 4, "subject": "DBMS",               "unit": 1, "title": "ER Diagrams & Normalization", "filename": None, "uploaded": "2024-01-18"},
    {"semester": 5, "subject": "Computer Networks",  "unit": 3, "title": "TCP/IP & OSI Model",          "filename": None, "uploaded": "2024-01-20"},
]

_SEED_QUIZZES = {
    "Data Structures": [
        {"q": "Which data structure uses LIFO order?",               "options": ["Queue","Stack","Array","Tree"],          "answer": 1},
        {"q": "Time complexity of binary search?",                    "options": ["O(n)","O(log n)","O(n²)","O(1)"],       "answer": 1},
        {"q": "Which is NOT a linear data structure?",               "options": ["Array","Stack","Queue","Tree"],          "answer": 3},
    ],
    "Operating Systems": [
        {"q": "Which scheduling algo gives minimum average waiting time?", "options": ["FCFS","SJF","Round Robin","Priority"], "answer": 1},
        {"q": "PCB stands for?",                                          "options": ["Process Control Block","Program Counter Base","Process Counter Block","Program Control Base"], "answer": 0},
    ],
    "DBMS": [
        {"q": "ACID stands for?",                 "options": ["Atomicity,Consistency,Isolation,Durability","Access,Control,Integrity,Data","Atomic,Concurrent,Isolated,Durable","None"], "answer": 0},
        {"q": "Which NF removes transitive dependency?", "options": ["1NF","2NF","3NF","BCNF"], "answer": 2},
    ],
}

# ── In-memory fallback store ────────────────────────────────────────────────
_mem = {
    "materials":  [dict(id=i+1, **m) for i, m in enumerate(_SEED_MATERIALS)],
    "feedbacks":  [],
    "complaints": [],
    "scores":     [],
    "users":      [],
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — convert ObjectId to str for templates
# ══════════════════════════════════════════════════════════════════════════════
def _clean(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def _clean_list(docs):
    return [_clean(d) for d in docs]


# ══════════════════════════════════════════════════════════════════════════════
# STUDY MATERIALS
# ══════════════════════════════════════════════════════════════════════════════
def get_materials(semester=None, subject=None):
    if MONGO_AVAILABLE:
        col = db["materials"]
        if col.count_documents({}) == 0:
            col.insert_many([m.copy() for m in _SEED_MATERIALS])
        query = {}
        if semester: query["semester"] = semester
        if subject:  query["subject"]  = {"$regex": subject, "$options": "i"}
        return _clean_list(list(col.find(query).sort("uploaded", DESCENDING)))
    # fallback
    result = _mem["materials"]
    if semester: result = [m for m in result if m["semester"] == semester]
    if subject:  result = [m for m in result if m["subject"].lower() == subject.lower()]
    return result

def add_material(semester, subject, unit, title, filename):
    doc = {"semester": semester, "subject": subject, "unit": unit,
           "title": title, "filename": filename,
           "uploaded": datetime.now().strftime("%Y-%m-%d")}
    if MONGO_AVAILABLE:
        result = db["materials"].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    doc["id"] = len(_mem["materials"]) + 1
    _mem["materials"].append(doc)
    return doc

def get_all_subjects():
    if MONGO_AVAILABLE:
        return sorted(db["materials"].distinct("subject"))
    return sorted(set(m["subject"] for m in _mem["materials"]))

def get_all_semesters():
    if MONGO_AVAILABLE:
        return sorted(db["materials"].distinct("semester"))
    return sorted(set(m["semester"] for m in _mem["materials"]))

def get_recent_materials(n=5):
    if MONGO_AVAILABLE:
        return _clean_list(list(db["materials"].find().sort("uploaded", DESCENDING).limit(n)))
    return list(reversed(_mem["materials"]))[:n]


# ══════════════════════════════════════════════════════════════════════════════
# QUIZZES  (stored in MongoDB for easy admin editing)
# ══════════════════════════════════════════════════════════════════════════════
def get_quiz_subjects():
    if MONGO_AVAILABLE:
        col = db["quizzes"]
        if col.count_documents({}) == 0:
            for subj, qs in _SEED_QUIZZES.items():
                col.insert_one({"subject": subj, "questions": qs})
        return [d["subject"] for d in col.find({}, {"subject": 1})]
    return list(_SEED_QUIZZES.keys())

def get_quiz_questions(subject):
    if MONGO_AVAILABLE:
        doc = db["quizzes"].find_one({"subject": subject})
        return doc["questions"] if doc else []
    return _SEED_QUIZZES.get(subject, [])


# ══════════════════════════════════════════════════════════════════════════════
# FEEDBACK & COMPLAINTS
# ══════════════════════════════════════════════════════════════════════════════
def add_feedback(name, ftype, message, rating):
    doc = {"name": name, "type": ftype, "message": message,
           "rating": rating, "date": datetime.now().strftime("%d %b %Y"),
           "status": "Pending"}
    if MONGO_AVAILABLE:
        col = "complaints" if ftype == "complaint" else "feedbacks"
        result = db[col].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    col = "complaints" if ftype == "complaint" else "feedbacks"
    _mem[col].append(doc)
    return doc

def get_feedbacks(limit=5):
    if MONGO_AVAILABLE:
        return _clean_list(list(db["feedbacks"].find().sort("date", DESCENDING).limit(limit)))
    return list(reversed(_mem["feedbacks"]))[:limit]

def get_complaints():
    if MONGO_AVAILABLE:
        return _clean_list(list(db["complaints"].find().sort("date", DESCENDING)))
    return list(reversed(_mem["complaints"]))

def get_all_feedbacks():
    if MONGO_AVAILABLE:
        return _clean_list(list(db["feedbacks"].find().sort("date", DESCENDING)))
    return list(reversed(_mem["feedbacks"]))


# ══════════════════════════════════════════════════════════════════════════════
# QUIZ SCORES
# ══════════════════════════════════════════════════════════════════════════════
def save_score(user_id, subject, score, total):
    pct = round(score / total * 100) if total else 0
    doc = {"user_id": user_id, "subject": subject, "score": score,
           "total": total, "pct": pct,
           "date": datetime.now().strftime("%d %b %Y")}
    if MONGO_AVAILABLE:
        result = db["scores"].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    _mem["scores"].append(doc)
    return doc

def get_scores(limit=50):
    if MONGO_AVAILABLE:
        return _clean_list(list(db["scores"].find().sort("date", DESCENDING).limit(limit)))
    return list(reversed(_mem["scores"]))


# ══════════════════════════════════════════════════════════════════════════════
# USERS  (for login system)
# ══════════════════════════════════════════════════════════════════════════════
def create_user(name, email, password_hash, role="student"):
    doc = {"name": name, "email": email.lower(), "password": password_hash,
           "role": role, "semester": 1,
           "created": datetime.now().strftime("%d %b %Y"),
           "active": True}
    if MONGO_AVAILABLE:
        if db["users"].find_one({"email": email.lower()}):
            return None   # duplicate
        result = db["users"].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    if any(u["email"] == email.lower() for u in _mem["users"]):
        return None
    doc["id"] = len(_mem["users"]) + 1
    _mem["users"].append(doc)
    return doc

def find_user_by_email(email):
    if MONGO_AVAILABLE:
        return _clean(db["users"].find_one({"email": email.lower()}))
    return next((u for u in _mem["users"] if u["email"] == email.lower()), None)

def find_user_by_id(uid):
    if MONGO_AVAILABLE:
        try:
            return _clean(db["users"].find_one({"_id": ObjectId(uid)}))
        except Exception:
            return None
    return next((u for u in _mem["users"] if str(u.get("id")) == str(uid)), None)

def get_all_users():
    if MONGO_AVAILABLE:
        return _clean_list(list(db["users"].find({}, {"password": 0})))
    return [{k:v for k,v in u.items() if k != "password"} for u in _mem["users"]]


# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════
def get_stats():
    if MONGO_AVAILABLE:
        return {
            "materials":  db["materials"].count_documents({}),
            "subjects":   len(db["materials"].distinct("subject")),
            "quizzes":    sum(len(d.get("questions",[])) for d in db["quizzes"].find()),
            "feedbacks":  db["feedbacks"].count_documents({}),
            "users":      db["users"].count_documents({}),
        }
    return {
        "materials":  len(_mem["materials"]),
        "subjects":   len(set(m["subject"] for m in _mem["materials"])),
        "quizzes":    sum(len(v) for v in _SEED_QUIZZES.values()),
        "feedbacks":  len(_mem["feedbacks"]),
        "users":      len(_mem["users"]),
    }
