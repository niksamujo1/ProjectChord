
from flask import Flask, render_template, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
from chord_detector import analyze_song

app = Flask(__name__)
app.config["SECRET_KEY"] = "123456"
app.config["UPLOAD_FOLDER"] = "audio"
ALLOWED_EXTENSIONS = {"wav"}

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload file")

@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    timeline = None
    form = UploadFileForm()
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
            
            uploaded_file.save(filepath)
            
            timeline = analyze_song(filepath)
            
            
    return render_template(
        "index.html", 
        form=form,
        timeline=timeline
    )
    
    
    
# -------------------------- HELPER -------------------------------

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)