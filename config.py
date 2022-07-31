from flask_sqlalchemy import SQLAlchemy
from flask import Flask


# part with flask configuration starts here
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = "c24cc731487b6356c9f87c1c336feb58cede7f8aaaed75bbef315e346313ef4f"
app.config["SECURITY_PASSWORD_SALT"] = "cb22cd61603dee9e60e8d3d752f77e4580e7d1932036eda9609896c03308fc92"
db = SQLAlchemy(app)

# mail settings
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

# gmail authentication
app.config["MAIL_USERNAME"] = "simple.bugtracker2@gmail.com"
app.config["MAIL_PASSWORD"] = "jvddqgdghnyhsxgk"

# mail accounts
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

# customisation options

# set mail_ver to False if you don't want the users to confirm their rejestrations with email.
# set it to False when you use testing module
mail_ver = True
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