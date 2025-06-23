import pymupdf4llm
from docx import Document
import pandas as pd

def extract_text_from_pdf(file_path: str, 
                          pages: list[int] = None,
                          write_images: bool = False,
                          image_path: str = None) -> str:
    """Extract text from PDF file as MD format"""
    md_text = pymupdf4llm.to_markdown(file_path, pages=pages, write_images=write_images, image_path=image_path)
    return md_text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    md_lines = []

    for para in doc.paragraphs:
        style = para.style.name
        text = ""

        if style.startswith("Heading"):
            level = int(style.split()[-1]) 
            text = f"{'#' * level} {para.text}"
        elif style in ["List Paragraph"]:
            text = f"- {para.text}"
        else:
            for run in para.runs:
                run_text = run.text
                if not run_text.strip():
                    text += run_text
                    continue
                if run.bold:
                    run_text = f"**{run_text}**"
                if run.italic:
                    run_text = f"*{run_text}*"
                if run.underline:
                    run_text = f"_{run_text}_"
                text += run_text

        md_lines.append(text)
    md_text = "\n\n".join(md_lines)
    return md_text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def extract_text_from_csv(file_path: str) -> str:
    """Extract text from CSV file"""
    df = pd.read_csv(file_path)
    return df.to_string()

def extract_text_from_md(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text_from_py(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text_from_tex(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text_from_html(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text(file_path: str) -> str:
    """Extract text based on file type"""
    file_type = file_path.split('.')[-1]
    if file_type.lower() == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type.lower() in ['docx', 'doc']:
        return extract_text_from_docx(file_path)
    elif file_type.lower() == 'txt':
        return extract_text_from_txt(file_path)
    elif file_type.lower() == 'csv':
        return extract_text_from_csv(file_path)
    elif file_type.lower() == 'md':
        return extract_text_from_md(file_path)
    elif file_type.lower() == 'py':
        return extract_text_from_py(file_path)
    elif file_type.lower() == 'tex':
        return extract_text_from_tex(file_path)
    elif file_type.lower() == 'html':
        return extract_text_from_html(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
