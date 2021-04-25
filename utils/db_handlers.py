import sqlite3
import io
import csv
from random import random
from settings import DB
from werkzeug.security import check_password_hash
from utils.emailer import check_if_expired

def fetch_new_segment():
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""SELECT * FROM segments WHERE number_passes < 3""")
            rows = cur.fetchall()
            random_row = int(random()*len(rows))
            if len(rows) > 0:
                return rows[random_row][0], rows[random_row][5], rows[random_row][10]
            return False
    except:
        return False
    finally:
        con.close()



def record_transcription(transcription, if_illegible, if_blank, row_num, user_transcriber):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (segment_id, 
                          transcription, user_transcriber, 
                          marked_illegible, marked_blank) VALUES (?,?,?,?,?)""",(row_num, transcription, user_transcriber, if_illegible, if_blank) )
            #Set this back to number_passes + 1 when ready to go to production
            cur.execute("""UPDATE segments SET number_passes = number_passes + 1 WHERE segment_id = ?""", (row_num,) )
            con.commit()
        return True
    except:
        return False
    finally:
        con.close()

def record_user_strokes(id_plus_coords):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_stroke_coordinates (x1_coord, y1_coord, x2_coord, y2_coord, segment_id, user_transcriber) VALUES (?,?,?,?,?,?)""",(id_plus_coords) )
            con.commit()
        return True
    except:
        return False
    finally:
        con.close()


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
        return False
    finally:
        con.close()


def set_user(email, password, access):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO users (email, password_hash, is_admin) VALUES (?,?,?)""",(email, password, access) )
            con.commit()
        return True
    except:
       return False
    finally:
        con.close()


def update_user(email, password):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""UPDATE users SET password_hash = ? WHERE email = ?""",(password, email) )
            con.commit()
        return True
    except:
        return False
    finally:
        con.close()


def set_reset_pw(user_email, temp_pw, expire_date, if_used, unique_token):
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_reset (user_email, temp_password, expiration_date, if_used, unique_token) VALUES (?,?,?,?,?)""", (user_email, temp_pw, expire_date, if_used, unique_token))
            con.commit()
        return True
    except:
        return False
    finally:
        con.close()


def check_unique_token(user_email, token):
    try:
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
    except:
        return False
    finally:
        con.close()


def check_reset_pw(user_email, temp_pw):
    try:
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
    except:
        return "A problem occurred with finding your account. Please try entering again."
    finally:
        con.close()


def make_report():
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""SELECT number_passes, COUNT(*) FROM segments GROUP BY number_passes""")
            seg_passes = cur.fetchall()
            cur.execute("""SELECT year, COUNT(*) FROM segments GROUP BY year""")
            year_counts = cur.fetchall()
            cur.execute("""SELECT user_transcriber, COUNT(*) FROM transcriptions GROUP BY user_transcriber""")
            per_transcriber_count = cur.fetchall()
            cur.execute("""SELECT COUNT(*) FROM transcriptions WHERE transcription != ''; """)
            number_with_transcriptions = cur.fetchall()
            cur.execute("""SELECT COUNT(*) FROM transcriptions WHERE marked_illegible = 1""")
            number_marked_illegible = cur.fetchall()
            cur.execute("""SELECT COUNT(*) FROM transcriptions WHERE marked_blank = 1""")
            number_marked_blank = cur.fetchall()
            return seg_passes, year_counts, per_transcriber_count, number_with_transcriptions, number_marked_illegible, number_marked_blank
    except:
        return False
    finally:
        con.close()


def make_transcriptions_csv():
    try:
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("""PRAGMA table_info('segments')""")
            seg_cols = cur.fetchall()
            seg_cols = [i[1] for i in seg_cols]
            cur.execute("""PRAGMA table_info('transcriptions')""")
            transcriptions_cols = cur.fetchall()
            transcriptions_cols = [i[1] for i in transcriptions_cols]
            cur.execute("""PRAGMA table_info('user_stroke_coordinates')""")
            stroke_cols = cur.fetchall()
            stroke_cols = [i[1] for i in stroke_cols]
            all_cols = transcriptions_cols + seg_cols + stroke_cols
            cur.execute("""SELECT * FROM transcriptions LEFT JOIN segments ON transcriptions.segment_id = segments.segment_id LEFT JOIN user_stroke_coordinates ON transcriptions.segment_id = user_stroke_coordinates.record_id""")
            rows = cur.fetchall()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(all_cols)
            for row in rows:
                writer.writerow(list(row))
            output.seek(0)
            return output
    except:
        return False
    finally:
        con.close()