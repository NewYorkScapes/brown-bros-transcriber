from mysql.connector import connect
from settings import CONFIG
import io
import csv
from random import random


def fetch_new_segment():
    try:
        with connect(**CONFIG) as con:
            cur = con.cursor()
            cur.execute("""SELECT * FROM segments WHERE match_reached = 0 AND number_passes < 4""")
            rows = cur.fetchall()
            random_row = int(random()*len(rows))
            if len(rows) > 0:
                return rows[random_row][0], rows[random_row][5], rows[random_row][11]
            return False
    except:
        return False
    finally:
        cur.close()
        con.close()


def test_match(transcription, row_num):
    try:
        with connect(**CONFIG) as con:
            cur = con.cursor()
            cur.execute("""SELECT transcription FROM transcriptions WHERE segment_id = %s""", (row_num,))
            rows = cur.fetchall()
            match_exists = False
            if len(rows) > 0:
                for row in rows:
                    if row[0] == transcription:
                        match_exists = True
            return match_exists
    except:
        return False
    finally:
        cur.close()
        con.close()

def record_transcription(transcription, if_illegible, if_blank, row_num, user_transcriber, set_done):
    try:
        with connect(**CONFIG) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO transcriptions (segment_id,
                          transcription, user_transcriber,
                          marked_illegible, marked_blank) VALUES (%s,%s,%s,%s,%s)""",(row_num, transcription, user_transcriber, if_illegible, if_blank) )
            con.commit()
            #Set this back to number_passes + 1 when ready to go to production
            if set_done:
                cur.execute("""UPDATE segments SET number_passes = number_passes + 1, match_reached = 1 WHERE segment_id = %s""", (row_num,) )
            else:
                cur.execute("""UPDATE segments SET number_passes = number_passes + 1 WHERE segment_id = %s""", (row_num,) )
            con.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        con.close()


def record_user_strokes(id_plus_coords):
    try:
        with connect(**CONFIG) as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO user_stroke_coordinates (x1_coord, y1_coord, x2_coord, y2_coord, segment_id, user_transcriber) VALUES (%s,%s,%s,%s,%s,%s)""",(id_plus_coords) )
            con.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        con.close()


def make_report():
    try:
        with connect(**CONFIG) as con:
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
        cur.close()
        con.close()


def make_transcriptions_csv():
    try:
        with connect(**CONFIG) as con:
            cur = con.cursor()
            cur.execute("""SELECT group_concat(COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'segments'""", (CONFIG['database'],))
            seg_cols = cur.fetchall()
            seg_cols = [i for i in list(seg_cols[0])[0].split(',')]
            cur.execute("""SELECT group_concat(COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'transcriptions'""", (CONFIG['database'],))
            transcriptions_cols = cur.fetchall()
            transcriptions_cols = [i for i in list(transcriptions_cols[0])[0].split(',')]
            cur.execute("""SELECT group_concat(COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'user_stroke_coordinates'""", (CONFIG['database'],))
            stroke_cols = cur.fetchall()
            stroke_cols = [i for i in list(stroke_cols[0])[0].split(',')]
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
        cur.close()
        con.close()
