import os
import re
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for
import read_resume
import File_downloader_from_github as file_downloader

app = Flask(__name__)

# Load datasets
company_df = pd.read_csv('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Companies_Dataset.csv')
skills_df = pd.read_csv('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Skills_Dataset.csv')
universities_df = pd.read_csv('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Universities_Dataset.csv')

def parse_resume_sections(resume_text, resume_name):
    """Parses different sections from a resume text."""
    section_headers = ["SUMMARY", "CONTACT", "OBJECTIVE", "REFERENCES", "SKILLS", "EDUCATION", "EXPERIENCE", "PROJECTS"]
    normalized_text = re.sub(r'[\r\u2022\u200b]', '', resume_text)
    normalized_text = re.sub(r'-\n', '', normalized_text)
    normalized_text = "\n" + normalized_text + "\n"

    sections = {}
    section_positions = []
    for header in section_headers:
        pattern = re.compile(rf'\n\s*{re.escape(header)}[\s:•\-]*\n+', re.IGNORECASE)
        for match in pattern.finditer(normalized_text):
            section_positions.append((match.start(), header))

    section_positions.sort()
    prev_end, prev_header = 0, "BASIC_INFO"

    for start, header in section_positions:
        sections[prev_header] = normalized_text[prev_end:start].strip()
        prev_end = start
        prev_header = header.upper()

    sections[prev_header] = normalized_text[prev_end:].strip()
    return sections

def match_keywords(section_text, dataset, column_name, metric_column):
    """Finds matching entries from a dataset in the given section text."""
    if not section_text:
        return pd.DataFrame(columns=[metric_column])
    section_text = section_text.lower()
    return dataset[dataset[column_name].str.lower().apply(lambda x: x in section_text)][[metric_column]]

def calculate_resume_score(company_ranks, skills_scores, university_rankings, has_work_experience):
    """Calculates the resume score based on different weighted factors."""
    company_score = company_ranks['Rank'].min() if not company_ranks.empty else 0
    skills_score = skills_scores['Score'].sum() if not skills_scores.empty else 0
    university_score = university_rankings['ranking'].min() if not university_rankings.empty else 0

    # Weights for each factor
    weights = {'company': 2.0, 'skills': 1.5, 'university': 1.0}
    total_score = (company_score * weights['company']) + (skills_score * weights['skills']) + (university_score * weights['university'])

    # Apply penalty if no work experience
    if not has_work_experience:
        total_score *= 0.8  # Reduce score by 20%

    scaled_score = round(total_score / 10, 2)  # Adjust scaling factor as needed
    return scaled_score

def process_resume(pdf_path):
    """Processes a resume and returns its score."""
    resume_text, extracted_links = read_resume.extract_text_and_links_from_pdf(pdf_path)
    resume_sections = parse_resume_sections(resume_text, pdf_path.split("/")[-1])

    company_ranks = match_keywords(resume_sections.get("EXPERIENCE", ""), company_df, 'Name', 'Rank')
    skills_scores = match_keywords(resume_sections.get("SKILLS", ""), skills_df, 'Skill', 'Score')
    university_rankings = match_keywords(resume_sections.get("EDUCATION", ""), universities_df, 'University', 'ranking')

    has_experience = "EXPERIENCE" in resume_sections and bool(resume_sections["EXPERIENCE"].strip())

    for link in extracted_links:
        if "github" in link:
            file_downloader.Downloader(link)

    return calculate_resume_score(company_ranks, skills_scores, university_rankings, has_experience)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return redirect(url_for('index'))

    file = request.files['resume']
    if file.filename == '':
        return redirect(url_for('index'))

    # Save the uploaded file
    upload_folder = "/workspaces/SIMS-Project/Resume_Scrapper/Uploaded_Resumes/"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    # Process the resume
    score = process_resume(file_path)

    return render_template('result.html', filename=file.filename, score=score)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)