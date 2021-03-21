from flask import Flask, render_template, request, session, url_for, flash, redirect, abort
from flask_login import LoginManager, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
import os
from utils.db_handlers import fetch_new_segment, record_transcription, record_user_strokes, retrieve_user, set_user
from models import LoginForm, RegistrationForm, User

app = Flask(__name__)
app.secret_key = "L2*@AZP3z-/kR4vC4*VCK7JfNr"
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

SEGMENT_DIR = os.path.join('static', 'segments')


@app.route('/')
@login_required
def transcriber_home():
    segment_filename, session['current_row_id'] = fetch_new_segment()
    current_image = os.path.join(SEGMENT_DIR, segment_filename)
    return render_template('home.html', image_url = current_image)


@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
    msg = record_transcription(request.form['segment_transcription'], session.get('current_row_id', None), session.get('user_transcriber', None))
    list_stroke_coords = request.form['segment_coords'].split('|')[:-1]
    if len(list_stroke_coords):
        for stroke_coords in list_stroke_coords:
            insert_row = tuple([i for i in stroke_coords.split('-')] + [session.get('current_row_id', None),session.get('user_transcriber', None)],)
            stroke_coords_msg = record_user_strokes(insert_row)
    else:
        stroke_coords_msg = "No segments produced."
    return render_template("thanks.html", msg=msg + '. ' + stroke_coords_msg)
    con.close()


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/register', methods=["GET", "POST"])
def register_page():
    form = RegistrationForm(request.form)

    if request.method == "POST" and form.validate():
        email = form.email.data
        password = generate_password_hash(form.password.data)
        users_check = retrieve_user(email)

        if len(users_check) > 0:
            flash("That username has already been registered. Select another.")
            return render_template('register.html', form=form, alert=True)

        else:
            add_user = set_user(email, password)
            if add_user:
                flash("Thanks for registering!")
                return transcriber_home()
                con.close()
            else:
                flash("An error occurred in registering user. Please try again.")
                return render_template('register.html', form=form)

    return render_template("register.html", form=form, alert=False)
    con.close()


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        """
        Normal use of login page to log in using POST method.
        """
        user = User(form.email.data)
        if user:
            if user.check_password(form.password.data):
                login_user(user, remember=True)
                session['user_transcriber'] = user.id

                next = request.args.get('next')
                if next not in ['', 'transcriber']:
                    return abort(400)
                flash("Logged in successfully.")
                return transcriber_home()
            else:
                flash("Incorrect password. Please try again.")
                return render_template('login.html', form=form)
    if request.method == "GET":
        """
        This request occurs when a user logs out; the system redirects to login page again.
        """
        return render_template('login.html', form=form)

    """
    Some other kind of error in landing on login page. Shouldn't normally happen.
    """
    flash("An error occurred during log in. Please try again.")
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug = True)
