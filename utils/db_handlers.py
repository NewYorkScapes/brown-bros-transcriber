import sqlite3
from random import random
from settings import DB
from werkzeug.security import check_password_hash
from utils.emailer import check_if_expired

def fetch_new_segment():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM segments WHERE number_passes < 3""")
        rows = cur.fetchall()
        random_row = int(random()*len(rows))
        if len(rows) > 0:
            return rows[random_row][0], rows[random_row][5], rows[random_row][10]
        return None


def record_transcription(transcription, if_illegible, if_blank, row_num, user_transcriber):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (segment_id, 
                          transcription, user_transcriber, 
                          marked_illegible, marked_blank) VALUES (?,?,?,?,?)""",(row_num, transcription, user_transcriber, if_illegible, if_blank) )
            #Set this back to number_passes + 1 when ready to go to production
            cur.execute("""UPDATE segments SET number_passes = number_passes + 0 WHERE segment_id = ?""", (row_num,) )
            con.commit()
        return True
    except:
        con.rollback()
        return False


def record_user_strokes(id_plus_coords):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_stroke_coordinates (x1_coord, y1_coord, x2_coord, y2_coord, segment_id, user_transcriber) VALUES (?,?,?,?,?,?)""",(id_plus_coords) )
            con.commit()
        return True
    except:
        con.rollback()
        return False


def retrieve_user(email=False, user_id=False):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            if not user_id:
                cur.execute("""SELECT * FROM users WHERE email = ?""", (email,) )
            else:
                cur.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
            rows = cur.fetchall()
        return rows
    except:
        con.rollback()
        return False


def set_user(email, password):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO users (email, password_hash) VALUES (?,?)""",(email, password) )
            con.commit()
        return True
    except:
        con.rollback()
        return False


def update_user(email, password):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""UPDATE users SET password_hash = ? WHERE email = ?""",(password, email) )
            con.commit()
        return True
    except:
        con.rollback()
        return False


def set_reset_pw(user_email, temp_pw, expire_date, if_used, unique_token):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_reset (user_email, temp_password, expiration_date, if_used, unique_token) VALUES (?,?,?,?,?)""", (user_email, temp_pw, expire_date, if_used, unique_token))
            con.commit()
        return True
    except:
        con.rollback()
        return False


def check_unique_token(user_email, token):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM user_reset WHERE user_email = ? ORDER BY rowid DESC LIMIT 1""", (user_email,))
        rows = cur.fetchall()
        if len(rows) == 1:
            if not check_if_expired(rows[0][2]):
                if rows[0][4] == token:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


def check_reset_pw(user_email, temp_pw):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM user_reset WHERE user_email = ? ORDER BY rowid DESC LIMIT 1""", (user_email,))
        rows = cur.fetchall()
        print(rows)
        if len(rows) == 1 and rows[0][3] != 1:
            if not check_if_expired(rows[0][2]):
                if check_password_hash(rows[0][1], temp_pw):
                    cur.execute("""UPDATE user_reset SET if_used = 1 WHERE user_email = ? AND expiration_date = ?""", (rows[0][0],rows[0][2]))
                    return True
                else:
                    return "Temporary password was incorrect, try entering again."
            else:
                return "Temporary password has expired. Please request a password reset again."
        else:
            return "No temporary password was set or it has already been used. Please request a password reset again."


