# pdf_preprocessor.py
import fitz  # PyMuPDF
import os
from typing import List, Dict, Any

class PDFProcessor:
    def __init__(self):
        self.extracted_data = []
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text content from a PDF file."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def process_pdf_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all PDFs in a directory."""
        processed_files = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(directory_path, filename)
                text_content = self.extract_text_from_pdf(file_path)
                processed_files.append({
                    'filename': filename,
                    'content': text_content
                })
        return processed_files
