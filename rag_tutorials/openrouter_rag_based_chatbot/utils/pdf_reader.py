# ==========================
# utils/pdf_reader.py
# ==========================
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_file):
    """
    Extracts and returns text content from a PDF file.
    :param pdf_file: Uploaded file from Streamlit (BytesIO)
    :return: Extracted text as a string
    """
    text = ""
    try:
        # Open the PDF in memory
        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
            for page in doc:
                # Extract text from each page
                text += page.get_text("text")
        return text
    except Exception as e:
        return f"⚠️ Error reading PDF: {e}"
