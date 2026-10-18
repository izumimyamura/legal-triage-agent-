import fitz  # PyMuPDF
import io

def extract_document_text(uploaded_file):
    """
    Strictly on-device ingestion pipeline for PDFs and plain text (.txt).
    Includes automatic fallback for scanned PDF pages via local OCR (if available)
    and safe error handling for malformed/corrupted files.
    Returns: (list_of_page_dicts, error_message)
    """
    filename = uploaded_file.name.lower()
    extracted_data = []

    try:
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return [], "The uploaded file is empty (0 bytes). Please upload a valid PDF or TXT document."

        # 1. Plain Text (.txt) Ingestion
        if filename.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="replace").strip()
            if not text:
                return [], "The uploaded text file contains no readable characters."
            return [{"page": 1, "text": text, "ocr_used": False}], None

        # 2. PDF (.pdf) Ingestion + On-Device OCR Fallback
        elif filename.endswith(".pdf"):
            try:
                document = fitz.open(stream=file_bytes, filetype="pdf")
            except Exception:
                return [], "Malformed or corrupted PDF file detected. The file could not be safely parsed on-device."

            if len(document) == 0:
                return [], "The uploaded PDF has 0 pages."

            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text = page.get_text("text").strip()
                ocr_used = False

                # If page has no digital text, attempt local on-device OCR via PyMuPDF/Tesseract
                if not text:
                    try:
                        tp = page.get_textpage_ocr(flags=0, full=True)
                        ocr_text = page.get_text("text", textpage=tp).strip()
                        if ocr_text:
                            text = ocr_text
                            ocr_used = True
                    except Exception:
                        pass

                if not text:
                    text = "[SCAN DETECTED: No digital text found on this page. Install local Tesseract OCR engine for scanned image extraction.]"

                extracted_data.append({
                    "page": page_num + 1,
                    "text": text,
                    "ocr_used": ocr_used
                })

            return extracted_data, None

        else:
            return [], f"Unsupported file format ({filename}). Only PDF and TXT files are supported."

    except Exception as e:
        return [], f"Safe Ingestion Guardrail Triggered: Unable to process malformed file ({str(e)})."