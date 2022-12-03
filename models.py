from datetime import datetime, timezone
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from dateutil import tz
from flask_mail import Message, Mail

from config import app, db, allowed_extensions


# part with mail veryfication functions
mail = Mail(app)
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt = app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt = app.config['SECURITY_PASSWORD_SALT'],
            max_age = expiration
        )
    except:
        return False
    return email

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)
   
# this function checks if attachments have proper extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# this function transforms utc time into local timezone time and is used for saving 
# Action times for history of changes
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz.tzlocal())

# This function help with sorting and searching by bug importance
def importance_to_num(str):
   if str == "propozycja":
      return 0
   if str == "błachy":
      return 1
   if str == "poprawka":
      return 2
   if str == "drobny":
      return 3
   if str == "ważny":
      return 4
   if str == "krytyczny":
      return 5
   if str == "blokujący":
      return 6

# part with n to m relationship tables starts here
user_project = db.Table("user_project",
db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
db.Column("project_id", db.Integer, db.ForeignKey("project.id")))

bug_tag = db.Table("bug_tag",
db.Column("bug_id", db.Integer, db.ForeignKey("bug.id")),
db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")))

# part with sql tables starts here
class User(db.Model, UserMixin):
   id = db.Column("id", db.Integer, primary_key = True)
   login = db.Column(db.String(200), nullable=False, unique = True)
   password = db.Column(db.String(200), nullable=False)
   email = db.Column(db.String(200), nullable=False)
   confirmed = db.Column(db.Boolean, default = False)
   project_id = db.relationship("Project", secondary = user_project, backref = "isworked")
   bugs = db.relationship("Bug", backref = "user")
   new_email = db.Column(db.String(200))

   def __init__(self, login, password, email):
      self.login = login
      self.password = password
      self.email = email
   
   def __repr__(self):
      return f"{self.login}"

class Project(db.Model):
   id = db.Column("id", db.Integer, primary_key = True)
   id_ = db.Column("id_", db.Integer)
   name = db.Column(db.String(200))
   description = db.Column(db.String(1000))
   submiter_id = db.Column(db.Integer)
   user_id = db.relationship("User",secondary = user_project, backref = "belongs")
   bug_id = db.relationship("Bug", backref = "project")

   def __init__(self, name, description, submiter_id):
      self.name = name
      self.description = description
      self.submiter_id = submiter_id
   
   def __repr__(self):
      return f"{self.name}"

class Bug(db.Model):
   id = db.Column("id", db.Integer, primary_key = True)
   id_ = db.Column("id_", db.Integer)
   topic = db.Column(db.String(200), nullable=False)
   importance = db.Column(db.String(200), nullable=False)
   description = db.Column(db.String(1000))
   status = db.Column(db.String(200), default = "nierozwiązany")
   project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
   user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
   actions = db.relationship("Action", backref = "bug")
   attachment = db.relationship("Attachment", backref = "bug")
   tag_id = db.relationship("Tag",secondary = bug_tag, backref = "describes")

   def __init__(self, topic, importance, description, project_id, user_id):
      self.topic = topic
      self.importance = importance
      self.description = description
      self.project_id = project_id
      self.user_id = user_id
   
   def __repr__(self):
      return f"{self.topic}"

# action table is used for history of changes
class Action(db.Model):
   id = db.Column("id", db.Integer, primary_key = True)
   kind = db.Column(db.String(20), nullable=False)
   time_utc = db.Column(db.DateTime, default=datetime.utcnow())
   time = db.Column(db.String(70), default = utc_to_local(datetime.utcnow()).strftime('%d.%m.%Y - %H:%M:%S'))
   bug_id = db.Column(db.Integer, db.ForeignKey("bug.id"))

   def __init__(self, kind, bug_id):
      self.kind = kind
      self.bug_id = bug_id

class Attachment(db.Model):
   id = db.Column("id", db.Integer, primary_key = True)
   filename = db.Column(db.String(50))
   bug_id = db.Column(db.Integer, db.ForeignKey("bug.id"))
   attachment = db.Column(db.LargeBinary)

   def __init__(self, filename, attachment, bug_id):
      self.filename = filename
      self.attachment = attachment
      self.bug_id = bug_id
   
   def __repr__(self):
      return f"{self.filename}"

class Tag(db.Model):
   id = db.Column("id", db.Integer, primary_key = True)
   name = db.Column(db.String(200), nullable=False, unique = True)
   bug_id = db.relationship("Bug",secondary = bug_tag, backref = "isdescribed")

   def __init__(self, name):
      self.name = name
   
   def __repr__(self):
      return f"{self.name}"