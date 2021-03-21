from flask_login import UserMixin
from wtforms import Form, BooleanField, TextField, StringField, PasswordField, SubmitField
from wtforms.validators import Required, DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db_handlers import retrieve_user


class LoginForm(Form):
    email = StringField('Email', [Email(message="Please enter a valid email address."), DataRequired(), Length(max=120)])
    password = PasswordField('Password', [DataRequired()])


class RegistrationForm(Form):
    email = TextField('Email Address: ', [Email(message="Please enter a valid email address"), DataRequired()])
    password = PasswordField('New Password: ', [
        DataRequired(),
        Length(min=8, message='Password should be at least %(min)d characters long.'),
        EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Repeat password')
    accept_tos = BooleanField('I have read and understood the website data use policy.', [Required()])


class User(UserMixin):
    def __init__(self, email_or_user_id):
        if '@' in email_or_user_id:
            user_info = retrieve_user(email=email_or_user_id)
        else:
            user_info = retrieve_user(user_id=email_or_user_id)
        self.id = str(user_info[0][0])
        self.email = user_info[0][1]
        self.password_hash = user_info[0][2]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)