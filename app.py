from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Story
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "super-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

    return render_template("login.html")

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

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("home")
    )
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

        return redirect(url_for("dashboard"))

    return render_template("create_story.html")

@app.route("/story/<int:story_id>")
@login_required
def story_detail(story_id):

    story = Story.query.get_or_404(story_id)

    return render_template(
        "story_detail.html",
        story=story
    )
    
@app.route(
    "/edit-story/<int:story_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_story(story_id):

    story = Story.query.get_or_404(story_id)

    if request.method == "POST":

        story.title = request.form["title"]
        story.content = request.form["content"]

        db.session.commit()

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
    
@app.route(
    "/delete-story/<int:story_id>"
)
@login_required
def delete_story(story_id):

    story = Story.query.get_or_404(story_id)

    db.session.delete(story)

    db.session.commit()

    return redirect(
        url_for("dashboard")
    )
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)