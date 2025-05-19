let recorder;
let audioChunks = [];

const recordButton = document.getElementById('recordButton');
const stopButton = document.getElementById('stopButton');
const reRecordButton = document.getElementById('reRecordButton');
const status = document.getElementById('status');
const results = document.getElementById('results');

recordButton.onclick = async () => {
    if (!navigator.mediaDevices) {
        alert('Your browser does not support audio recording.');
        return;
    }

    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);

    recorder.ondataavailable = e => {
        audioChunks.push(e.data);
    };

    recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        const formData = new FormData();
        formData.append('audio', audioBlob, 'speech.wav');

        status.textContent = 'Analyzing audio... Please wait.';
        results.innerHTML = '';

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            if (data.error) {
                status.textContent = 'Error: ' + data.error;
            } else {
                status.textContent = 'Analysis complete.';
                results.innerHTML = `
                    <p><b>Transcription:</b> ${data.transcription}</p>
                    <p><b>Word count:</b> ${data.word_count}</p>
                    <p><b>Missing words:</b> ${data.missing_words.join(', ') || 'None'}</p>
                    <p><b>Extra words:</b> ${data.extra_words.join(', ') || 'None'}</p>
                    <p><b>Repeated words:</b> ${data.repeated_words.join(', ') || 'None'}</p>
                    <p><b>Substitutions:</b> ${data.substitutions}</p>
                    <p><b>Alzheimer's Risk Estimate:</b> ${data.alzheimers_percent}%</p>
                `;
            }
        } else {
            status.textContent = 'Failed to analyze audio.';
        }

        reRecordButton.style.display = 'inline-block';
        recordButton.disabled = false;
        stopButton.disabled = true;
    };

    recorder.start();
    status.textContent = 'Recording...';
    recordButton.disabled = true;
    stopButton.disabled = false;
};

stopButton.onclick = () => {
    recorder.stop();
    status.textContent = 'Stopping recording...';
    recordButton.disabled = false;
    stopButton.disabled = true;
};

reRecordButton.onclick = () => {
    results.innerHTML = '';
    status.textContent = '';
    reRecordButton.style.display = 'none';
};
