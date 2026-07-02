from flask import Flask, render_template, request, redirect, url_for, flash
import random

from models import db, User, Story

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)


# ---------------- APP SETUP ----------------

app = Flask(__name__)

app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)


# ---------------- LOGIN MANAGER SETUP ----------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- HOME ROUTE ----------------

@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------- REGISTER ROUTE ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            flash(
                "An account with this email already exists. Please login.",
                "error"
            )

            return redirect(url_for("login"))

        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            flash(
                "This username is already taken. Please choose another one.",
                "error"
            )

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Account created successfully! Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ROUTE ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash(
                f"Welcome back, {user.username}!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# ---------------- LOGOUT ROUTE ----------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "info"
    )

    return redirect(url_for("login"))


# ---------------- DASHBOARD ROUTE ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    stories = Story.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "dashboard.html",
        user=current_user,
        stories=stories
    )


# ---------------- CREATE STORY ROUTE ----------------

@app.route("/create-story", methods=["GET", "POST"])
@login_required
def create_story():

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        new_story = Story(
            title=title,
            content=content,
            user_id=current_user.id
        )

        db.session.add(new_story)
        db.session.commit()

        flash(
            "Story created successfully!",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template("create_story.html")


# ---------------- STORY DETAIL ROUTE ----------------

@app.route("/story/<int:story_id>")
@login_required
def story_detail(story_id):

    story = Story.query.get_or_404(story_id)

    if story.user_id != current_user.id:

        flash(
            "You do not have permission to view that story.",
            "error"
        )

        return redirect(url_for("dashboard"))

    return render_template(
        "story_detail.html",
        story=story
    )


# ---------------- EDIT STORY ROUTE ----------------

@app.route("/edit-story/<int:story_id>", methods=["GET", "POST"])
@login_required
def edit_story(story_id):

    story = Story.query.get_or_404(story_id)

    if story.user_id != current_user.id:

        flash(
            "You do not have permission to edit that story.",
            "error"
        )

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        story.title = request.form["title"]
        story.content = request.form["content"]

        db.session.commit()

        flash(
            "Story updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "story_detail",
                story_id=story.id
            )
        )

    return render_template(
        "edit_story.html",
        story=story
    )


# ---------------- DELETE STORY ROUTE ----------------

@app.route("/delete-story/<int:story_id>")
@login_required
def delete_story(story_id):

    story = Story.query.get_or_404(story_id)

    if story.user_id != current_user.id:

        flash(
            "You do not have permission to delete that story.",
            "error"
        )

        return redirect(url_for("dashboard"))

    db.session.delete(story)
    db.session.commit()

    flash(
        "Story deleted successfully!",
        "success"
    )

    return redirect(url_for("dashboard"))


# ---------------- PROFILE ROUTE ----------------

@app.route("/profile")
@login_required
def profile():

    story_count = Story.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(
        "profile.html",
        user=current_user,
        story_count=story_count
    )


# ---------------- EDIT PROFILE ROUTE ----------------

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        current_user.bio = request.form["bio"]

        db.session.commit()

        flash(
            "Profile updated successfully!",
            "success"
        )

        return redirect(url_for("profile"))

    return render_template("edit_profile.html")


# ---------------- STORY GENERATOR ROUTE ----------------

@app.route("/generate-story", methods=["GET", "POST"])
@login_required
def generate_story():

    generated_title = None
    generated_genre = None
    generated_story = None

    if request.method == "POST":

        prompt = request.form["prompt"]
        genre = request.form["genre"]

        title_templates = [
            f"The Secret of {prompt}",
            f"The Last Legend of {prompt}",
            f"When {prompt} Changed Everything",
            f"The Mystery Behind {prompt}",
            f"A Journey Through {prompt}"
        ]

        opening_lines = [
            f"No one believed the stories about {prompt}, until everything changed.",
            f"In a world shaped by secrets, {prompt} became the beginning of something impossible.",
            f"The first sign appeared quietly, but soon everyone would know about {prompt}.",
            f"For years, {prompt} was only a rumour. Then it became real.",
            f"Every great adventure begins with a question — this one began with {prompt}."
        ]

        conflict_lines = [
            "A hidden danger began to rise from the shadows.",
            "The character was forced to make a choice that changed everything.",
            "Old enemies returned with forgotten secrets.",
            "A powerful truth was uncovered.",
            "The world became more dangerous with every step."
        ]

        ending_hooks = [
            "But this was only the beginning.",
            "And somewhere far away, someone was watching.",
            "The final answer was still hidden.",
            "The journey ahead would test everything.",
            "A new mystery had just begun."
        ]

        generated_title = random.choice(title_templates)
        generated_genre = genre

        generated_story = (
            random.choice(opening_lines)
            + "\n\n"
            + f"This {genre.lower()} story follows a character discovering the truth behind {prompt}. "
            + random.choice(conflict_lines)
            + "\n\n"
            + random.choice(ending_hooks)
        )

    return render_template(
        "generate_story.html",
        generated_title=generated_title,
        generated_genre=generated_genre,
        generated_story=generated_story
    )


# ---------------- SAVE GENERATED STORY ROUTE ----------------

@app.route("/save-generated-story", methods=["POST"])
@login_required
def save_generated_story():

    title = request.form["title"]
    content = request.form["content"]

    new_story = Story(
        title=title,
        content=content,
        user_id=current_user.id
    )

    db.session.add(new_story)
    db.session.commit()

    flash(
        "Generated story saved successfully!",
        "success"
    )

    return redirect(url_for("dashboard"))


# ---------------- CREATE DATABASE TABLES ----------------

with app.app_context():
    db.create_all()


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)