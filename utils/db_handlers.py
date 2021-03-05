import sqlite3

def fetch_new_segment():
    with sqlite3.connect("transcriptions.db") as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM segments WHERE complete = 0 LIMIT 1""")
        rows = cur.fetchall()
        return rows[0][0], rows[0][5]

def record_transcription(transcription, row_num):
    try:
        with sqlite3.connect("transcriptions.db") as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (transcription) VALUES (?)""",(transcription,) )
            cur.execute("""UPDATE segments SET complete = 1 where id = ? """, (row_num,))
            con.commit()
        return "Record successfully added"
    except:
        con.rollback()
        return "Error in insert operation"
