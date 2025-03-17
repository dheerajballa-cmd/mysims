import pdfplumber
import pdfminer.high_level as pm
import re

def extract_text_and_links_from_pdf(pdf_path):
    text = pm.extract_text(pdf_path)
    links = []

    github_link_pattern = r"https://github\.com/[a-zA-Z0-9-_]+/[a-zA-Z0-9-_]+"
    links += re.findall(github_link_pattern, text)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            hyperlinks = page.hyperlinks
            if hyperlinks:
                for hyperlink in hyperlinks:
                    if 'uri' in hyperlink:
                        links.append(hyperlink['uri'])

    links = list(set(links))
    return text, links