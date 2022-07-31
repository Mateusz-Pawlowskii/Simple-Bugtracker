from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
   login = StringField('Login', validators=[DataRequired()])
   password = PasswordField('Password', validators=[DataRequired()])

class SignForm(FlaskForm):
   login = StringField('Login', validators=[DataRequired()])
   password = PasswordField('Password', validators=[DataRequired()])
   email = StringField('Email', validators=[DataRequired(), Email()])

class ProjectForm(FlaskForm):
   name = StringField('Name', validators=[DataRequired()])
   description = TextAreaField('Description')

class BugForm(FlaskForm):
   topic = StringField('Topic', validators=[DataRequired()])
   importance = StringField('Importance', validators=[DataRequired()])
   description = StringField('Description', validators=[DataRequired()])
   project_id = IntegerField('Project_id', validators=[DataRequired()])
   attachment = FileField("Attachment")
   tag_id = StringField("Tag_id")
   status = StringField("Status")

class UserProjectForm(FlaskForm):
   user_login = StringField('User_login', validators=[DataRequired()])
   project_id = IntegerField('Project_id', validators=[DataRequired()])

class SearchForm(FlaskForm):
   searched = StringField('Searched', validators=[DataRequired()])
   sor_by = StringField('Sor_by')
   order = StringField('Order')

class SortForm(FlaskForm):
   sor_by = StringField('Sor_by')
   order = StringField('Order')

class ChangeForm(FlaskForm):
   new_data = StringField('New_data', validators=[DataRequired()])
   new_data_repeat = StringField('New_data_repeat', validators=[DataRequired()])
   password = PasswordField('Password', validators=[DataRequired()])