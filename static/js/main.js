const input       = document.getElementById('fileInput');
const label       = document.getElementById('fileName');
const zone        = document.getElementById('dropZone');
const playerWrap  = document.getElementById('playerWrap');
const audioPlayer = document.getElementById('audioPlayer');
const playerLabel = document.getElementById('playerLabel');

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

let transposeSteps = 0;

function hideResults() {
    const results = document.querySelector('.results');
    if (results) results.style.display = 'none';
}

function loadPreview(file) {
    if (!file) return;

    const recordedFilenameInput = document.getElementById("recordedFilename");
    if(recordedFilenameInput) recordedFilenameInput.value = "";

    label.textContent = file.name;
    playerLabel.textContent = '♪ ' + file.name;
    audioPlayer.src = URL.createObjectURL(file);
    audioPlayer.load();
    playerWrap.style.display = 'block';
    hideResults(); 
}

input.addEventListener('change', () => loadPreview(input.files[0]));

zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('over'); });
zone.addEventListener('dragleave', () => zone.classList.remove('over'));
zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('over');
    if (e.dataTransfer.files.length) {
    input.files = e.dataTransfer.files;
    loadPreview(input.files[0]);
    }
});
// ── Recording ──────────────────────────────────────────────



let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

const recBtn = document.getElementById("recBtn");
const recBtnText = document.getElementById("recBtnText");
const recStatus = document.getElementById("recStatus");

if (recBtn) {
  recBtn.addEventListener("click", async () => {
    if (!isRecording) {
      await startBrowserRecording();
    } else {
      stopBrowserRecording();
    }
  });
}

async function startBrowserRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
            channelCount: 1,
            sampleRate: 44100
        }
    });

  audioChunks = [];
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      audioChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    recStatus.textContent = "Saving recording...";

    const response = await fetch("/record/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (data.error) {
        recStatus.textContent = data.error;
        return;
    }

    const recordedFilenameInput = document.getElementById("recordedFilename");
    recordedFilenameInput.value = data.filename;

    const playerWrap = document.getElementById("playerWrap");
    const audioPlayer = document.getElementById("audioPlayer");
    const playerLabel = document.getElementById("playerLabel");

    playerWrap.style.display = "block";
    playerLabel.textContent = "♫ " + data.filename;

    audioPlayer.innerHTML = "";
    const source = document.createElement("source");
    source.src = data.audio_url;
    source.type = "audio/wav";
    audioPlayer.appendChild(source);
    audioPlayer.load();

    recStatus.textContent = "";
    };

  mediaRecorder.start();
  isRecording = true;

  recBtnText.textContent = "■ Stop Recording";
  recStatus.textContent = "Recording...";
}

function stopBrowserRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;

    mediaRecorder.stream.getTracks().forEach(track => track.stop());

    recBtnText.textContent = "● Start Recording";
    recStatus.textContent = "Processing...";
  }
}
// const recBtn      = document.getElementById('recBtn');
// const recBtnText  = document.getElementById('recBtnText');
// const recStatus   = document.getElementById('recStatus');
// const recTimer    = document.getElementById('recTimer');
// const recTimerVal = document.getElementById('recTimerVal');

// let isRecording = false;
// let timerInterval = null;
// let seconds = 0;

// function formatTime(s) {
//     const m = Math.floor(s / 60);
//     const ss = String(s % 60).padStart(2, '0');
//     return `${m}:${ss}`;
// }

// recBtn.addEventListener('click', async () => {
//     if (!isRecording) {
//     // START
//     recBtn.disabled = true;
//     recStatus.textContent = 'Starting...';
//     try {
//         const res = await fetch('/record/start', { method: 'POST' });
//         const data = await res.json();
//         if (data.status === 'recording') {
//         isRecording = true;
//         recBtnText.textContent = '⏹ Stop Recording';
//         recBtn.style.background = '#e05555';
//         recBtn.style.color = '#fff';
//         recStatus.textContent = '';
//         recTimer.style.display = 'block';
//         seconds = 0;
//         recTimerVal.textContent = formatTime(seconds);
//         timerInterval = setInterval(() => {
//             seconds++;
//             recTimerVal.textContent = formatTime(seconds);
//         }, 1000);
//         }
//     } catch(e) {
//         recStatus.textContent = 'Error starting recording.';
//     }
//     recBtn.disabled = false;
//     } else {
//     // STOP
//     recBtn.disabled = true;
//     recStatus.textContent = 'Saving...';
//     clearInterval(timerInterval);
//     recTimer.style.display = 'none';
//     try {
//         const res = await fetch('/record/stop', { method: 'POST' });
//         const data = await res.json();
//         if (data.filename) {
//         isRecording = false;
//         recBtnText.textContent = '● Start Recording';
//         recBtn.style.background = 'var(--border)';
//         recBtn.style.color = 'var(--text)';
//         recStatus.textContent = `Saved: ${data.filename}`;

//         // load into player
//         playerLabel.textContent = '♪ ' + data.filename;
//         audioPlayer.src = `/audio/${data.filename}`;
//         audioPlayer.load();
//         playerWrap.style.display = 'block';
//         hideResults();

//         // set hidden file input so form can submit it
//         label.textContent = data.filename;

//         // store filename for form submission
//         recBtn.dataset.lastFile = data.filename;

//         // inject hidden field so Flask knows which recorded file to analyze
//         let hiddenRec = document.getElementById('recordedFilename');
//         if (!hiddenRec) {
//             hiddenRec = document.createElement('input');
//             hiddenRec.type = 'hidden';
//             hiddenRec.id = 'recordedFilename';
//             hiddenRec.name = 'recorded_filename';
//             document.querySelector('form').appendChild(hiddenRec);
//         }
//         hiddenRec.value = data.filename;
//         }
//     } catch(e) {
//         recStatus.textContent = 'Error saving recording.';
//     }
//     recBtn.disabled = false;
//     }
// });
// ── Live chord mode ─────────────────────────────────────────
const toggleBtn = document.getElementById('toggleMode');
const liveBox   = document.getElementById('liveBox');
const tableBox  = document.getElementById('tableBox');
const liveChord = document.getElementById('liveChord');



let liveMode = false;
let liveInterval = null;

if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
    liveMode = !liveMode;
    if (liveMode) {
        tableBox.style.display = 'none';
        liveBox.style.display = 'block';
        toggleBtn.textContent = '≡ Table';
        toggleBtn.style.color = 'var(--accent)';
        toggleBtn.style.borderColor = 'var(--accent)';
        startLiveTracking();
    } else {
        tableBox.style.display = 'block';
        liveBox.style.display = 'none';
        toggleBtn.textContent = '⬡ Live';
        toggleBtn.style.color = 'var(--muted)';
        toggleBtn.style.borderColor = 'var(--border)';
        stopLiveTracking();
    }
    });
}

function getCurrentChord(time) {
    const filtered = chordTimeline.filter(i => i.chord && i.chord.toLowerCase() !== 'none');
    for (const item of filtered) {
    if (time >= item.start && time < item.end) return item.chord;
    }
    return null;
}

function startLiveTracking() {
    liveInterval = setInterval(() => {
    if (!audioPlayer || audioPlayer.paused) return;
    const t = audioPlayer.currentTime;
    const chord = getCurrentChord(t);
    const display = chord || '—';
    if (liveChord.textContent !== display) {
        liveChord.style.opacity = '0';
        setTimeout(() => {
        liveChord.textContent = display;
        liveChord.style.opacity = '1';
        }, 80);
    }
    }, 100);
}

function stopLiveTracking() {
    clearInterval(liveInterval);
    liveInterval = null;
    if (liveChord) liveChord.textContent = '—';
}

// reset live display when audio ends
if (audioPlayer) {
    audioPlayer.addEventListener('ended', () => {
    if (liveChord) liveChord.textContent = '—';
    });
    audioPlayer.addEventListener('seeked', () => {
    if (!liveMode) return;
    const chord = getCurrentChord(audioPlayer.currentTime);
    if (liveChord) liveChord.textContent = chord || '—';
    });
}

// transpose 

function transposeChord(chord, steps) {
  if (!chord || chord === "None") return chord;

  const parts = chord.split("_");
  const root = parts[0];
  const type = parts[1];

  const index = NOTE_NAMES.indexOf(root);
  if (index === -1) return chord;

  const newIndex = (index + steps + 12) % 12;
  return `${NOTE_NAMES[newIndex]}_${type}`;
}

function updateDisplayedChords() {
  const rows = document.querySelectorAll(".chord-row");

  rows.forEach((row, index) => {
    const chordSpan = row.querySelector(".chord-name");
    const originalChord = chordTimeline[index].chord;

    chordSpan.textContent = transposeChord(originalChord, transposeSteps);
  });

  const liveChord = document.getElementById("liveChord");
  if (liveChord && liveChord.textContent !== "—") {
    liveChord.textContent = transposeChord(liveChord.dataset.originalChord, transposeSteps);
  }

  document.getElementById("transposeValue").textContent =
    transposeSteps > 0 ? `+${transposeSteps}` : transposeSteps;
}

document.getElementById("transposeUp")?.addEventListener("click", () => {
    if(transposeSteps < 12){
        transposeSteps += 1;
        updateDisplayedChords();

    }
});

document.getElementById("transposeDown")?.addEventListener("click", () => {
    if(transposeSteps > -12){
        transposeSteps -= 1;
        updateDisplayedChords();

    }
});