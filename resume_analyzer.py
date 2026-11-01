import streamlit as st
import re
from pypdf import PdfReader

def analyze_resume(uploaded_file, career_goal):
    reader = PdfReader(uploaded_file)

    resume_text = ""

    for page in reader.pages:
        resume_text += page.extract_text() or ""

    resume_text = resume_text.lower()

    skills = [
        "python", "java", "c", "c++", "html",
        "css", "javascript", "sql", "flask",
        "django", "machine learning", "data analysis",
        "git", "github", "react"
    ]

    found_skills = []

    for skill in skills:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, resume_text):
            found_skills.append(skill.upper())

    career_skills = {
        "Web Development": [
            "HTML", "CSS", "JAVASCRIPT", "REACT", "GIT"
        ],
        "Python Developer": [
            "PYTHON", "SQL", "GIT", "FLASK"
        ],
        "Data Analyst": [
            "PYTHON", "SQL", "DATA ANALYSIS"
        ],
        "AI/ML Engineer": [
            "PYTHON", "MACHINE LEARNING", "SQL"
        ]
    }

    required_skills = career_skills.get(
        career_goal, ["PYTHON", "SQL", "GIT"]
    )

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in found_skills
    ]

    return found_skills, missing_skills