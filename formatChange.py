from pydub import AudioSegment
import numpy as np

audio = AudioSegment.from_wav("Mostovi.wav")

audio = audio + 5


audio = audio.fade_in(2000).fade_out(2000)

audio.export("Mostovi_modified.mp3", format="mp3")

audio2 = AudioSegment.from_mp3("Mostovi_modified.mp3")

print("Done")

