import sqlite3

def fetch_new_segment():
    with sqlite3.connect("transcriptions.db") as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM segments WHERE number_passes < 3 AND checkout = 0 LIMIT 1""")
        rows = cur.fetchall()
        if len(rows) > 0:
            filename = rows[0][0]
            id = rows[0][5]
            cur.execute("""UPDATE segments SET checkout = 1 WHERE segment_id = ?""", (id,))
            return filename, id
        return None


def record_transcription(transcription, row_num, user_transcriber):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (segment_id, transcription, user_transcriber) VALUES (?,?,?)""",(row_num, transcription, user_transcriber) )
            cur.execute("""UPDATE segments SET number_passes = number_passes + 1, checkout = 0 WHERE segment_id = ?""", (row_num,) )
            con.commit()
        return "Record successfully added"
    except:
        con.rollback()
        return "Error in insert operation"

def record_user_strokes(id_plus_coords):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_stroke_coordinates (x1_coord, y1_coord, x2_coord, y2_coord, segment_id, user_transcriber) VALUES (?,?,?,?,?,?)""",(id_plus_coords) )
            con.commit()
        return "User-provided stroke segments added to database."
    except:
        con.rollback()
        return "Error in insert operation"


def retrieve_user(email=False, user_id=False):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            if not user_id:
                cur.execute("""SELECT * FROM users WHERE email = ?""", (email,) )
            else:
                cur.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
            rows = cur.fetchall()
        return rows
    except:
        con.rollback()
        return "Error in insert operation"


def set_user(email, password):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO users (email, password_hash) VALUES (?,?)""",(email, password) )
            con.commit()
        return True
    except:
        con.rollback()
        return False

def update_user(email, password):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""UPDATE users SET password_hash = ? WHERE email = ?""",(password, email) )
            con.commit()
        return True
    except:
        con.rollback()
        return False
