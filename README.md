1. Simple Bugtracker
This project is a simple and easly deployable bug tracker with basic functionalities in polish language. You can use it in any project you want.
It uses flask and associated libraries like flask_login and flask_mail. It doesen't contain any JS nor php, just python and html files.
It provides simple registration with email confirmation, features of adding multiple projects, bugs to the projects and attachments to
the bugs. It allows to search for bugs and projects by different parameters and sort the results.

2. User guide
You can fork this repository and upload it to a hosting server.
For a preview you can visit this Heroku link: https://simple-bugtracker-mp.herokuapp.com
You can also use wheel to make a deployed version of this app, check "https://flask.palletsprojects.com/en/2.1.x/tutorial/deploy/" for more info.
Before deployment remember to set enviormental variables such as SECRET_KEY, SECURITY_PASSWORD_SALT, MAIL_SERVER, MAIL_USERNAME and MAIL_PASSWORD
in config.py file. You can also set a few additional options in this file such as disabling email veryfication.

3. Credits:
Mateusz Pawłowski