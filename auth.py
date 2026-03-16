"""
auth.py — Student Register/Login system for Smart Learning
Uses Flask sessions + Werkzeug password hashing.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import database as db_layer

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Decorators ──────────────────────────────────────────────────────────────
def login_required(f):
    """Redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Redirect if user is not admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "error")
            return redirect(url_for("auth.login"))
        if session.get("user_role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    """Return current user dict from session, or None."""
    if "user_id" not in session:
        return None
    return db_layer.find_user_by_id(session["user_id"])


# ── Register ────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")
        semester = request.form.get("semester", "1")

        # Validation
        errors = []
        if not name:             errors.append("Name is required.")
        if not email or "@" not in email: errors.append("Valid email is required.")
        if len(password) < 6:    errors.append("Password must be at least 6 characters.")
        if password != confirm:  errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth_register.html",
                                   name=name, email=email, semester=semester)

        hashed = generate_password_hash(password)
        user = db_layer.create_user(name, email, hashed, role="student")

        if user is None:
            flash("An account with this email already exists.", "error")
            return render_template("auth_register.html", email=email)

        # Auto-login after register
        _set_session(user)
        flash(f"Welcome, {name}! Your account has been created.", "success")
        return redirect(url_for("index"))

    return render_template("auth_register.html")


# ── Login ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    next_url = request.args.get("next", "")

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = db_layer.find_user_by_email(email)
        if not user or not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "error")
            return render_template("auth_login.html", email=email, next=next_url)

        if not user.get("active", True):
            flash("Your account has been deactivated. Contact admin.", "error")
            return render_template("auth_login.html", email=email)

        _set_session(user)
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(next_url or url_for("index"))

    return render_template("auth_login.html", next=next_url)


# ── Logout ──────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    name = session.get("user_name", "")
    session.clear()
    flash(f"You have been logged out{', ' + name if name else ''}.", "success")
    return redirect(url_for("auth.login"))


# ── Profile ──────────────────────────────────────────────────────────────────
@auth_bp.route("/profile")
@login_required
def profile():
    user = get_current_user()
    return render_template("auth_profile.html", user=user)


# ── Helper ──────────────────────────────────────────────────────────────────
def _set_session(user):
    session["user_id"]   = str(user.get("_id") or user.get("id"))
    session["user_name"] = user["name"]
    session["user_role"] = user.get("role", "student")
    session["user_email"]= user["email"]
