import os
import tempfile
from flask import Flask, request, jsonify, redirect, url_for, session, render_template
import speech_recognition as sr
from pydub import AudioSegment
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

#chat bot code! (based on commonly asked keywords)
@app.route('/api/ask_bot', methods=['POST'])
def ask_bot():
    user_msg = request.json.get('message', '').lower()

    #rule-based simple and straight-forward chat bot as last resort
    if any(word in user_msg for word in ['score', 'percent', 'result']):
        reply = (
            "Your Alzheimer's score estimates potential symptoms based on speech errors. "
            "Lower percentages are better. Would you like tips to improve your speech?"
        )
    elif any(word in user_msg for word in ['symptom', 'sign', 'warning']):
        reply = (
            "Common Alzheimer's symptoms include memory loss, difficulty finding words, "
            "repeating phrases, and trouble organizing thoughts. "
            "Ask me about how your speech test measures these."
        )
    elif ('how' in user_msg and any(word in user_msg for word in ['measure', 'analyze', 'detect', 'work', 'working'])) or 'how does the test' in user_msg:
        reply = (
            "The speech test analyzes your recording for things like missing or repeated words, "
            "filler words like 'um', and changes in sentence structure. These signs are often linked "
            "to early Alzheimer's symptoms."
        )
    elif any(word in user_msg for word in ['improve', 'tips', 'practice', 'better']):
        reply = (
            "To improve your speech clarity, try slowing down, avoid repeating words, and practice the test sentence. "
            "Would you like some exercises?"
        )
    elif any(word in user_msg for word in ['exercise', 'resources', 'help']):
        reply = (
            "Sure! You can visit the Alzheimer's Association website or practice with speech exercises focusing "
            "on clarity and fluency."
        )
    elif any(word in user_msg for word in ['thank', 'thanks']):
        reply = "You're welcome! Let me know if you have any other questions."
    elif any(word in user_msg for word in ['bye', 'goodbye', 'see you']):
        reply = "Goodbye! Take care and keep practicing your speech."
    elif any(word in user_msg for word in ['yes', 'okay', 'sure']):
        reply = "Great! What would you like help with next?"
    else:
        reply = (
            "I'm your assistant bot! You can ask about your Alzheimer's score, symptoms, how to improve or how the test works. "
        )

    return jsonify({'reply': reply})

#actual versus transcripted text comparison for metrics like missing words
EXPECTED_PROMPT = "The quick brown fox jumps over the lazy dog"

def calculate_alzheimers_chance(expected, actual):
    expected_words = expected.lower().split()
    actual_words = actual.lower().split()

    missing_words = [w for w in expected_words if w not in actual_words]
    extra_words = [w for w in actual_words if w not in expected_words]

    repeated_words = []
    for i in range(1, len(actual_words)):
        if actual_words[i] == actual_words[i-1]:
            repeated_words.append(actual_words[i])
    repeated_words = list(set(repeated_words))

    substitutions = sum(1 for ew, aw in zip(expected_words, actual_words) if ew != aw)

    missing_penalty = len(missing_words) * 4
    extra_penalty = len(extra_words) * 2
    repeated_penalty = len(repeated_words) * 5
    substitution_penalty = substitutions * 4

    error_score = missing_penalty + extra_penalty + repeated_penalty + substitution_penalty

    max_possible_errors = len(expected_words) * 10
    alzheimers_percent = min(100, int((error_score / max_possible_errors) * 100))

    return alzheimers_percent, missing_words, extra_words, repeated_words, substitutions

#app routing for logging in!
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/')
def home():
    return redirect(url_for('login'))

#dashboard app routing :)
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session.get('username', 'User')
    return render_template('dashboard.html', username=username)

@app.route('/resources')
def resources():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('resources.html')

#audio recording and processing code
@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    temp_filename = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            temp_filename = tmp.name
            audio_file.save(temp_filename)

        sound = AudioSegment.from_file(temp_filename)
        wav_path = temp_filename + '.wav'
        sound.export(wav_path, format='wav')

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio)

        alzheimers_percent, missing_words, extra_words, repeated_words, substitutions = calculate_alzheimers_chance(EXPECTED_PROMPT, transcription)

        result = {
            'transcription': transcription,
            'word_count': len(transcription.split()),
            'missing_words': missing_words,
            'extra_words': extra_words,
            'repeated_words': repeated_words,
            'substitutions': substitutions,
            'alzheimers_percent': alzheimers_percent
        }

        return jsonify(result)

    #alternate option
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Speech recognition service error: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#allows app to run
if __name__ == '__main__':
    app.run(debug=True)
