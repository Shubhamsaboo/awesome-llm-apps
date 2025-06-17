import io
import logging
import re
import pdfplumber
from docx import Document as DocxDocument # Renamed to avoid conflict
from bs4 import BeautifulSoup

# Configure logging for this module
logger = logging.getLogger(__name__)

def _extract_text_from_pdf(content: bytes) -> str:
    text = ""
    try:
        with io.BytesIO(content) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        if text.strip():
            logger.info("Successfully extracted text using pdfplumber.")
            return text
    except Exception as e_plumber:
        logger.warning(f"PDF extraction error with pdfplumber: {str(e_plumber)}. Trying pdfminer.six.")
    
    # Fallback to pdfminer.six
    try:
        from pdfminer.high_level import extract_text as extract_text_pdfminer
        with io.BytesIO(content) as pdf_file_obj:
             text = extract_text_pdfminer(pdf_file_obj)
        if text.strip():
            logger.info("Successfully extracted text using pdfminer.six as fallback.")
            return text
    except Exception as e_miner:
        logger.error(f"PDF extraction error with pdfminer.six: {str(e_miner)}")
    
    if not text.strip():
        logger.warning("Both pdfplumber and pdfminer.six failed to extract text from PDF.")
    return text

def _extract_text_from_docx(content: bytes) -> str:
    try:
        doc = DocxDocument(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}", exc_info=True)
        return ""

def _extract_text_from_html(html_content: str) -> str:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r'\n\s*\n', '\n\n', text) # Consolidate multiple newlines
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}", exc_info=True)
        return ""

def parse_file_content(content: bytes, file_format: str, filename: str) -> str:
    """
    Parses raw byte content from a file into a text string based on its format.
    """
    logger.info(f"Parsing content from '{filename}' (format: {file_format}).")
    try:
        if file_format == 'pdf':
            return _extract_text_from_pdf(content)
        elif file_format == 'docx':
            return _extract_text_from_docx(content)
        elif file_format == 'txt':
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 decoding failed for {filename}, trying ISO-8859-1.")
                return content.decode('iso-8859-1', errors='replace')
        elif file_format == 'html':
            # HTML content might already be a string if read from a text stream,
            # but if it's bytes, it needs decoding first.
            # Assuming HTML content is passed as bytes, similar to other formats.
            try:
                decoded_html = content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 decoding failed for HTML {filename}, trying ISO-8859-1.")
                decoded_html = content.decode('iso-8859-1', errors='replace')
            return _extract_text_from_html(decoded_html)
        else:
            logger.warning(f"Unsupported file format for text extraction: {file_format} for file {filename}")
            return ""
    except Exception as e:
        logger.error(f"Error parsing {file_format} file {filename}: {e}", exc_info=True)
        return ""