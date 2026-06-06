import sys
import json
from collections import Counter

import numpy as np
import scipy.io.wavfile as wav


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

WINDOW_DURATION = 0.15        # 150 ms
OVERLAP = 0.5                 # 50 %
SILENCE_THRESHOLD_RATIO = 0.03
MIN_CHORD_DURATION = 0.5      # seconds


def load_audio(filepath):
    sample_rate, signal = wav.read(filepath)

    if len(signal.shape) > 1:
        signal = signal.mean(axis=1)

    signal = signal.astype(float)
    return sample_rate, signal


def create_chord_templates():
    templates = {}

    for i, note in enumerate(NOTE_NAMES):
        major = np.zeros(12)
        major[i] = 1.0
        major[(i + 4) % 12] = 0.8
        major[(i + 7) % 12] = 0.8
        templates[f"{note}_DUR"] = major

        minor = np.zeros(12)
        minor[i] = 1.0
        minor[(i + 3) % 12] = 0.8
        minor[(i + 7) % 12] = 0.8
        templates[f"{note}_MOL"] = minor

    return templates


def split_into_segments(signal, window_size, hop_size):
    segments = []

    for start in range(0, len(signal) - window_size, hop_size):
        segment = signal[start:start + window_size]
        segments.append(segment)

    return segments


def cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0

    return np.dot(a, b) / denominator


def calculate_chroma(segment, sample_rate):
    window = np.hanning(len(segment))
    windowed_segment = segment * window

    fft_values = np.fft.rfft(windowed_segment)
    fft_magnitude = np.abs(fft_values)
    freqs = np.fft.rfftfreq(len(windowed_segment), d=1 / sample_rate)

    chroma = np.zeros(12)

    for frequency, magnitude in zip(freqs, fft_magnitude):
        if frequency < 20:
            continue

        midi = 69 + 12 * np.log2(frequency / 440.0)
        chroma_bin = int(round(midi)) % 12
        chroma[chroma_bin] += magnitude

    if np.sum(chroma) > 0:
        chroma = chroma / np.sum(chroma)

    return chroma


def detect_chord(chroma, templates):
    best_chord = None
    best_score = -1

    for chord_name, template in templates.items():
        score = cosine_similarity(chroma, template)

        if score > best_score:
            best_score = score
            best_chord = chord_name

    return best_chord


def smooth_chords(detected_chords, window_radius=2):
    smoothed = []

    for i in range(len(detected_chords)):
        start = max(0, i - window_radius)
        end = min(len(detected_chords), i + window_radius + 1)

        neighborhood = detected_chords[start:end]
        most_common = Counter(neighborhood).most_common(1)[0][0]
        smoothed.append(most_common)

    return smoothed


def remove_short_chords(chords, min_length):
    filtered = chords.copy()
    i = 0

    while i < len(filtered):
        current = filtered[i]
        start = i

        while i < len(filtered) and filtered[i] == current:
            i += 1

        length = i - start

        if length < min_length:
            if start > 0:
                replacement = filtered[start - 1]
            elif i < len(filtered):
                replacement = filtered[i]
            else:
                continue

            for j in range(start, i):
                filtered[j] = replacement

    return filtered


def create_timeline(chords, hop_size, sample_rate):
    timeline = []

    if not chords:
        return timeline

    current_chord = chords[0]
    start_idx = 0

    for i in range(1, len(chords)):
        if chords[i] != current_chord:
            start_time = start_idx * hop_size / sample_rate
            end_time = i * hop_size / sample_rate

            if current_chord is not None:
                timeline.append({
                    "start": round(start_time, 3),
                    "end": round(end_time, 3),
                    "chord": current_chord
                })

            current_chord = chords[i]
            start_idx = i

    start_time = start_idx * hop_size / sample_rate
    end_time = len(chords) * hop_size / sample_rate

    if current_chord is not None:
        timeline.append({
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "chord": current_chord
        })

    return timeline


def analyze_song(filepath):
    sample_rate, signal = load_audio(filepath)
    templates = create_chord_templates()

    window_size = int(WINDOW_DURATION * sample_rate)
    hop_size = int(window_size * (1 - OVERLAP))

    silence_threshold = SILENCE_THRESHOLD_RATIO * np.max(np.abs(signal))
    min_chord_length = int(MIN_CHORD_DURATION / (hop_size / sample_rate))

    segments = split_into_segments(signal, window_size, hop_size)

    detected_chords = []

    for segment in segments:
        energy = np.mean(np.abs(segment))

        if energy < silence_threshold:
            detected_chords.append(None)
            continue

        chroma = calculate_chroma(segment, sample_rate)
        chord = detect_chord(chroma, templates)
        detected_chords.append(chord)

    smoothed_chords = smooth_chords(detected_chords)
    filtered_chords = remove_short_chords(smoothed_chords, min_chord_length)

    return create_timeline(filtered_chords, hop_size, sample_rate)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Upotreba: python3 chord_detector.py pjesma.wav")
        sys.exit(1)

    result = analyze_song(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))