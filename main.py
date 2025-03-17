import read_resume
import File_downloader_from_github as file_downloader
import re
import os
import pandas as pd

def parse_resume_sections(resume_text, resume_name, base_path="/workspaces/SIMS-Project/Resume_Scrapper/Downloaded/resume_text/"):
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

    # Save to files
    os.makedirs(base_path, exist_ok=True)
    for section, content in sections.items():
        filename = f"{section.replace(' ', '_')}.txt"
        with open(base_path+resume_name+"-"+filename, 'w', encoding='utf-8') as f:
            f.write(content)

    return sections


def load_dataset(file_path):
    """Loads a dataset from a CSV file."""
    return pd.read_csv(file_path)

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

def process_resume(pdf_path, company_df, skills_df, universities_df):
    """Processes a resume and returns its score."""
    resume_text, extracted_links = read_resume.extract_text_and_links_from_pdf(pdf_path)
    resume_sections = parse_resume_sections(resume_text, pdf_path.split("/")[-1])
    print(f"\n🔄 Extracted sections of {pdf_path.split('/')[-1]}")
    
    company_ranks = match_keywords(resume_sections.get("EXPERIENCE", ""), company_df, 'Name', 'Rank')
    skills_scores = match_keywords(resume_sections.get("SKILLS", ""), skills_df, 'Skill', 'Score')
    university_rankings = match_keywords(resume_sections.get("EDUCATION", ""), universities_df, 'University', 'ranking')
    
    has_experience = "EXPERIENCE" in resume_sections and bool(resume_sections["EXPERIENCE"].strip())
    
    for link in extracted_links:
        if "github" in link:
            file_downloader.Downloader(link)
    print("🔄 Downloaded code files from GitHub links.")
    
    # Fix count issue
    global count
    count += 1
    print(f"✅ Processed {count} resumes...")

    return calculate_resume_score(company_ranks, skills_scores, university_rankings, has_experience)

count = 0

if __name__ == "__main__":
    print("🚀 Resume Processing started...")
    print("\n🔄 Loading datasets...")
    company_df = load_dataset('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Companies_Dataset.csv')
    skills_df = load_dataset('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Skills_Dataset.csv')
    universities_df = load_dataset('/workspaces/SIMS-Project/Resume_Scrapper/Datasets/Universities_Dataset.csv')
    print("✅ Datasets loaded successfully.")
    
    resume_files = [
        '/workspaces/SIMS-Project/Resume_Scrapper/Resumes/autoCV (1).pdf',
        '/workspaces/SIMS-Project/Resume_Scrapper/Resumes/autoCV (3).pdf',
        '/workspaces/SIMS-Project/Resume_Scrapper/Resumes/autoCV (4).pdf',
        '/workspaces/SIMS-Project/Resume_Scrapper/Resumes/Resume_2.pdf',
        '/workspaces/SIMS-Project/Resume_Scrapper/Resumes/me.pdf',
    ]
    
    print("🔎 Processing resumes...")
    resume_scores = [(file, process_resume(file, company_df, skills_df, universities_df)) for file in resume_files]
    resume_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("\n📊 Resumes Ranking (Highest to Lowest):")
    print("=" * 50)
    for rank, (file, score) in enumerate(resume_scores, start=1):
        print(f"🏅 Rank {rank}: {file.split('/')[-1]} --> Score: {score}")
    print("=" * 50)