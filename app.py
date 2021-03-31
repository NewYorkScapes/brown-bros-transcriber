from flask import Flask, render_template, request, session, url_for, flash, redirect, abort, Markup
from flask_login import LoginManager, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
import os
import sys


sys.path.insert(0, '/newyorks/brownbros.newyorkscapes.org/')

from utils.db_handlers import fetch_new_segment, record_transcription, record_user_strokes, \
    retrieve_user, set_user, update_user
from models import LoginForm, RegistrationForm, ResetForm, User
from settings import APP_SECRET_KEY, SEGMENT_DIR, CONTEXT_DIR, DEBUG

app = Flask(__name__)
#application = app
app.secret_key = APP_SECRET_KEY
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/narrative')
def narrative():
    return render_template("narrative.html")


"""
TRANSCRIPTION MANAGEMENT ROUTES
"""

@app.route('/segment')
@login_required
def transcribe_segment():
    new_segments = fetch_new_segment()
    if new_segments != None:
        segment_filename, session['current_row_id'], context_filename = new_segments[0], new_segments[1], new_segments[2]
        current_image = os.path.join(SEGMENT_DIR, segment_filename)
        context_image = os.path.join(CONTEXT_DIR, context_filename)
        return render_template('segment_transcription_page.html', image_url = current_image, context_url = context_image)
    flash("No segments currently available to transcribe.")
    return render_template("thanks.html")


@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
    try:
        if_illegible = 1 if request.form['illegible'] == "True" else 0
    except:
        if_illegible = 0
    try:
        if_blank = 1 if request.form['blank'] == "True" else 0
    except:
        if_blank = 0

    recorded_success = record_transcription(request.form['segment_transcription'],
                                    if_illegible, if_blank,
                                    session.get('current_row_id', None),
                                    session.get('user_transcriber', None))
    if recorded_success:
        flash("Response successfully recorded.")
    else:
        flash("Error in recording response.")
    list_stroke_coords = request.form['segment_coords'].split('|')[:-1]
    if len(list_stroke_coords):
        for stroke_coords in list_stroke_coords:
            insert_row = tuple([i for i in stroke_coords.split('-')] + [session.get('current_row_id', None),session.get('user_transcriber', None)],)
            strokes_success = record_user_strokes(insert_row)
            if strokes_success:
                flash("Success recording segments separation.")
            else:
                flash("Error in recording segments separation.")
    return render_template("thanks.html")


"""
USER MANAGEMENT ROUTES
"""

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/register', methods=["GET", "POST"])
def register_page():
    form = RegistrationForm(request.form)

    if request.method == "POST" and form.validate():
        email = form.email.data.lower()
        password = generate_password_hash(form.password.data)
        users_check = retrieve_user(email)

        if len(users_check) > 0:
            flash("That email address has already been registered. Please log in or select a different email address.")
            return render_template('register.html', form=form, alert=True)

        else:
            add_user = set_user(email, password)
            if add_user:
                flash("Thanks for registering!")
                return transcribe_segment()
            else:
                flash("An error occurred in registration. Please try again.")
                return render_template('register.html', form=form)

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        """
        Normal use of login page to log in using POST method.
        """
        try:
            user = User(form.email.data.lower())

            if user.check_password(form.password.data):
                login_user(user, remember=True)
                session['user_transcriber'] = user.id

                next = request.args.get('next')
                if next not in ['', 'transcriber']:
                    return abort(400)
                return home()
            else:
                flash("Incorrect password. Please try again.")
                return render_template('login.html', form=form)

        except:
            """
            This scenario should happen only if user-provided email is 
            not found, indicating a mistype or attempt to login with 
            non-registered user
            """
            flash("User not found. Please try again.")
            return render_template('login.html', form=form)

    if request.method == "GET":
        """
        This request occurs when a user logs out; the system redirects to login page again.
        """
        return render_template('login.html', form=form)

    """
    Some other kind of error in landing on login page. Shouldn't normally happen.
    """
    flash("An error occurred during login. Please try again.")
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect(url_for('login'))


@app.route('/reset', methods=["GET", "POST"])
@login_required
def reset_page():
    form = ResetForm(request.form)

    if request.method == "POST" and form.validate():
        email = form.email.data.lower()
        new_password = generate_password_hash(form.new_password.data)

        user = User(email)
        if user:
            if user.check_password(form.password.data):

                change_user = update_user(email, new_password)
                if change_user:
                    flash(Markup("""Password succesfully updated! <br/><br/><a class="btn btn-light btn-medium js-scroll-trigger" href=" """) + url_for('transcribe_segment') + Markup(""" ">Start Transcribing</a> """))
                    return render_template('reset.html', form=form)
                else:
                    flash("An error occurred in updating password. Please try again.")
                    return render_template('reset.html', form=form)

            else:
                flash("Incorrect password. Please try again.")
                return render_template('reset.html', form=form)

        else:
            flash("Email not found. Please try again.")
            return render_template('reset.html', form=form)

    return render_template("reset.html", form=form)


@app.route('/profile', methods=["GET"])
@login_required
def profile():
    email = User(session.get('user_transcriber', None)).email
    return render_template("profile.html", account_email=email)


if __name__ == '__main__':
    app.run(debug = DEBUG)
