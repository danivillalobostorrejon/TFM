# pdf_preprocessor.py
import fitz  # PyMuPDF
import os
from typing import List, Dict, Any

class PDFProcessor:
    def __init__(self):
        self.extracted_data = []

    
    def generar_id(self, nombre_completo: str) -> str:
        nombre = nombre_completo.upper().strip()

        # Si tiene coma: "APELLIDO1 APELLIDO2, NOMBRE"
        if ',' in nombre:
            apellidos, nombre = map(str.strip, nombre.split(',', 1))
            partes_apellido = apellidos.split()
        else:
            partes = nombre.split()
            if len(partes) < 3:
                return nombre[:3]  # fallback
            nombre = partes[-1]  # Último elemento es nombre
            partes_apellido = partes[:-1]  # Resto son apellidos

        if len(partes_apellido) >= 2:
            id_code = partes_apellido[0][:2] + partes_apellido[1][:2] + nombre[0]
        elif len(partes_apellido) == 1:
            id_code = partes_apellido[0][:2] + nombre[:2]
        else:
            id_code = nombre[:3]

        return id_code.upper()

    def extract_text_from_pdf(self, file_input):
        """Extrae texto desde un archivo PDF, ya sea ruta o archivo subido por Streamlit"""
        if hasattr(file_input, "read"):  # Si es BytesIO (Streamlit uploader)
            doc = fitz.open(stream=file_input.read(), filetype="pdf")
        else:  # Si es una ruta (str)
            doc = fitz.open(file_input)

        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def extract_text_by_page(self, pdf_path: str) -> List[str]:
        doc = fitz.open(pdf_path)
        return [page.get_text() for page in doc]

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
