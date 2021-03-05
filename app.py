from flask import Flask, render_template, request, session
import os
from utils.db_handlers import fetch_new_segment, record_transcription

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
    return render_template("thanks.html", msg=msg)
    con.close()


if __name__ == '__main__':
    app.run(debug = True)
