import sqlite3

def fetch_new_segment():
    with sqlite3.connect("transcriptions.db") as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM segments WHERE complete = 0 AND checkout = 0 LIMIT 1""")
        rows = cur.fetchall()
        filename = rows[0][0]
        id = rows[0][5]
        #cur.execute("""UPDATE segments SET checkout = 1 WHERE id = ?""", (id,))
        return filename, id

def record_transcription(transcription, row_num):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (segment_id, transcription) VALUES (?,?)""",(row_num, transcription) )
            cur.execute("""UPDATE segments SET complete = 0 WHERE id = ? """, (row_num,))  ## Set complete to 1 when ready to start up again
            con.commit()
        return "Record successfully added"
    except:
        con.rollback()
        return "Error in insert operation"

def record_user_strokes(id_plus_coords):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_stroke_coordinates (x1_coord, y1_coord, x2_coord, y2_coord, segment_id) VALUES (?,?,?,?,?)""",(id_plus_coords) )
            con.commit()
        return "User-provided stroke segments added to database."
    except:
        con.rollback()
        return "Error in insert operation"
