import docx
import json
from pathlib import Path

def extract_docx_content(file_path):
    doc = docx.Document(file_path)
    content = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            content.append(para.text.strip())
    
    return content

def process_profiles():
    profiles = {}
    docx_files = [
        'Nho_Thanh_Le_Profile_data_science.docx',
        'Nho_Thanh_Le_Profile_data_analytics.docx',
        'Nho_Thanh_Le_Profile_Data_Engineer.docx'
    ]
    
    for docx_file in docx_files:
        if Path(docx_file).exists():
            profile_name = docx_file.replace('Nho_Thanh_Le_Profile_', '').replace('.docx', '')
            profiles[profile_name] = extract_docx_content(docx_file)
    
    # Save the extracted content to a JSON file for easy access
    with open('profile_content.json', 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    process_profiles() 