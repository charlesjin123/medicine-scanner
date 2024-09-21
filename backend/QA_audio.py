import os
import subprocess
from transformers import pipeline  # For BioBERT model
from gtts import gTTS  # For text-to-speech
import speech_recognition as sr  # For transcription

# Configuration
BIOBERT_MODEL_PATH = "dmis-lab/biobert-large-cased-v1.1-squad"  # BioBERT model for QA
M4A_FILE_PATH = "input_audio.m4a"  # Path to your input M4A file
WAV_FILE_PATH = "converted_audio.wav"  # Path to save the converted WAV file

# Function to convert M4A to WAV
def convert_m4a_to_wav(m4a_file, wav_file):
    # Use ffmpeg to convert M4A to WAV
    command = f'ffmpeg -y -i "{m4a_file}" -ar 16000 -ac 1 "{wav_file}"'
    subprocess.call(command, shell=True)

# Function for Text-to-Speech (TTS) using gTTS
def text_to_speech(text, file_name="response.mp3"):
    tts = gTTS(text)
    tts.save(file_name)
    # Play the audio (adjust command for your OS)
    if os.name == 'posix':
        subprocess.call(["afplay", file_name])  # For macOS
    elif os.name == 'nt':
        os.startfile(file_name)  # For Windows
    else:
        subprocess.call(["mpg321", file_name])  # For Linux

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

# Main function to handle conversion, transcription, BioBERT processing, and audio output
def main():
    # Convert M4A to WAV
    print("Converting M4A to WAV...")
    convert_m4a_to_wav(M4A_FILE_PATH, WAV_FILE_PATH)

    # Transcribe the audio input using SpeechRecognition
    print("Transcribing audio...")
    transcribed_text = transcribe_audio(WAV_FILE_PATH)
    if transcribed_text is None:
        return

    # Get context from user input
    # print("Please enter the context for BioBERT:")
    context = """
    Aspirin is used to reduce fever and relieve mild to moderate pain from conditions such as muscle aches, toothaches, common cold, and headaches.
    It may also be used to reduce pain and swelling in conditions such as arthritis. Aspirin is known as a salicylate and a nonsteroidal 
    anti-inflammatory drug (NSAID). It works by blocking a certain natural substance in your body to reduce pain and swelling.
    Take 2 tablets every 4 to 6 hours, with a maximum of 8 tablets in a 24-hour period.
    """

    # Load BioBERT pipeline for question-answering
    print("Processing with BioBERT...")
    qa_pipeline = pipeline("question-answering", model=BIOBERT_MODEL_PATH)

    # Ask BioBERT the question based on transcribed text
    question = transcribed_text  # Using transcribed text as the question
    answer = qa_pipeline(question=question, context=context)
    print(f"Answer: {answer['answer']}")

    # Convert BioBERT's answer to speech and play it
    print("Converting answer to speech...")
    text_to_speech(answer['answer'])

if __name__ == "__main__":
    main()

