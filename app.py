
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
from chord_detector import analyze_song
import threading
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from datetime import datetime
import numpy as np
from formatChange import convert_to_wav 


app = Flask(__name__)
app.config["SECRET_KEY"] = "123456"
app.config["UPLOAD_FOLDER"] = "audio"
ALLOWED_EXTENSIONS = {"wav", "mp3"}

SAMPLE_RATE = 44100
recording_data = {"frames": [], "stream": None, "filepath": None}


class UploadFileForm(FlaskForm):
    file = FileField("File")
    submit = SubmitField("Upload file")
    
    


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    timeline = None
    form = UploadFileForm()
    uploaded_filename = None
    
    
    # Snimljeni fajl (bez file uploada)
    recorded_filename = request.form.get("recorded_filename")
    if recorded_filename and request.method == "POST":
        filepath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            app.config["UPLOAD_FOLDER"],
            secure_filename(recorded_filename)
        )
        if os.path.exists(filepath):
            uploaded_filename = recorded_filename
            timeline = analyze_song(filepath)
            os.remove(filepath)
            return render_template("index.html", form=form,
                                   timeline=timeline,
                                   uploaded_filename=uploaded_filename)



    if form.validate_on_submit():
        uploaded_file = form.file.data
        if uploaded_file and uploaded_file.filename:
            
            if not allowed_file(uploaded_file.filename):
                return "Only WAV files are allowed"
            
            filepath = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                app.config["UPLOAD_FOLDER"],
                secure_filename(uploaded_file.filename),
            )
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(filepath)
            uploaded_filename = filename
            
            # konvertiraj mp3 u wav ako treba
            if filename.rsplit(".", 1)[1].lower() == "mp3":
                filepath = convert_to_wav(filepath)
                uploaded_filename = os.path.basename(filepath)  # koristi wav ime za player

            timeline = analyze_song(filepath)
            os.remove(filepath)
            
            
    return render_template(
        "index.html", 
        form=form,
        timeline=timeline,
        uploaded_filename=uploaded_filename 
    )
    
# -------------------------- PREVIEW ------------------------------
@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config["UPLOAD_FOLDER"]),
        filename
    )
    
    
    
# ------------------------- RECORDING --------------------------------

@app.route("/record/start", methods=["POST"])
def record_start():
    recording_data["frames"] = []

    def callback(indata, frames, time, status):
        recording_data["frames"].append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback)
    stream.start()
    recording_data["stream"] = stream
    return jsonify({"status": "recording"})

@app.route("/record/stop", methods=["POST"])
def record_stop():
    stream = recording_data.get("stream")
    if not stream:
        return jsonify({"error": "No active recording"}), 400

    stream.stop()
    stream.close()
    recording_data["stream"] = None

    audio = np.concatenate(recording_data["frames"], axis=0)
    filename = datetime.now().strftime("recording_%Y%m%d_%H%M%S.wav")
    filepath = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        app.config["UPLOAD_FOLDER"],
        filename
    )
    wav_write(filepath, SAMPLE_RATE, audio)
    recording_data["filepath"] = filepath
    return jsonify({"status": "done", "filename": filename})



# -------------------------- HELPER -------------------------------

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)