import os
import subprocess
from transformers import pipeline  # For BioBERT model
from gtts import gTTS  # For text-to-speech
import speech_recognition as sr  # For transcription
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid

# Configuration
BIOBERT_MODEL_PATH = "dmis-lab/biobert-large-cased-v1.1-squad"
context_file = "contexts/medinfo.txt"

app = Flask(__name__)
CORS(app)  # Enable CORS to allow cross-origin requests

def load_context_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to convert M4A to WAV
def convert_m4a_to_wav(m4a_file, wav_file):
    # Use ffmpeg to convert M4A to WAV
    command = f'ffmpeg -y -i "{m4a_file}" -ar 16000 -ac 1 "{wav_file}"'
    subprocess.call(command, shell=True)

# Function for Text-to-Speech (TTS) using gTTS
def text_to_speech(text, file_name="response.mp3"):
    tts = gTTS(text)
    tts.save(file_name)

# Function to transcribe audio using SpeechRecognition
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            transcribed_text = recognizer.recognize_google(audio_data)
            print(f"Transcription: {transcribed_text}")
            return transcribed_text
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")
            return None

# Endpoint to process audio
@app.route('/process_audio', methods=['POST'])
def process_audio():
    print("hiiii")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded M4A audio file
    unique_id = str(uuid.uuid4())
    m4a_filename = f"uploaded_{unique_id}.m4a"
    wav_filename = f"converted_{unique_id}.wav"
    response_audio_filename = f"response_{unique_id}.mp3"

    audio_file.save(m4a_filename)

    # Convert M4A to WAV
    print("Converting M4A to WAV...")
    convert_m4a_to_wav(m4a_filename, wav_filename)

    # Transcribe the audio input using SpeechRecognition
    print("Transcribing audio...")
    transcribed_text = transcribe_audio(wav_filename)
    if transcribed_text is None:
        # Clean up files
        os.remove(m4a_filename)
        os.remove(wav_filename)
        return jsonify({'error': 'Transcription failed'}), 500

    # Load context from file
    context = load_context_from_file(context_file)

    # Load BioBERT pipeline for question-answering
    print("Processing with BioBERT...")
    qa_pipeline = pipeline("question-answering", model=BIOBERT_MODEL_PATH)

    # Ask BioBERT the question based on transcribed text
    question = transcribed_text
    answer = qa_pipeline(question=question, context=context)
    answer_text = answer['answer']
    print(f"Answer: {answer_text}")

    # Convert BioBERT's answer to speech
    print("Converting answer to speech...")
    text_to_speech(answer_text, response_audio_filename)

    # Return the text answer and URL to the audio response
    response = {
        'text_response': answer_text,
        'audio_response_url': f"/get_audio/{response_audio_filename}"
    }

    # Clean up uploaded and intermediate files
    os.remove(m4a_filename)
    os.remove(wav_filename)

    return jsonify(response)

# Endpoint to serve the audio response file
@app.route('/get_audio/<filename>', methods=['GET'])
def get_audio(filename):
    return send_file(filename, mimetype='audio/mpeg')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

