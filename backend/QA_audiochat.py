import os
import subprocess
from transformers import pipeline  # For BioBERT model
from gtts import gTTS  # For text-to-speech
import speech_recognition as sr  # For transcription
from flask import Flask, request, jsonify, send_file, url_for
from flask_cors import CORS
import uuid
import pytesseract  # For OCR
from PIL import Image  # For image processing
import logging  # For logging
import base64
import cv2
import re


# Configuration
BIOBERT_MODEL_PATH = "dmis-lab/biobert-large-cased-v1.1-squad"
context_file = "contexts/medinfo.txt"
cards_file = "cards.txt"  # File to save summarized information

app = Flask(__name__)
CORS(app)  # Enable CORS to allow cross-origin requests

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize BioBERT pipeline
qa_pipeline = pipeline("question-answering", model=BIOBERT_MODEL_PATH)

# Utility functions
def load_context_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def save_context_to_file(text, file_path):
    with open(file_path, 'a') as file:  # 'a' mode to append text
        file.write("\n" + text + "\n")

def save_summary_to_cards_file(summary, file_path):
    """Overwrite and save summarized data to cards.txt."""
    with open(file_path, 'w') as file:  # 'w' mode to overwrite the file each time
        file.write(f"Medication, {summary['med_name']}\n")
        file.write(f"Disease Treated, {summary['disease']}\n")
        file.write(f"How Often to Take, {summary['how_often']}\n")
        file.write(f"How to Take, {summary['how_to_take']}\n")
        file.write(f"Side Effects, {summary['side_effects']}\n")
        file.write("\n-------------------------\n")

# Audio-related functionality
def convert_m4a_to_wav(m4a_file, wav_file):
    command = f'ffmpeg -y -i "{m4a_file}" -ar 16000 -ac 1 "{wav_file}"'
    subprocess.call(command, shell=True)

def amplify_audio(input_file, output_file, target):
    print("Amplifying audio: ", input_file, output_file, target)
    command = f'ffmpeg -i "{input_file}" -filter:a "volume={target}dB" "{output_file}"'
    subprocess.call(command, shell=True)

def text_to_speech(text, file_name="response.wav"):
    tts = gTTS(text)
    tts.save(file_name)
    amplified_file_name = "amplified_" + file_name
    amplify_audio(file_name, amplified_file_name, 75) 

    return amplified_file_name

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

# OCR-related functionality
def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_image_path = 'preprocessed_image.png'
    cv2.imwrite(preprocessed_image_path, thresh)
    return preprocessed_image_path

def ocr_tesseract(image_path):
    logging.info(f"Starting OCR processing for {image_path}")
    try:
        preprocessed_image_path = preprocess_image(image_path)
        image = Image.open(preprocessed_image_path)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config, lang='eng')
        logging.info("Completed OCR processing")
        return text
    except Exception as e:
        logging.error(f"Error during OCR processing: {e}")
        return None

# Text formatting
def format_text(text):
    text = clean_unnecessary_characters(text)
    text = text.strip()
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    formatted_text = "\n\n".join(paragraphs)
    formatted_text = " ".join(formatted_text.split())
    return formatted_text

def clean_unnecessary_characters(text):
    text = re.sub(r'[^A-Za-z0-9.,!?\'"\s]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

# BioBERT summarization
def summarize_medical_info(text):
    """Summarizes medical information using BioBERT."""
    summary = {}
    questions = {
        "med_name": "What is the medication?",
        "disease": "What disease or symptoms does this medication treat?",
        "how_often": "How often should the medication be taken?",
        "how_to_take": "How do you take the medicine?",
        "side_effects": "What are the side effects of the medication?"
    }
    for key, question in questions.items():
        logging.info(f"Asking BioBERT: {question}")
        answer = qa_pipeline(question=question, context=text)
        logging.info(f"BioBERT answer: {answer['answer']}")
        summary[key] = answer['answer']
    return summary

# Image processing and cards update endpoint
@app.route('/process_image', methods=['POST'])
def process_image():
    logging.info("Processing image for OCR...")
    data = request.get_json()
    base64_image = data['base64']
    image_name = "med_image.png"
    with open(image_name, "wb") as med_image:
        med_image.write(base64.decodebytes(bytes(base64_image, "utf-8")))

    ocr_text = ocr_tesseract(image_name)
    if ocr_text is None:
        return jsonify({'error': 'OCR processing failed'}), 500

    cleaned_text = format_text(ocr_text)
    save_context_to_file(cleaned_text, context_file)

    logging.info("OCR text appended to medinfo.txt")

    # BioBERT summarization
    summary = summarize_medical_info(cleaned_text)
    save_summary_to_cards_file(summary, cards_file)

    logging.info(f"Summary added to {cards_file}")

    return jsonify({'message': 'OCR processing successful and summary added to cards.txt', 'summary': summary}), 200

# Audio processing endpoint
@app.route('/process_audio', methods=['POST'])
def process_audio():
    print("Processing audio...")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    unique_id = str(uuid.uuid4())
    m4a_filename = f"uploaded_{unique_id}.m4a"
    wav_filename = f"converted_{unique_id}.wav"
    response_wav = f"response_{unique_id}.wav"
    audio_file.save(m4a_filename)

    print("Converting M4A to WAV...")
    convert_m4a_to_wav(m4a_filename, wav_filename)

    print("Transcribing audio...")
    transcribed_text = transcribe_audio(wav_filename)
    if transcribed_text is None:
        os.remove(m4a_filename)
        os.remove(wav_filename)
        return jsonify({'error': 'Transcription failed'}), 500

    context = load_context_from_file(context_file)

    print("Processing with BioBERT...")
    question = transcribed_text
    answer = qa_pipeline(question=question, context=context)
    answer_text = answer['answer']
    print(f"Answer: {answer_text}")

    print("Converting answer to speech...")
    amplified = text_to_speech(answer_text, response_wav)

    response = {
        'text_response': answer_text,
        'audio_response_url': url_for('get_audio', filename=amplified, _external=True)
    }

    os.remove(m4a_filename)
    os.remove(wav_filename)

    return jsonify(response)

# Endpoint to serve the audio response file
@app.route('/get_audio/<filename>', methods=['GET'])
def get_audio(filename):
    return send_file(filename, mimetype='audio/mpeg')

# Endpoint to retrieve cards data
@app.route('/cards', methods=['GET'])
def get_cards():
    cards = []
    try:
        with open(cards_file, 'r') as file:
            for line in file:
                if ',' in line:
                    title, content = line.split(',', 1)
                    cards.append({'title': title.strip(), 'content': content.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(cards)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
