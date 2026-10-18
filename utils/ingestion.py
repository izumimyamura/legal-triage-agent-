import fitz

def extract_text_from_pdf(uploaded_file):
    document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    extracted_data = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        extracted_data.append({
            "page": page_num + 1,
            "text": text.strip()
        })
    return extracted_data
