import os
import pytesseract
from PIL import Image
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def ocr_tesseract(image_path, output_txt_file):
    """
    Perform OCR on the image and save the extracted text to a text file.

    Args:
    - image_path: Path to the input image (PNG format)
    - output_txt_file: Path to the output text file to store the extracted text
    """
    logging.info(f"Starting OCR processing for {image_path}")
    
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        # Write extracted text to output file
        with open(output_txt_file, "w") as f:
            f.write(text)
        
        logging.info(f"Completed OCR processing. Extracted text saved to {output_txt_file}")
        print(f"OCR Completed. Text saved to {output_txt_file}")

    except Exception as e:
        logging.error(f"Error occurred during OCR processing: {e}")

if __name__ == "__main__":
    # Example usage
    image_path = "test.png"  # Path to your input PNG image
    output_txt_file = "output_text.txt"  # Path to your output text file

    ocr_tesseract(image_path, output_txt_file)
