#------------------------------------------------------
# Define all entry points (Web pages & API endpoints)
#------------------------------------------------------
import os
from flask import jsonify, json, abort, request, render_template, redirect, current_app, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from git import Repo
from flask_bcrypt import Bcrypt 
from . import helpers, create_app, db, swagger
from datetime import datetime
from operator import attrgetter

from .models import Tag, Subject, Reminder, User


app = create_app(os.getenv('FLASK_CONFIG') or 'default')

"""
To-do list :
    - Bcrypt scurity
    - * Relationship between user and reminder --- Done in models.py, need to apply to routes.py
    - * Create add reminder functionnality 
    - * Change approach for frontend to get reminders (need to use fetch)
    - Send email verification 
    - Ask for username and email rather than just email

* Priority/important
"""

#------------------------------------------------------
# HOME SITE
@app.route("/")
@app.route("/index")
@app.route("/home")
def home():
    return render_template("home.html")

#------------------------------------------------------
# WEB
@app.route('/agenda')
@login_required
def agenda():
    reminders = Reminder.query.all()
    return render_template('agenda.html', title="Agenda Personnel", user="test", reminders=reminders)

@app.route('/add_reminder')
@login_required
def add_reminder():
    return render_template("add_reminder.html")
#------------------------------------------------------
# API ~~ CRUD functions
@app.route("/api/reminder/<int:rem_id>")
@login_required
def get_reminder(rem_id): # Read
    """Endpoint to read a reminder
    ---
    description: Endpoint returning reminder with a specified id (must be logged in)
    parameters:
      - name: rem_id
        in: path
        type: integer
        required: true
        default: all
    definitions:
      Reminder:
        type: object
        properties:
          id:
            type: integer
            example: 1478
          user_id: 
            type: integer
            example: 3927
          tag_id: 
            type: integer
            example: 8370
          subject_id: 
            type: integer
            example: 9239
          date: 
            type: string
            example: 2026-12-31T00:00:00
          content: 
            type: string
            example: Create an account on quantix.pythonanywhere.com
    responses:
      200:
        description: A reminder object
        schema:
          $ref: '#/definitions/Reminder'
        examples:
          application/json: {
            "content": "An example content of a reminder",
            "date": "2027-02-24T00:00:00",
            "id": 54,
            "subject_id": 36,
            "tag_id": 29,
            "user_id": 167
          }
      403:
        description: The reminder with the specified id belongs to someone else
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          application/json: {"message": "Not logged into the account of the reminder"}
      404:
        description: The reminder with the specified id was not found
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          application/json: {"message": "Reminder not found"}
      500:
        description: An error ocurred internally. This isn't planned and can have many causes
    """
    reminders = Reminder.query.filter_by(reminder_id=rem_id).first()
    if reminders is not None:
        if reminders.user_id == current_user.id:
            return jsonify(reminders.to_json()), 200
        else:
            return jsonify({"message": "Not logged into the account of the reminder"}), 403
    else:
        return jsonify({"message": "Reminder not found"}), 404
    
@app.route("/api/reminder")
@login_required
def get_reminders(): # Read
    """Endpoint to read reminders
    ---
    description: Endpoint returning all reminders linked to your account (must be logged in)
    responses:
      200:
        description: A list of all reminders sorted chronologically by date property
        schema:
        type: array
        items:
          $ref: '#/definitions/Reminder'
        examples:
          application/json: [{
            "content": "An example content of a reminder",
            "date": "2027-02-24T00:00:00",
            "id": 54,
            "subject_id": 36,
            "tag_id": 29,
            "user_id": 167
          },
          {
            "content": "An other example content of a reminder",
            "date": "2028-02-24T00:00:00",
            "id": 55,
            "subject_id": 78,
            "tag_id": 5,
            "user_id": 167
          }]
      500:
        description: An error ocurred internally. This isn't planned and can have many causes
    """
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()
    sorted_rems = sorted(reminders, key=attrgetter('date'))
    return jsonify([r.to_json() for r in sorted_rems]), 200
    
@app.route("/api/reminder", methods=["POST"])
@login_required
def create_reminders(): # Create
    """Endpoint to create reminders
    ---
    description: Endpoint to create new reminders linked to your account (must be logged in)
    parameters:
      - name: body
        in: body
        required: True
        schema:
          type: object
          properties:
            content:
              type: string
              example: Have a good day :)
            date:
              type: string
              example: 2027-01-01T00:00:00
            subject_id:
              type: integer
              example: 8888
            tag_id:
              type: integer
              example: 1234
    responses:
      200:
        description: A validation message along with the id of the newly created reminder
        schema:
          type: object
          properties:
            message:
              type: string
              example: Reminder created succesfully
            rem_id:
              type: integer
              example: 12345
        examples:
          application/json: {"message": "Reminder was created succesfully", "rem_id": 54321}
      404:
        description: Meaning one of the params of the request was not found in the database 
        schema:
          type: object
          properties:
            message:
              type: string
              example: Tag requested not found
        examples:
          application/json: {"message": "Subject requested not found"}
      403:
        description: Meaning one of the params of the request was found but doesnt belong to your account
        schema:
          type: object
          properties:
            message:
              type: string
              example: Tag requested not linked to your account
        examples:
          application/json: {"message": "Subject requested not linked to your account"}
      500:
        description: An error ocurred internally. This isn't planned and can have many causes
    """
    data = json.loads(request.data)
    tag_id=data.get("tag_id")
    subject_id=data.get("subject_id")
    tag=Tag.query.get(tag_id)
    subject=Subject.query.get(subject_id)
    if tag:
        if subject:
            if tag.user_id == current_user.id:
                if subject.user_id == current_user.id:
                    reminder = Reminder(
                        content=data.get("content"), 
                        date=datetime.strptime(data.get("date"), "%Y-%m-%d"),
                        user=current_user,
                        user_id=current_user.id,
                        tag_id=tag_id,
                        subject_id=subject_id
                    )
                    db.session.add(reminder)
                    db.session.commit()
                    return jsonify({"message": "Reminder created succesfully", "rem_id": reminder.reminder_id}), 200
                return jsonify({"message": "Subject requested not linked to your account"}), 403
            return jsonify({"message": "Tag requested not linked to your account"}), 403
        return jsonify({"message": "Subject requested not found"}), 404
    return jsonify({"message": "Tag requested not found"}), 404
        

@app.route("/api/reminder/<int:rem_id>", methods=["DELETE"])
@login_required
def delete_reminders(rem_id): # Delete
    """Endpoint to delete a reminder
    ---
    description: Endpoint to delete a reminder with a specified id (must be logged in)
    parameters:
      - name: rem_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: A reminder object
        schema:
          $ref: '#/definitions/Reminder'
        examples:
          application/json: {
            "content": "An example content of a reminder",
            "date": "2027-02-24T00:00:00",
            "id": 54,
            "subject_id": 36,
            "tag_id": 29,
            "user_id": 167
          }
      403:
        description: The reminder with the specified id belongs to someone else
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          application/json: {"message": "Not logged into the account of the reminder"}
      404:
        description: The reminder with the specified id was not found
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          application/json: {"message": "Reminder not found"}
      500:
        description: An error ocurred internally. This isn't planned and can have many causes
    """
    reminder = Reminder.query.filter_by(reminder_id=rem_id).first()
    if reminder:
        if reminder.user_id == current_user.id: # Layer of security
            db.session.delete(reminder)
            db.session.commit()
            return jsonify({"message":"Reminder deleted succesfully"}), 200
        else:
            return jsonify({"message": "Not logged in the right account"}), 403
    else:
        return jsonify({"message": "Reminder not found"}), 404

@app.route("/api/reminder/<int:rem_id>", methods=["PUT"])
@login_required
def update_reminders(rem_id): # Update ~~ Not complete
    data = json.loads(request.data)
    reminder = Reminder(
        content=data.get("content"), 
        date=datetime.strptime(data.get("date"), "%Y-%m-%d"),
        user=current_user,
        user_id=current_user.id,
        tag_id=data.get("tag_id"),
        subject_id=data.get("subject_id")
    )
    db_reminder = Reminder.query.get(rem_id)
    if db_reminder.user_id == current_user.id:
        db_reminder.update(reminder)
        db.session.commit()
        return jsonify({"message": "Reminder updated succesfully"}), 200
    return jsonify({"message": "Not loggedi in the account of the reminder"}), 403


@app.route("/api/subject", methods=["GET", "POST"])
@login_required
def subjects():
    if request.method == "GET":
        subjects = Subject.query.filter_by(user_id=current_user.id).all()
        return jsonify([s.to_json() for s in subjects])
    data = json.loads(request.data)
    if Subject.query.filter_by(content=data.get("content"), user_id=current_user.id).first() is None:
        subject = Subject(
            content=data.get("content"), 
            bg_color=data.get("bg_color"),
            user=current_user,
            user_id=current_user.id
        )
        db.session.add(subject)
        db.session.commit()
        return jsonify(subject.to_json()), 200
    else:
        return jsonify({"message": "Une matière avec le même nom existe déjà"}), 400
        
@app.route("/api/tag", methods=["GET", "POST"]) 
@login_required
def tags():
    if request.method == "GET":
        tags = Tag.query.filter_by(user_id=current_user.id).all()
        return jsonify([t.to_json() for t in tags])
    data = json.loads(request.data)
    if Tag.query.filter_by(content=data.get("content"), user_id=current_user.id).first() is None:
        tag = Tag(
            content=data.get("content"), 
            bg_color=data.get("bg_color"),
            user=current_user,
            user_id=current_user.id
        )
        db.session.add(tag)
        db.session.commit()
        return jsonify(tag.to_json()), 200
    else:
        return jsonify({"message": "Un tag avec le même nom existe déjà"}), 400
    
@app.route("/api/reminder/delete/<int:reminderId>", methods=["POST"])
@login_required
def delete_reminder(reminderId):
    reminder = Reminder.query.filter_by(reminder_id=reminderId).first()
    if reminder:
        if reminder.user_id == current_user.id: # Layer of security
            db.session.delete(reminder)
            db.session.commit()
            return jsonify({"message":"Reminder deleted succesfully"}), 200
        else:
            return jsonify({"message": "Not logged in the right account"}), 403
    else:
        return jsonify({"message": "Reminder not found"}), 404
        
#------------------------------------------------------
# Auto deploy
@app.route('/api/push_version', methods=['POST'])
def git_webhook():
    x_hub_signature = request.headers.get('X-Hub-Signature')
    helpers.verify_signature(request.data, current_app.config['GIT_REPO_SECRET'],x_hub_signature)
    repo = Repo(current_app.config['GIT_REPO_PATH'])
    origin = repo.remotes.origin
    origin.pull(current_app.config['GIT_REPO_BRANCH'])
    return 'Updated PythonAnywhere successfully', 200

#------------------------------------------------------
# User Verification
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)
    
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = json.loads(request.data)
        email = data.get('email')
        if User.query.filter_by(username=email).first() is None:
            if data.get("password1") == data.get("password2"):
                user = User(username=email,
                            password=bcrypt.generate_password_hash(data.get("password1")).decode('utf-8'))
                db.session.add(user)
                db.session.commit()
                return jsonify({"message": "Account created successfully"}), 200 # Error here ~Probably~
            else:
                return jsonify({"message": "Les mots de passe ne correspondent pas."}), 400
        else:
            response = {
                "message": "Un compte existe déjà avec cette adresse email. ",
                "link_href": "/login",
                "link_display":"Se connecter"
            }
            return jsonify(response), 400
    return render_template("register.html")
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = json.loads(request.data)
        email = data.get('email')
        try:
            user = User.query.filter_by(
                username=email).first()
            if bcrypt.check_password_hash(user.password, data.get('password')):
                login_user(user)
                return jsonify({"message": "Logged in successfully"}), 200
            raise AttributeError
        except AttributeError:
            response = {"message": "L'adresse email ou le mot de passe est incorrect."}
            return jsonify(response), 400
    return render_template("login.html")
 
 
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))
