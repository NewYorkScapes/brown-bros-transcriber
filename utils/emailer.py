from flask_mail import Message
import string
from random import random
from datetime import datetime, timedelta


def send_reset_email(user_email, reset_code, mail):
    msg = Message()
    msg.subject = "Transcriber Account"
    msg.recipients = [user_email]
    msg.sender = 'do-not-reply@newyorkscapes.org'
    message_html = """
                <p>You are receiving this email because you requested to change your account login</p>
                <p>To reset your password please <a href="https://brownbros.newyorkscapes.org/forgot_password_check?next=forgot">login</a> using the following temporary credentials:</p>
                <p><b>Email:</b> {0}</p>
                <p><b>Password:</b> {1}</p>
                <p>These credentials will expire within 24 hours</p>
                """.format(user_email, reset_code)
    msg.html = message_html
    mail.send(msg)


def build_reset_pw():
    avail_chars = [i for i in string.ascii_uppercase] + [str(i) for i in range(2,10)]
    avail_chars.remove("I")
    avail_chars.remove("O")
    temp_pw = ''
    for i in range(0,9):
        temp_pw += avail_chars[int(random()*len(avail_chars))]
    expire_date = (datetime.today() + timedelta(days = 1)).isoformat()
    return temp_pw, expire_date


def check_if_expired(expire_time):
    return (datetime.today() + timedelta(days = 1)) < datetime.fromisoformat(expire_time)