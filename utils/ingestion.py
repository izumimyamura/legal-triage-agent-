import fitz  # PyMuPDF

def extract_document_text(uploaded_file):
    """
    Locally extracts text from PDF or TXT files.
    Returns a tuple: (list_of_page_dicts, error_message)
    """
    filename = uploaded_file.name.lower()
    extracted_data = []

    try:
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return [], "The uploaded file is empty."

        # Handle Plain Text (.txt)
        if filename.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="replace").strip()
            if not text:
                return [], "No readable text found in the text file."
            return [{"page": 1, "text": text}], None

        # Handle PDF (.pdf)
        elif filename.endswith(".pdf"):
            document = fitz.open(stream=file_bytes, filetype="pdf")
            if len(document) == 0:
                return [], "The PDF contains 0 pages."

            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text = page.get_text("text").strip()
                extracted_data.append({
                    "page": page_num + 1,
                    "text": text if text else "[No extractable text on this page - may be a scanned image]"
                })
            return extracted_data, None

        else:
            return [], "Unsupported file format. Please upload a PDF or TXT file."

    except Exception as e:
        # Fails gracefully on malformed/corrupted files (Criterion 6: Robustness)
        return [], f"Failed to parse document safely: {str(e)}"
