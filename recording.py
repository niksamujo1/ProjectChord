import sounddevice as sd
from scipy.io.wavfile import write
import os
from datetime import datetime

# Postavke
SAMPLE_RATE = 44100  # Hz
DURATION = 5  # sekundi (promijeni po želji)

# Kreiraj ./audio folder ako ne postoji
output_dir = "./audio"
os.makedirs(output_dir, exist_ok=True)

# Generiraj ime file-a s timestampom
filename = datetime.now().strftime("recording_%Y%m%d_%H%M%S.wav")
filepath = os.path.join(output_dir, filename)

print("Snimanje počinje...")
recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
sd.wait()
print("Snimanje završeno.")

# Spremi kao WAV
write(filepath, SAMPLE_RATE, recording)

print(f"Audio spremljen u: {filepath}")