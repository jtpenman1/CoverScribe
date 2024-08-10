import datetime
import os
import cs50 
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import openai
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///personal.db")

@app.route("/")
@login_required
def index():
    """Show portfolio of user"""
    id = session.get("user_id")
    info = db.execute("SELECT * FROM information WHERE user_id = ?", id)
    intro = info[0]["intro"]
    skills = info[0]["skills"]
    projects = info[0]["projects"]

    return render_template("index.html", intro=intro, skills=skills, projects=projects)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        if not username:
            return apology("must provide username", 400)
        elif not first_name:
            return apology("must provide first name", 400)
        
        elif not last_name:
            return apology("must provide last name", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        elif not confirmation:
            return apology("must provide confirmation", 400)

        elif password != confirmation:
            return apology("confirmation must match ", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        # Ensure username doesn't exist
        if len(rows) != 0:
            return apology("username is already taken", 400)

        db.execute("INSERT INTO users (username, hash, firstname, lastname) VALUES(?, ?, ?, ?)",
                    username, generate_password_hash(password), first_name, last_name)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to the edit info page to add information
        return redirect("/edit_info")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/edit_info", methods=["GET", "POST"])
@login_required
def edit_info():
    """edit user information"""
    id = session.get("user_id")
    if request.method == "POST":
        intro = request.form.get("intro")
        skills = request.form.get("skills")
        projects = request.form.get("projects")
        info = db.execute("SELECT * FROM information WHERE user_id = ?", id)
        if len(info) == 0:
            db.execute("INSERT INTO information (intro, skills, projects, user_id) VALUES(?, ?, ?, ?)",
                    intro, skills, projects, id)
        else: 
            db.execute("UPDATE information SET intro = ?, skills = ?, projects = ? WHERE user_id = ?", intro, skills, projects, id)
        return render_template("index.html", intro=intro, skills=skills, projects=projects)
    else:
        info = db.execute("SELECT * FROM information WHERE user_id = ?", id)
        if len(info) == 0:
            return render_template("edit_info.html")
        intro = info[0]["intro"]
        skills = info[0]["skills"]
        projects = info[0]["projects"]
        return render_template("edit_info.html", intro=intro, skills=skills, projects=projects)

@app.route("/create_cover", methods=["GET", "POST"])
@login_required
def create_cover():
    """get job information"""
    id = session.get("user_id")
    if request.method == "POST":
        name = db.execute("SELECT * FROM users WHERE id = ?", id)
        first_name = name[0]["firstname"]
        last_name = name[0]["lastname"]

        info = db.execute("SELECT * FROM information WHERE user_id = ?", id)
        intro = info[0]["intro"]
        skills = info[0]["skills"]
        projects = info[0]["projects"]

        company = request.form.get("company")
        title = request.form.get("title")
        date = datetime.datetime.now().strftime("%B %d %Y")

        job = request.form.get("job")
        qualifications = request.form.get("qualifications")
        other = request.form.get("other")
        info = db.execute("SELECT * FROM information WHERE user_id = ?", id)

        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Remember this information about me to help me write a cover letter. First Name:" + first_name + "last name:" + last_name + "intro: " + intro + " skills: " + skills + " projects: " + projects},
            {"role": "system", "content": "remember this information about the job to help me write a cover letter. job: " + job + " qualifications: " + qualifications + " other: " + other},
            {"role": "user", "content": "Write a one page cover letter only using relevant information about me and the job. Do not use any fill in the blank templates. Start with Dear Hiring Manager or company name"},
        ]
        )
        coverletter = completion.choices[0].message.content

        db.execute("INSERT INTO letters (user_id, letter, date, company_name, job_title) VALUES(?, ?, ?, ?, ?)",
                    id, coverletter, date, company, title)
        
        db.execute("UPDATE users SET letter_count = letter_count + 1 WHERE id = ?", id)

        return render_template("letter_view.html", coverletter=coverletter)
    else:
        return render_template("create_cover.html")

@app.route("/letter_editor", methods=["GET", "POST"])
@login_required
def letter_editor():
    """get job information"""
    user_id = session.get("user_id")
    if request.method == "POST":
        info = db.execute("SELECT * FROM users WHERE user_id = ?", user_id)
        id = info[0]["id"]
        coverletter = request.form.get("coverletter")
        db.execute("UPDATE letters SET letter = ? WHERE user_id = ? AND id = ?", coverletter, user_id, id)
        return render_template("letter_view.html", coverletter=coverletter)
    else:
        return render_template("letter_editor.html")
    
@app.route("/letter_view", methods=["GET", "POST"])
@login_required
def letter_view():
    """view cover letter"""
    id = session.get("user_id")
    if request.method == "POST":
        if request.form.get("edit"):
            return render_template("letter_editor.html")
        if request.form.get("done"):
            return render_template("history.html")
    else:
        return render_template("letter_view.html")
    
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """view cover letter"""
    id = session.get("user_id")
    if request.method == "POST":
        letter_id = request.form.get("letter_id")
        info = db.execute("SELECT * FROM letters WHERE user_id = ? AND id = ?", id, letter_id)
        return render_template("letter_view.html", coverletter=info[0]["letter"])
    else:
        info = db.execute("SELECT * FROM letters WHERE user_id = ?", id)            
        return render_template("history.html", info=info)