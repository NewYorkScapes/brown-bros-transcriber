from flask import Markup
from flask_login import UserMixin
from wtforms import Form, BooleanField, TextField, StringField, PasswordField, SubmitField
from wtforms.validators import Required, DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db_handlers import retrieve_user


"""
Login/User Classes
"""

class LoginForm(Form):
    email = TextField('Email', [Email(message="Please enter a valid email address."), DataRequired()])
    password = PasswordField('Password', [DataRequired()])


class ResetRequestForm(Form):
    email = TextField('Email', [Email(message="Please enter the email address associated with your account. If it matches one in our system, a reset email will be sent."), DataRequired()])


class RegistrationForm(Form):
    email = TextField('Email Address', [Email(message="Please enter a valid email address"), DataRequired()])
    password = PasswordField('Select a Password', [
        DataRequired(),
        Length(min=8, message='Password should be at least %(min)d characters long.'),
        EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField(Markup('I agree to the <a data-toggle="modal" href="#data_use_Modal">data use policy</a>.'), [Required()])


class ResetForm(Form):
    email = TextField('Email Address', [Email(message="Please enter a valid email address"), DataRequired()])
    password = PasswordField('Current Password', [DataRequired()])
    new_password = PasswordField('New Password', [
        DataRequired(),
        Length(min=8, message='Password should be at least %(min)d characters long.'),
        EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Repeat Password')


class ResetFormForgot(Form):
    new_password = PasswordField('New Password', [
        DataRequired(),
        Length(min=8, message='Password should be at least %(min)d characters long.'),
        EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Repeat Password')


class User(UserMixin):
    def __init__(self, email_or_user_id):
        if '@' in email_or_user_id:
            user_info = retrieve_user(email=email_or_user_id)
        else:
            user_info = retrieve_user(user_id=email_or_user_id)
        if user_info != False:
            self.user_found = True
            self.id = str(user_info[0][0])
            self.email = user_info[0][1]
            self.password_hash = user_info[0][2]
            self.access = user_info[0][3]
        else:
            self.user_found = False

    def is_admin(self, access_level):
        return self.access == access_level

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)