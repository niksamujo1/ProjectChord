from pydub import AudioSegment
import os

def convert_to_wav(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".wav":
        return filepath 
    
    audio = AudioSegment.from_file(filepath)
    wav_filepath = os.path.splitext(filepath)[0] + ".wav"
    audio.export(wav_filepath, format="wav")
    return wav_filepath