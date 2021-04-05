from flask import Flask, render_template, request, session, url_for, flash, redirect, abort, Markup
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_mail import Mail
from werkzeug.security import generate_password_hash
import os
import sys


sys.path.insert(0, '/newyorks/brownbros.newyorkscapes.org/')

from utils.db_handlers import fetch_new_segment, record_transcription, record_user_strokes, \
    retrieve_user, set_user, update_user, set_reset_pw, check_reset_pw, check_unique_token
from utils.emailer import send_reset_email, build_reset_pw
from models import LoginForm, RegistrationForm, ResetForm, User, \
    ResetRequestForm, ResetFormForgot
from settings import APP_SECRET_KEY, SEGMENT_DIR, CONTEXT_DIR, DEBUG, \
                    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME,\
                    MAIL_PASSWORD

app = Flask(__name__)
application = app
app.secret_key = APP_SECRET_KEY
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
mail = Mail(app)


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
                flash(Markup(
                    """<a class="btn btn-light btn-medium js-scroll-trigger" href=" """) + url_for(
                    'transcribe_segment') + Markup(""" ">Start Transcribing</a> """))
                return render_template('general_use_template.html', title_text="Thanks for registering!")
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
                flash(Markup(
                    """<a class="btn btn-light btn-medium js-scroll-trigger" href=" """) + url_for(
                    'transcribe_segment') + Markup(""" ">Start Transcribing</a> """))
                return render_template('general_use_template.html', title_text = "Login successful!" )
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
                    flash(Markup    ("""<a class="btn btn-light btn-medium js-scroll-trigger" href=" """) + url_for('transcribe_segment') + Markup(""" ">Start Transcribing</a> """))
                    return render_template('general_use_template.html', title_text="Password succesfully updated!")

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


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ResetRequestForm(request.form)

    if request.method == "POST" and form.validate():
        email = form.email.data.lower()

        if retrieve_user(email=email) != False:
            temp_pw, expire_date, unique_token = build_reset_pw()
            if set_reset_pw(email, generate_password_hash(temp_pw), expire_date, 0, unique_token):
                send_reset_email(email, temp_pw, mail, unique_token)
                flash("A temporary password has been sent to your email address. Please check your email and enter the password below.")
                return redirect(url_for('forgot_password_check', reset_email=email, next=unique_token))
            else:
                flash("An error occurred in sending a temporary password. Please try again.")
                return render_template('forgot_password.html', form=form)
        else:
           flash("Email not found. Please try again.")
           return render_template('forgot_password.html', form=form)

    return render_template('forgot_password.html', form=form)


@app.route('/forgot_password_check', methods=['GET', 'POST'])
def forgot_password_check():
    try:
        in_email = request.args.get('reset_email').replace('%40','@')
        sent_unique_token = request.args.get('next')
        let_pass = check_unique_token(in_email, sent_unique_token)
    except:
        flash("A password reset is not available.")
        return render_template('general_use_template.html', title_text="Error in resetting password.")
    form = LoginForm(request.form, email=in_email)

    if request.method == "POST" and let_pass == True:
        user_email = form.email.data.lower()
        message = check_reset_pw(user_email, form.password.data)
        if message == True:
            return redirect(url_for('reset_forgot', next=sent_unique_token, reset_email=user_email))

        else:
            flash(message)
            if "incorrect" in message:
                return redirect(url_for('forgot_password_check', next=sent_unique_token, reset_email=user_email))
            return redirect(url_for('forgot_password'))

    """
    Initial arrival at reset password site. Since this page is not login/password protected, we don't allow anyone to direct access the page as a GET
    without having the correct unique_token attached to the user's email's reset password. 
    """
    if let_pass:
        return render_template('temp_reset_login.html', form=form, next=sent_unique_token, reset_email=in_email)


@app.route('/reset_forgot', methods=['GET', 'POST'])
def reset_forgot():
    try:
        in_email = request.args.get('reset_email').replace('%40','@')
        sent_unique_token = request.args.get('next')
        let_pass = check_unique_token(in_email, sent_unique_token)
    except:
        flash("Password reset was not successful. Please try again.")
        return render_template('general_use_template.html', title_text="Error in resetting password.")

    form = ResetFormForgot(request.form)


    if request.method == "POST" and form.validate():
        new_password = generate_password_hash(form.new_password.data)
        change_user = update_user(in_email, new_password)
        if change_user:
            flash(Markup(
                """<a class="btn btn-light btn-medium js-scroll-trigger" href=" """) + url_for(
                'transcribe_segment') + Markup(""" ">Start Transcribing</a> """))
            return render_template('general_use_template.html', title_text = "Password succesfully updated!")

        else:
            flash("An error occurred in updating password. Please try again.")
            return render_template('reset_forgot.html', form=form, reset_email=user_email, next=sent_unique_token)

    if let_pass:
        return render_template('reset_forgot.html', form=form, reset_email=in_email, next=sent_unique_token)

    else:
        return abort(400)

if __name__ == '__main__':
    app.run(debug = DEBUG)
