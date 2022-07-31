from io import BytesIO
from flask import render_template, redirect, request, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from functools import wraps

from models import Bug, User, Project, Action, Attachment, Tag, allowed_file, generate_confirmation_token, confirm_token, send_email, importance_to_num
from forms import ChangeForm, LoginForm, SignForm, ProjectForm, BugForm, UserProjectForm, SearchForm, SortForm
from config import mail_ver, projects_hide, max_projects, limit_extensions, app, db


def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.confirmed is False:
            return redirect(url_for("unconfirmed"))
        return func(*args, **kwargs)
    return decorated_function

# part with the general homepage views starts here
@app.route("/", methods = ["GET","POST"])
def homepage():
    if current_user.is_authenticated:
        form = SortForm()
        projects = User.query.get(int(session["user_id"])).project_id
        bugs = projects[1:1]
        # If you don't want to allow big amounts of projects to show(that would make screen messy)
        # you can set this variable in customisation
        if projects_hide is True and len(projects)>max_projects:
            no_display = True
        else:
            no_display = False
        for project in projects:
            bugs += project.bug_id
        if request.method == "POST":
            if request.form.get("sor_by") == "id":
                bugs = sorted(bugs, key = lambda x:x.id)
            elif request.form.get("sor_by") == "topic":
                bugs = sorted(bugs, key = lambda x:x.topic)
            elif request.form.get("sor_by") == "importance":
                bugs = sorted(bugs, key = lambda x:importance_to_num(x.importance))
            elif request.form.get("sor_by") == "project":
                bugs = sorted(bugs, key = lambda x:x.project_id)
            elif request.form.get("sor_by") == "status":
                bugs = sorted(bugs, key = lambda x:x.status)
            elif request.form.get("sor_by") == "len_att":
                bugs = sorted(bugs, key = lambda x:len(x.attachment))
            if request.form.get("order") == "decreasing":
                bugs = bugs[::-1]
        return render_template("general/homepage.html", nav = "homepage", projects = projects, bugs = bugs,
                                no_display = no_display, form = form)
    # I haven't used @login_required becouse the user on the homepage might not have an account yet
    return redirect(url_for("welcome"))

#route for viewing bugs belonging to a specyfic project
@app.route("/homepage/project/<int:id>", methods = ["GET","POST"])
@login_required
@check_confirmed
def homepage_specyfic(id):
    form = SortForm()
    active = Project.query.get(id)
    projects = User.query.get(int(session["user_id"])).project_id
    bugs = active.bug_id
    if len(projects)>16:
        no_display = 1
    else:
        no_display = 0
    if request.method == "POST":
        if request.form.get("sor_by") == "id":
            bugs = sorted(bugs, key = lambda x:x.id)
        elif request.form.get("sor_by") == "topic":
            bugs = sorted(bugs, key = lambda x:x.topic)
        elif request.form.get("sor_by") == "project":
            bugs = sorted(bugs, key = lambda x:x.project_id)
        elif request.form.get("sor_by") == "status":
            bugs = sorted(bugs, key = lambda x:x.status)
        elif request.form.get("sor_by") == "len_att":
            bugs = sorted(bugs, key = lambda x:len(x.attachment))
        if request.form.get("order") == "1":
            bugs = bugs[::-1]
    return render_template("general/homepage.html", nav = "homepage", projects = projects, bugs = bugs, 
                            active = active, no_display = no_display, form = form)

@app.route("/projects/", methods = ["GET","POST"])
@login_required
@check_confirmed
def homepage_projects():
    form = SortForm()
    projects = User.query.get(int(session["user_id"])).project_id
    if request.method == "POST":
        if form.validate_on_submit:
            if request.form.get("sor_by") == "id":
                projects = sorted(projects, key = lambda x:x.id)
            elif request.form.get("sor_by") == "name":
                projects = sorted(projects, key = lambda x:x.name)
            elif request.form.get("sor_by") == "len_bugs":
                projects = sorted(projects, key = lambda x:len(x.bug_id))
            if request.form.get("order") == "1":
                projects = projects[::-1]
    return render_template("general/homepage_projects.html", nav = "homepage", projects = projects, form = form)

# view for history of all changes that happened to the bugs that were submitted to projects
# which the user is allwed to sumbit to
@app.route("/history/")
@login_required
@check_confirmed
def homepage_history():
    projects = User.query.get(int(session["user_id"])).project_id
    bugs = projects[1:1]
    actions = projects[1:1]
    for project in projects:
        bugs += project.bug_id
    for bug in bugs:
        actions += bug.actions
    return render_template("general/homepage_history.html", 
            nav="homepage", projects = projects, bugs = bugs, actions=sorted(actions,key = lambda x:x.id)[::-1])

# part with registraion and logging in starts here
@app.route("/login/", methods=["GET", "POST"])
def login():
   form = LoginForm()
   errors = None
   if request.method == "POST":
    if form.validate_on_submit:
        user = User.query.filter_by(login = request.form.get("login")).first()
        if user:
            if check_password_hash(user.password, request.form["password"]):
                login_user(user)
                session["user_id"] = User.query.filter(User.login == request.form["login"]).first().id
                return redirect(url_for("homepage"))
            else:
                flash("Złe hasło - spróbuj ponownie")
        else:
            flash("Zły login - spróbuj ponownie")
   return render_template("logging/login_form.html", form=form, errors=errors)

@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
   if request.method == "POST":
       logout_user()
       session.clear()
       flash("Zostałeś wylogowany")
   return redirect(url_for("login"))

@app.route("/sign/", methods=["GET", "POST"])
def sign():
    form = SignForm()
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                user=User(login = request.form.get("login"),
                        password = generate_password_hash(request.form.get("password")),
                        email = request.form.get("email"))
                # mail_ver is customisation option (found in config) that desides if the users have to recieve confirmation emails
                if mail_ver is False:
                    user.confirmed = True
                db.session.add(user)
                db.session.commit()
                if mail_ver is True:
                    token = generate_confirmation_token(user.email)
                    confirm_url = url_for("confirm_email", token=token, _external=True)
                    html = render_template("logging/sign_confirm.html", confirm_url=confirm_url)
                    subject = "Prosze o potwierdzenie adresu email"
                    send_email(user.email, subject, html)
                    login_user(user)
                    session["user_id"] = User.query.filter(User.login == request.form["login"]).first().id
                    session.permanent = True
                    flash("Udało się pomyślnie utworzyć nowe konto, sprawdź skrzynkę mailową by potwierdzić rejestrację")
                    return redirect(url_for("unconfirmed"))
                return redirect(url_for("login"))
            except:
                flash("Podany login jest już zajęty, prosze wybrać inny")
        flash("Niepoprawny adres E-mail")
    return render_template("logging/sign_form.html", form = form)

# view that asks user if they want to login or sign
@app.route("/welcome/")
def welcome():
        return render_template("welcome.html")

# view that informs about me and presents my email and phone number
@app.route("/about/")
def about():
        return render_template("about.html", nav = "about")

# part with email veryfication starts here
@app.route("/confirm/<token>")
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash("Link potwierdzający wygasł lub jest niepoprawny")
    user = User.query.filter_by(email = email).first()
    if user.confirmed:
        flash("Konto zostało już potwierdzone, można się zalogować")
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash("Konto zostało pomyślnie potwierdzone")
    return redirect(url_for("homepage"))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('homepage'))
    flash("Prosimy o potwierdzenie konta")
    return render_template('logging/unconfirmed.html')

@app.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('confirm_email', token = token, _external = True)
    html = render_template('logging/sign_confirm.html', confirm_url = confirm_url)
    subject = "Ponownie wysłany link potwierdzający"
    send_email(current_user.email, subject, html)
    flash("Nowy email potwierdzający został wysłany na podaną skrzynkę mailową")
    return redirect(url_for('unconfirmed'))


# part about adding new entries to the database starts here
@app.route("/add/")
@login_required
@check_confirmed
def add():
    projects_exist = 0
    if User.query.get(int(session["user_id"])).project_id:
        projects_exist = 1
    return render_template("addition/add.html", nav = "add", projects_exist = projects_exist)

@app.route("/add/project/", methods=["GET","POST"])
@login_required
@check_confirmed
def add_project():
    form = ProjectForm()
    if request.method == "POST":
        project=Project(name = request.form.get("name"),
        description = request.form.get("description"),
        submiter_id = int(session["user_id"]))
        project.isworked.append(User.query.get(int(session["user_id"])))
        db.session.add(project)
        db.session.commit()
        project.id_ = len(User.query.get(int(session["user_id"])).project_id)
        db.session.add(project)
        db.session.commit()
        flash("Pomyślnie dodano nowy projekt")
        return redirect(url_for("homepage_projects"))
    return render_template("addition/add_project.html", nav = "add", form = form)

@app.route("/add/bug/", methods = ["GET","POST"])
@login_required
@check_confirmed
def add_bug():
    form = BugForm()
    projects = User.query.get(int(session["user_id"])).project_id
    if request.method == "POST":
        project_id = int(request.form.get("project_id"))
        bug = Bug(topic = request.form.get("topic"),
        importance = request.form.get("importance"),
        description = request.form.get("description"),
        project_id = project_id,
        user_id = int(session["user_id"]))
        db.session.add(bug)
        db.session.commit()
        bug.id_ = len(Project.query.get(project_id).bug_id)
        db.session.add(bug)
        db.session.commit()
        if "tag_id" in request.form:
                tags_ = request.form.get("tag_id").replace(" ","")
                tags = tags_.split(",")
                for tag in tags:
                    try:
                        existing_tag = Tag.query.filter_by(name = tag).first()
                        existing_tag.describes.append(bug)
                        db.session.add(existing_tag)
                        db.session.commit()
                    except:
                        if tag != "":
                            new_tag = Tag(name = tag)
                            new_tag.describes.append(bug)
                            db.session.add(new_tag)
        if request.files["attachment"]:
            if limit_extensions == True:
                if allowed_file(request.files["attachment"].filename):
                    allow_attachment = True
                else:
                    allow_attachment = False
            else:
                allow_attachment = True
            if allow_attachment == True:
                file = request.files["attachment"]
                attachment = Attachment(
                    filename = file.filename,
                    attachment = file.read(),
                    bug_id = bug.id
                    )
                db.session.add(attachment)
            else:
                flash("Złe rozszerzenie załącznika")
        action = Action(kind = "Dodano błąd",
        bug_id = bug.id)
        db.session.add(action)
        db.session.commit()
        flash("Pomyślnie zgłoszono nowy błąd")
        return redirect(url_for("homepage"))
    return render_template("addition/add_bug.html", nav = "add", form = form, projects = projects)

@app.route("/add_user_to_project/", methods = ["GET","POST"])
@login_required
@check_confirmed
def add_user_to_project():
    form = UserProjectForm()
    projects = User.query.get(int(session["user_id"])).project_id
    if request.method == "POST":
        user = User.query.filter(User.login == request.form.get("user_login")).first()
        project = Project.query.get(int(request.form.get("project_id")))
        project.isworked.append(user)
        db.session.commit()
        flash(f"Nowy użytkownik został dodany do projektu {project.name}")
        return redirect(url_for("homepage"))
    return render_template("addition/add_user_to_project.html", nav = "add", form = form, projects = projects)

# part about editing existing entries starts here
@app.route("/edit/project/<int:id>", methods = ["GET","POST"])
@login_required
@check_confirmed
def edit_project(id):
    project = Project.query.get(id)
    form = ProjectForm(name = project.name, description = project.description)
    if request.method == "POST":
        project.name = request.form.get("name")
        project.description = request.form.get("description")
        db.session.add(project)
        db.session.commit()
        flash(f"{project.name} został edytowany")
        return redirect(url_for("homepage_projects"))
    return render_template("editing/edit_project.html", form = form)

@app.route("/edit/bug/<int:id>", methods = ["GET","POST"])
@login_required
@check_confirmed
def edit_bug(id):
    bug = Bug.query.get(id)
    form = BugForm(topic = bug.topic,
    importance = bug.importance,
    description = bug.description,
    tag_id = bug.tag_id)
    if request.method == "POST":
        bug.topic = request.form.get("topic")
        bug.importance = request.form.get("importance")
        bug.description = request.form.get("description")
        db.session.add(bug)
        db.session.commit()
        if "tag_id" in request.form:
            # Square brackets are removed becouse they are inserted automatically into Tag input field during editing
                tags_ = request.form.get("tag_id").replace(" ","").replace("[","").replace("]","")
                tags = tags_.split(",")
                all_tags =  Tag.query.all()
                for tag in all_tags:
                    if tag.name not in tags:
                        try:
                            tag.describes.remove(bug)
                            db.session.add(tag)
                            db.session.commit()
                        except:
                            pass
                for tag in tags:
                    try:
                        existing_tag = Tag.query.filter_by(name = tag).first()
                        existing_tag.describes.append(bug)
                        db.session.add(existing_tag)
                        db.session.commit()
                    except:
                        if tag != "":
                            new_tag=Tag(name = tag)
                            new_tag.describes.append(bug)
                            db.session.add(new_tag)
        action = Action(kind = "Edytowano błąd",
        bug_id = bug.id)
        db.session.add(action)
        db.session.commit()
        flash(f"Edytowano błąd: {bug.topic}")
        return redirect(url_for("detailed_view", id =  id))
    return render_template("editing/edit_bug.html", form = form, bug = bug)

# part about detailed bug view and managing attachments starts here
@app.route("/detailed/<int:id>", methods = ["GET","POST"])
@login_required
@check_confirmed
def detailed_view(id):
    bug = Bug.query.get(id)
    project = Project.query.get(int(bug.project_id))
    sub = User.query.get(project.submiter_id)
    attachments = Attachment.query.filter_by(bug_id = bug.id).all()
    if request.method == "POST":
        bug.status = request.form.get("status")
        db.session.add(bug)
        db.session.commit()
        action = Action(kind = f"Zmieniono status błędu na {bug.status}",
        bug_id = bug.id)
        db.session.add(action)
        db.session.commit()
        flash(f"Zmieniono status na {bug.status}")
        return render_template("detailed_view.html", bug = bug, project = project, sub = sub, attachments = attachments)
    return render_template("detailed_view.html", bug = bug, project = project, sub = sub, attachments = attachments)

@app.route("/bug/history/<int:id>")
@login_required
@check_confirmed
def bug_history(id):
    bug = Bug.query.get(id)
    actions = bug.actions
    return render_template("bug_history.html", bug = bug, actions = actions[::-1])

@app.route("/add/attachment/<int:id>", methods = ["GET","POST"])
@login_required
@check_confirmed
def change_attachments(id):
    bug = Bug.query.get(id)
    if request.method == "POST":
        if request.files["attachment"]:
            if limit_extensions == True:
                if allowed_file(request.files["attachment"].filename):
                    allow_attachment = True
                else:
                    allow_attachment = False
            else:
                allow_attachment = True
            if allow_attachment == True:
                file = request.files["attachment"]
                attachment = Attachment(
                    filename = file.filename,
                    attachment = file.read(),
                    bug_id=bug.id
                )
                db.session.add(attachment)
                db.session.commit()
                action = Action(kind = f"Dodano załącznik o nazwie {attachment.filename}",
                    bug_id = bug.id)
                db.session.add(action)
                db.session.commit()
                flash("Dodano załącznik")
            else:
                flash("Złe rozszerzenie załącznika")
        return redirect(url_for("detailed_view", id = id))

@app.route("/download/<int:id>")
@login_required
@check_confirmed
def download(id):
    attachment = Attachment.query.get(id)
    return send_file(BytesIO(attachment.attachment), attachment_filename = attachment.filename, as_attachment = True)

@app.route("/delete/attachment/<int:bug_id>/<int:atach_id>")
@login_required
@check_confirmed
def delete_attachment(bug_id,atach_id):
    attachment = Attachment.query.get(atach_id)
    db.session.delete(attachment)
    db.session.commit()
    action = Action(kind = f"Usunięto załącznik o nazwie {attachment.filename}",
        bug_id = bug_id)
    db.session.add(action)
    db.session.commit()
    flash("Usunięto załącznik")
    return redirect(url_for("detailed_view", id = bug_id))

# part about searching starts here
@app.route("/search/", methods = ["POST"])
@login_required
@check_confirmed
def search():
    form = SearchForm()
    projects = User.query.get(int(session["user_id"])).project_id
    user_bugs = projects[1:1]
    for project in projects:
            user_bugs += project.bug_id
    if form.validate_on_submit:
        searched = request.form.get("searched")
        bugs = Bug.query.filter(Bug.topic.like("%" + searched + "%")).all()
        bugs = [bug for bug in bugs if bug in user_bugs]
        if bugs == []:
                flash("Brak wyników")
        return render_template("searching/search.html", form = form, searched = searched, bugs = sorted(bugs, key = lambda x:x.id)[::-1],
                                projects = projects, nav = "search")

@app.route("/search/advenced")
@login_required
@check_confirmed
def advanced_search():
    return render_template("searching/advanced_search.html", nav = "search")

@app.route("/search/users/", methods = ["GET","POST"])
@login_required
@check_confirmed
def search_users():
    form = SearchForm()
    if request.method == "POST":
        if form.validate_on_submit:
            searched = request.form.get("searched")
            form = SearchForm(searched = searched)
            users = User.query.filter(User.login.like("%" + searched + "%")).all()
            if request.form.get("sor_by") == "login":
                users = sorted(users, key = lambda x:x.login)
            elif request.form.get("sor_by") == "id":
                users = sorted(users, key = lambda x:x.id)
            if request.form.get("order") == "decreasing":
                users = users[::-1]
            if users == []:
                flash("Brak wyników")
            return render_template("searching/search_users.html", form = form, searched = searched, users = users, nav = "search")
    return render_template("searching/search_users.html", form = form, nav = "search")

@app.route("/search/projects/<search_by>", methods = ["GET","POST"])
@login_required
@check_confirmed
def search_projects(search_by):
    form = SearchForm()
    user_projects = User.query.get(int(session["user_id"])).project_id
    bugs = user_projects[1:1]
    for project in user_projects:
            bugs += project.bug_id
    if request.method == "POST":
        if form.validate_on_submit:
            searched = request.form.get("searched")
            form = SearchForm(searched = searched)
            if search_by == "description":
                projects = Project.query.filter(Project.description.like("%" + searched + "%")).all()
            else:
                projects = Project.query.filter(Project.name.like("%" + searched + "%")).all()
            final_projects = user_projects[1:1]
            for project in projects:
                if project in user_projects:
                    final_projects.append(project)
            projects = final_projects
            if request.form.get("sor_by") == "id":
                projects = sorted(projects, key = lambda x:x.id)
            elif request.form.get("sor_by") == "name":
                projects = sorted(projects, key = lambda x:x.name)
            elif request.form.get("sor_by") == "len_bugs":
                projects = sorted(projects, key = lambda x:len(x.bug_id))
            if request.form.get("order") == "decreasing":
                projects = final_projects[::-1]
            if projects == []:
                flash("Brak wyników")
            return render_template("searching/search_projects.html", form = form, searched = searched, bugs = bugs,
                                    projects = projects, search_by = search_by, nav = "search")
    return render_template("searching/search_projects.html", form = form, search_by = search_by, nav = "search")
    
@app.route("/search/bugs/<search_by>", methods = ["GET","POST"])
@login_required
@check_confirmed
def search_bugs(search_by):
    form = SearchForm()
    bugs = Bug.query
    projects = User.query.get(int(session["user_id"])).project_id
    user_bugs = projects[1:1]
    for project in projects:
            user_bugs += project.bug_id
    if request.method == "POST":
        if form.validate_on_submit:
            searched = request.form.get("searched")
            form = SearchForm(searched = searched)
            if search_by == "topic":
                bugs = Bug.query.filter(Bug.topic.like("%" + searched + "%")).all()
            if search_by == "project":
                projects_bugs = projects[1:1]
                search_project = Project.query.filter(Project.name.like("%" + searched + "%")).all()
                for project in search_project:
                    projects_bugs += project.bug_id
                bugs = projects_bugs
            if search_by == "description":
                bugs = Bug.query.filter(Bug.description.like("%" + searched + "%")).all()
            if search_by == "status":
                if request.form.get("stat") == "unresolved":
                    bugs = Bug.query.filter_by(status = "nierozwiązany").all()
                    searched = "nierowiązanych"
                if request.form.get("stat") == "resolved":
                    bugs = Bug.query.filter_by(status = "rozwiązany").all()
                    searched = "rozwiązanych"
            if search_by == "tag":
                bugs = projects[1:1]
                tag_bugs = projects[1:1]
                tags = request.form.get("tags").replace(" ","")
                tags = tags.split(",")
                searched = "Wyniki:"
                for tag in tags:
                    try:
                        existing_tag = Tag.query.filter_by(name=tag).first()
                        tag_bugs += existing_tag.bug_id
                    except:
                        flash("Nie odnaleziono tagu")
                if request.form.get("joined") == None:
                    for bug in tag_bugs:
                        if bug not in bugs:
                            bugs.append(bug)
                else:
                    for bug in tag_bugs:
                        is_absent = 0
                        for tag in tags:
                            existing_tag = Tag.query.filter_by(name=tag).first().bug_id
                            if bug not in existing_tag:
                                is_absent = 1
                        if is_absent == 0 and bug not in bugs:
                            bugs.append(bug)
            bugs = [bug for bug in bugs if bug in user_bugs]
            if search_by == "importance":
                searched = request.form.get("importance")
                bugs = Bug.query.filter(Bug.importance.like("%" + searched + "%")).all()
            if request.form.get("sor_by") == "id":
                bugs = sorted(bugs, key = lambda x:x.id)
            elif request.form.get("sor_by") == "topic":
                bugs = sorted(bugs, key = lambda x:x.topic)
            elif request.form.get("sor_by") == "importance":
                bugs = sorted(bugs, key = lambda x:importance_to_num(x.importance))
            elif request.form.get("sor_by") == "project":
                bugs = sorted(bugs, key = lambda x:x.project_id)
            elif request.form.get("sor_by") == "status":
                bugs = sorted(bugs, key = lambda x:x.status)
            elif request.form.get("sor_by") == "len_att":
                bugs = sorted(bugs, key = lambda x:len(x.attachment))
            if request.form.get("order") == "decreasing":
                bugs = bugs[::-1]
            if bugs == []:
                flash("Brak wyników")
            return render_template("searching/search_bugs.html", form = form, searched = searched, bugs = bugs,
                                     projects = projects, search_by = search_by, nav = "search")
    return render_template("searching/search_bugs.html", form = form, search_by = search_by, nav = "search")

# part about settings starts here
@app.route("/settings/")
@login_required
def settings():
    return render_template("settings/settings.html", nav = "settings")

@app.route("/settings/login/change/", methods = ["GET","POST"])
@login_required
def login_change():
    user = User.query.get(int(session["user_id"]))
    form = ChangeForm()
    if request.method == "POST":
        if form.validate_on_submit:
            if check_password_hash(user.password, request.form["password"]):
                try:
                    user.login = request.form.get("new_data")
                    db.session.add(user)
                    db.session.commit()
                    flash("Login pomyślnie zmieniony")
                except:
                    flash("Podany login jest zajęty, prosze wybrać inny")
                return redirect(url_for("login_change"))    
            else:
                flash("Niepoprawne hasło")
    return render_template("settings/login_change.html", form = form, user = user, nav = "settings")

@app.route("/settings/password/change/", methods = ["GET","POST"])
@login_required
def password_change():
    user = User.query.get(int(session["user_id"]))
    form = ChangeForm()
    if request.method == "POST":
        if form.validate_on_submit:
            if check_password_hash(user.password, request.form["password"]):
                if request.form.get("new_data") == request.form.get("new_data_repeat"):
                    user.password = generate_password_hash(request.form.get("new_data"))
                    db.session.add(user)
                    db.session.commit()
                    flash("hasło pomyślnie zmienione")
                    return redirect(url_for("homepage"))
                else:
                    flash("Podałeś różne hasła jako nowe hasło")
            else:
                flash("Niepoprawne stare hasło")
    return render_template("settings/password_change.html", form = form, user = user, nav = "settings")

@app.route("/settings/email/change/", methods = ["GET","POST"])
def email_change():
    user = User.query.get(int(session["user_id"]))
    form = ChangeForm()
    if request.method == "POST":
        if form.validate_on_submit:
            if check_password_hash(user.password, request.form["password"]):
                if mail_ver == False:
                    user.email = request.form.get("new_data")
                    db.session.add(user)
                    db.session.commit()
                    flash("Mail pomyślnie zmieniony")
                else:
                    user.new_email = request.form.get("new_data")
                    db.session.add(user)
                    db.session.commit()
                    token = generate_confirmation_token(user.new_email)
                    confirm_url = url_for("email_change_confirm", token=token, _external=True)
                    html = render_template("settings/confirm_email_change.html", confirm_url=confirm_url)
                    subject = "Prosze o potwierdzenie nowego adresu email"
                    send_email(user.new_email, subject, html)
                    flash("Prosimy o sprawdzenie nowej skrzynki mailowej i użycie linku potwierdzającego")
                return redirect(url_for("settings"))    
            else:
                flash("Niepoprawne hasło")
    return render_template("settings/email_change.html", form = form, user = user, nav = "settings")

@app.route("/email/change/<token>")
@login_required
def email_change_confirm(token):
    try:
        new_email = confirm_token(token)
    except:
        flash("Link potwierdzający wygasł lub jest niepoprawny")
    user = User.query.filter_by(new_email = new_email).first()
    user.email = user.new_email
    db.session.add(user)
    db.session.commit()
    flash("Adres mailowy został pomyślnie zmieniony")
    return redirect(url_for("homepage"))

# part with routes that help with testing
@app.route("/test/del/")
def test_del():
    user = User.query.filter_by(login="test").first()
    projects = user.project_id[:]
    bugs = projects[1:1]
    tags = projects[1:1]
    for project in projects:
        bugs += project.bug_id
    for bug in bugs:
        tags += bug.tag_id
    for tag in tags:
        for bug in bugs:
            try:
                tag.describes.remove(bug)
            except:
                pass
    for project in projects:
        project.isworked.remove(user)
    for tag in tags:
        db.session.delete(tag)
    db.session.commit()
    for bug in bugs:
        db.session.delete(bug)
    db.session.commit()
    for project in projects:
        db.session.delete(project)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("homepage"))

# part about miscellaneous subjects starts here
@app.shell_context_processor
def make_shell_context():
   return {
       "db": db,
       "User" : User,
       "Bug" : Bug,
       "Project" : Project
   }

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__=="__main__":
    db.create_all()
    app.run(debug = False)