from flask_mongoengine import MongoEngine
from flask import Flask
import os


# part with flask configuration starts here
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "")
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get("SECURITY_PASSWORD_SALT", "")
db = MongoEngine()
db.init_app(app)

# mail settings
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "")
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

# gmail authentication
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")

# mail accounts
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

# customisation options

# set mail_ver to False if you don't want the users to confirm their rejestrations with email.
# set it to False when you use testing module
mail_ver = False
# In order to improve screen redability when there are a lot of projects assigned to users they are hidden from mainpage bug view
# set projects_hide to False if you don't want projects to be hidden
projects_hide = True
# this variable controls the maximum amount of projects that can show up on homepage bug view before they are going to be hidden.
# does nothing if projects_hid is set to 0
max_projects = 16
# set this to True if you want to limit extensions allowed for attachements
limit_extensions = False
# this variable controls which file extensions are allowed for attachments
allowed_extensions = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}