"""
AI Features for Smart Learning
Routes: /ai/explain, /ai/questions, /ai/chat, /ai/translate
Uses OpenAI API (gpt-3.5-turbo)
"""
from flask import Blueprint, request, jsonify, render_template, session
import openai, os, json

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# ── Set your OpenAI API key in environment: export OPENAI_API_KEY=sk-...
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

def call_openai(system_prompt, user_prompt, max_tokens=800):
    """Single helper to call OpenAI chat completion."""
    if not openai.api_key:
        return {"error": "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."}
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return {"result": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"error": str(e)}

# ── AI Explanation ──────────────────────────────────────────────────────────
@ai_bp.route('/explain', methods=['GET', 'POST'])
def explain():
    result = None
    if request.method == 'POST':
        topic   = request.form.get('topic', '').strip()
        subject = request.form.get('subject', '').strip()
        level   = request.form.get('level', 'simple')

        system = (
            "You are a helpful B.Tech professor. Explain topics clearly for engineering students. "
            "Use simple language, bullet points, and real-world examples. "
            "Format your response with: 1) Simple explanation (2-3 sentences) "
            "2) Key concepts (bullet list) 3) One real-world example."
        )
        user = f"Explain the topic '{topic}' from {subject} in a {level} way for B.Tech students."
        result = call_openai(system, user, max_tokens=600)
        result['topic'] = topic
        result['subject'] = subject

    subjects = ["Data Structures", "Operating Systems", "DBMS", "Computer Networks",
                "Algorithms", "Software Engineering", "Computer Architecture"]
    return render_template('ai_explain.html', result=result, subjects=subjects)


# ── Important Questions Generator ──────────────────────────────────────────
@ai_bp.route('/questions', methods=['GET', 'POST'])
def questions():
    result = None
    if request.method == 'POST':
        topic   = request.form.get('topic', '').strip()
        subject = request.form.get('subject', '').strip()
        qtype   = request.form.get('qtype', 'both')

        system = (
            "You are a B.Tech exam expert. Generate exam-oriented questions. "
            "Format strictly as JSON with keys: 'one_mark' (list of 5 questions) "
            "and 'five_mark' (list of 3 questions with brief answer hints). "
            "Return ONLY valid JSON, no markdown fences."
        )
        if qtype == '1mark':
            user = f"Generate 8 important 1-mark questions on '{topic}' from {subject} for B.Tech exam."
        elif qtype == '5mark':
            user = f"Generate 5 important 5-mark questions with answer hints on '{topic}' from {subject} for B.Tech exam."
        else:
            user = f"Generate important exam questions on '{topic}' from {subject}. Include 1-mark and 5-mark questions."

        raw = call_openai(system, user, max_tokens=700)
        if 'result' in raw:
            try:
                parsed = json.loads(raw['result'])
                result = {'data': parsed, 'topic': topic, 'subject': subject}
            except json.JSONDecodeError:
                # fallback: return raw text
                result = {'raw': raw['result'], 'topic': topic, 'subject': subject}
        else:
            result = {'error': raw.get('error'), 'topic': topic, 'subject': subject}

    subjects = ["Data Structures", "Operating Systems", "DBMS", "Computer Networks",
                "Algorithms", "Software Engineering", "Computer Architecture"]
    return render_template('ai_questions.html', result=result, subjects=subjects)


# ── AI Chatbot ──────────────────────────────────────────────────────────────
@ai_bp.route('/chat', methods=['GET'])
def chat():
    return render_template('ai_chat.html')

@ai_bp.route('/chat/message', methods=['POST'])
def chat_message():
    data    = request.get_json()
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not openai.api_key:
        return jsonify({"error": "OpenAI API key not set."})

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        messages = [
            {"role": "system", "content": (
                "You are SmartBot, an AI academic assistant for B.Tech engineering students. "
                "You help with: explaining concepts, solving doubts, generating practice questions, "
                "summarizing topics, and exam preparation. "
                "Be concise, friendly, and student-focused. Use bullet points for clarity."
            )}
        ]
        # Add conversation history (last 6 messages)
        for h in history[-6:]:
            messages.append({"role": h['role'], "content": h['content']})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)})


# ── Translation ─────────────────────────────────────────────────────────────
@ai_bp.route('/translate', methods=['GET', 'POST'])
def translate():
    result = None
    if request.method == 'POST':
        text     = request.form.get('text', '').strip()
        language = request.form.get('language', 'Hindi')
        system = (
            "You are a professional translator for educational content. "
            "Translate the given engineering/academic text clearly. "
            "Preserve technical terms in English inside brackets if needed."
        )
        user = f"Translate this educational content to {language}:\n\n{text}"
        result = call_openai(system, user, max_tokens=600)
        result['original'] = text
        result['language'] = language

    languages = ["Hindi", "Gujarati", "Marathi", "Tamil", "Telugu",
                 "Bengali", "Kannada", "Malayalam", "Punjabi"]
    return render_template('ai_translate.html', result=result, languages=languages)
