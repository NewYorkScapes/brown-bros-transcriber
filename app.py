from flask import Flask, render_template, request, session
import os
from utils.db_handlers import fetch_new_segment, record_transcription, record_user_strokes

app = Flask(__name__)
app.secret_key = "secret key"

SEGMENT_DIR = os.path.join('static', 'segments')

@app.route('/')
def transcriber_home():
    segment_filename, session['current_row_id'] = fetch_new_segment()
    current_image = os.path.join(SEGMENT_DIR, segment_filename)
    return render_template('home.html', image_url = current_image)

@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
    msg = record_transcription(request.form['segment_transcription'], session.get('current_row_id', None))
    list_stroke_coords = request.form['segment_coords'].split('|')[:-1]
    if len(list_stroke_coords):
        for stroke_coords in list_stroke_coords:
            insert_row = tuple([int(i) for i in stroke_coords.split('-')]) + (session.get('current_row_id', None),)
            print(insert_row)
            stroke_coords_msg = record_user_strokes(insert_row)
    else:
        stroke_coords_msg = "No segments produced."
    return render_template("thanks.html", msg=msg + '. ' + stroke_coords_msg)
    con.close()


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug = True)
