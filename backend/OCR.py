import os
import pytesseract
from PIL import Image
import logging
import cv2
import numpy as np


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
    
if __name__ == "__main__":
    # Example usage
    image_path = "test.png"  # Path to your input PNG image
    output_txt_file = "output_text.txt"  # Path to your output text file

    ocr_tesseract(image_path, output_txt_file)
