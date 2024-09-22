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

app = Flask(__name__)
CORS(app)  # Enable CORS to allow cross-origin requests

# Set up logging
logging.basicConfig(level=logging.INFO)

def load_context_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def save_context_to_file(text, file_path):
    with open(file_path, 'a') as file:  # 'a' mode to append text
        file.write("\n" + text)

# Function to convert M4A to WAV
def convert_m4a_to_wav(m4a_file, wav_file):
    # Use ffmpeg to convert M4A to WAV
    command = f'ffmpeg -y -i "{m4a_file}" -ar 16000 -ac 1 "{wav_file}"'
    subprocess.call(command, shell=True)

def amplify_audio(input_file, output_file, target):
    # Use ffmpeg to amplify the audio by a specific multiplier
    print("Amplifying audio: ", input_file, output_file, target)
    command = f'ffmpeg -i "{input_file}" -filter:a "volume={target}dB" "{output_file}"'
    subprocess.call(command, shell=True)

# Text-to-Speech function
def text_to_speech(text, file_name="response.wav"):
    tts = gTTS(text)
    tts.save(file_name)

    # Amplify the audio after generating it
    amplified_file_name = "amplified_" + file_name
    amplify_audio(file_name, amplified_file_name, 20) 

    return amplified_file_name

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


def preprocess_image(image_path):
    # Open the image using OpenCV
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply median blur to reduce noise
    gray = cv2.medianBlur(gray, 3)

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save the preprocessed image
    preprocessed_image_path = 'preprocessed_image.png'
    cv2.imwrite(preprocessed_image_path, thresh)

    return preprocessed_image_path

logging.basicConfig(level=logging.INFO)

def ocr_tesseract(image_path):
    logging.info(f"Starting OCR processing for {image_path}")
    try:
        # Preprocess the image
        preprocessed_image_path = preprocess_image(image_path)

        # Open the preprocessed image
        image = Image.open(preprocessed_image_path)

        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6'

        # Perform OCR
        text = pytesseract.image_to_string(image, config=custom_config, lang='eng')
        logging.info("Completed OCR processing")
        return text
    except Exception as e:
        logging.error(f"Error occurred during OCR processing: {e}")
        return None

# Endpoint to process image and update context
@app.route('/process_image', methods=['POST'])
def process_image():
    logging.info("Processing image for OCR...")
    data = request.get_json()
    print("Processing image for OCR")

    base64_image = data['base64']

    image_name = "med_image.png"
    with open(image_name, "wb") as med_image:
        med_image.write(base64.decodebytes(bytes(base64_image, "utf-8")))

    # Perform OCR
    ocr_text = ocr_tesseract(image_name)
    if ocr_text is None:
        return jsonify({'error': 'OCR processing failed'}), 500
    
    print("OCR text: ", ocr_text)

    # Clean up the OCR text to ensure a standard format
    cleaned_text = format_text(ocr_text)
    
    print("Cleaned OCR text: ", cleaned_text)

    # Append the cleaned OCR text to the context file
    save_context_to_file(cleaned_text, context_file)

    logging.info("OCR text appended to medinfo.txt")

    return jsonify({'message': 'OCR processing successful and text added to medinfo.txt'}), 200

def format_text(text):
    """Format and clean the OCR text to ensure readability."""
    # Remove unnecessary characters
    text = clean_unnecessary_characters(text)

    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple line breaks or empty lines with a single line break
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    
    # Join paragraphs with two newlines (to represent a paragraph break)
    formatted_text = "\n\n".join(paragraphs)
    
    # Ensure single spaces between sentences by collapsing any multiple spaces
    formatted_text = " ".join(formatted_text.split())
    
    return formatted_text

def clean_unnecessary_characters(text):
    """Clean up unnecessary characters like special symbols and extra punctuation."""
    # Remove non-alphabetic characters that aren't part of a sentence (like symbols and stray punctuation)
    # Use a regex to remove unwanted characters (except common punctuation marks like . , ! ?)
    text = re.sub(r'[^A-Za-z0-9.,!?\'"\s]+', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text

# Endpoint to process audio
@app.route('/process_audio', methods=['POST'])
def process_audio():
    print("Processing audio...")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded M4A audio file
    unique_id = str(uuid.uuid4())
    m4a_filename = f"uploaded_{unique_id}.m4a"
    wav_filename = f"converted_{unique_id}.wav"
    response_wav = f"response_{unique_id}.wav"

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
    amplified = text_to_speech(answer_text, response_wav)

    # Return the text answer and URL to the audio response
    response = {
        'text_response': answer_text,
        'audio_response_url': url_for('get_audio', filename=amplified, _external=True)
    }

    # Clean up uploaded and intermediate files
    os.remove(m4a_filename)
    os.remove(wav_filename)

    return jsonify(response)

# Endpoint to serve the audio response file
@app.route('/get_audio/<filename>', methods=['GET'])
def get_audio(filename):
    return send_file(filename, mimetype='audio/mpeg')

@app.route('/cards', methods=['GET'])
def get_cards():
    cards = []
    try:
        with open('cards.txt', 'r') as file:
            for line in file:
                if ',' in line:
                    title, content = line.split(',', 1)
                    cards.append({'title': title.strip(), 'content': content.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(cards)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
