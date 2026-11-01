import os
import sqlite3
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st

from auth import register_user, login_user

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="StudentCareerAI",
    page_icon="🎓",
    layout="wide",
)

DATABASE_NAME = "studentcareerai.db"


# ==================================================
# 2. LOAD CSS
# ==================================================

def load_css():
    css_path = os.path.join("static", "style.css")

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as file:
            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True,
            )


load_css()


# ==================================================
# 3. DATABASE
# ==================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course TEXT,
            year TEXT,
            skills TEXT,
            interests TEXT,
            username TEXT,
            branch TEXT,
            career_goal TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(students)")
    existing_columns = {
        row[1] for row in cursor.fetchall()
    }

    required_columns = {
        "name": "TEXT",
        "course": "TEXT",
        "year": "TEXT",
        "skills": "TEXT",
        "interests": "TEXT",
        "username": "TEXT",
        "branch": "TEXT",
        "career_goal": "TEXT",
    }

    for column, data_type in required_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE students ADD COLUMN {column} {data_type}"
            )

    connection.commit()
    connection.close()


initialize_database()


# ==================================================
# 4. SESSION STATE
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""

if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"


# ==================================================
# 5. CAREER DATA
# ==================================================

CAREERS = {
    "Software Developer": {
        "skills": [
            "Python",
            "Java",
            "C",
            "Data Structures",
            "Problem Solving",
            "Git",
        ],
        "interests": [
            "Coding",
            "Programming",
            "Software Development",
        ],
        "roadmap": [
            "Learn Python or Java fundamentals.",
            "Practice Data Structures and Algorithms.",
            "Solve coding problems regularly.",
            "Build two or three software projects.",
            "Learn Git and GitHub.",
            "Prepare for technical interviews.",
        ],
    },

    "Web Developer": {
        "skills": [
            "HTML",
            "CSS",
            "JavaScript",
            "React",
            "Git",
        ],
        "interests": [
            "Web Development",
            "Website Design",
            "Frontend Development",
        ],
        "roadmap": [
            "Learn HTML.",
            "Practice CSS and responsive design.",
            "Learn JavaScript.",
            "Build interactive websites.",
            "Learn React basics.",
            "Publish your projects on GitHub.",
        ],
    },

    "Data Analyst": {
        "skills": [
            "Python",
            "SQL",
            "Excel",
            "Pandas",
            "Statistics",
        ],
        "interests": [
            "Data Analysis",
            "Statistics",
            "Data Visualization",
        ],
        "roadmap": [
            "Learn Excel and basic statistics.",
            "Learn SQL.",
            "Practice Python.",
            "Learn Pandas and data cleaning.",
            "Create charts and dashboards.",
            "Build data analysis projects.",
        ],
    },

    "AI / ML Engineer": {
        "skills": [
            "Python",
            "Mathematics",
            "Statistics",
            "Machine Learning",
            "Pandas",
        ],
        "interests": [
            "Artificial Intelligence",
            "Machine Learning",
            "Deep Learning",
        ],
        "roadmap": [
            "Learn Python programming.",
            "Study basic mathematics and statistics.",
            "Learn NumPy and Pandas.",
            "Understand machine learning concepts.",
            "Practice with beginner datasets.",
            "Build machine learning projects.",
        ],
    },

    "Cybersecurity Analyst": {
        "skills": [
            "Networking",
            "Linux",
            "Python",
            "Security Fundamentals",
            "Problem Solving",
        ],
        "interests": [
            "Cybersecurity",
            "Ethical Hacking",
            "Network Security",
        ],
        "roadmap": [
            "Learn computer networking.",
            "Practice Linux commands.",
            "Understand operating system security.",
            "Study common cyber threats.",
            "Practice using legal cybersecurity labs.",
            "Build a cybersecurity portfolio.",
        ],
    },
}


# ==================================================
# 6. STUDENT PROFILE FUNCTIONS
# ==================================================

def save_profile(
    username,
    name,
    branch,
    year,
    skills,
    interests,
    career_goal,
):
    connection = get_connection()
    cursor = connection.cursor()

    skills_text = ", ".join(skills)
    interests_text = ", ".join(interests)

    cursor.execute("""
        SELECT id
        FROM students
        WHERE username = ?
        ORDER BY id DESC
        LIMIT 1
    """, (username,))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE students
            SET name = ?,
                course = ?,
                year = ?,
                skills = ?,
                interests = ?,
                branch = ?,
                career_goal = ?
            WHERE id = ?
        """, (
            name,
            branch,
            year,
            skills_text,
            interests_text,
            branch,
            career_goal,
            existing[0],
        ))

    else:
        cursor.execute("""
            INSERT INTO students
            (
                name,
                course,
                year,
                skills,
                interests,
                username,
                branch,
                career_goal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            branch,
            year,
            skills_text,
            interests_text,
            username,
            branch,
            career_goal,
        ))

    connection.commit()
    connection.close()


def get_profile(username):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, branch, year, skills, interests, career_goal
        FROM students
        WHERE username = ?
        ORDER BY id DESC
        LIMIT 1
    """, (username,))

    profile = cursor.fetchone()
    connection.close()

    return profile


def get_all_students():
    connection = get_connection()

    dataframe = pd.read_sql_query("""
        SELECT name, branch, year, skills, interests, career_goal
        FROM students
        ORDER BY id DESC
    """, connection)

    connection.close()

    return dataframe


# ==================================================
# 7. PDF CAREER REPORT
# ==================================================

def create_pdf_report(profile, username):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CareerReportTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#173F8A"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "CareerReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "CareerReportHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#087F8C"),
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = styles["BodyText"]

    name, branch, year, skills, interests, career_goal = profile

    story = [
        Paragraph("StudentCareerAI", title_style),
        Paragraph(
            "PERSONAL CAREER DEVELOPMENT REPORT",
            subtitle_style,
        ),
        Paragraph("Student Profile", heading_style),
    ]

    profile_data = [
        ["Student Name", name or "Not provided"],
        ["Username", username],
        ["Branch / Course", branch or "Not provided"],
        ["Academic Year", year or "Not provided"],
        ["Career Goal", career_goal or "Not selected"],
        ["Report Date", datetime.now().strftime("%d-%m-%Y")],
    ]

    safe_profile_data = [
        [escape(str(value)) for value in row]
        for row in profile_data
    ]

    table = Table(
        safe_profile_data,
        colWidths=[150, 330],
    )

    table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (0, -1),
            colors.HexColor("#DCE8FF"),
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (0, -1),
            colors.HexColor("#173F8A"),
        ),
        (
            "BACKGROUND",
            (1, 0),
            (1, -1),
            colors.HexColor("#F4F8FF"),
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#B8C9E8"),
        ),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Current Skills", heading_style))
    story.append(
        Paragraph(
            escape(skills or "No skills added yet"),
            body_style,
        )
    )

    story.append(Paragraph("Interests", heading_style))
    story.append(
        Paragraph(
            escape(interests or "No interests added yet"),
            body_style,
        )
    )

    story.append(Paragraph("Career Roadmap", heading_style))

    career_information = CAREERS.get(career_goal, {})
    roadmap = career_information.get("roadmap", [])

    if roadmap:
        for index, item in enumerate(roadmap, start=1):
            story.append(
                Paragraph(
                    f"{index}. {escape(item)}",
                    body_style,
                )
            )
            story.append(Spacer(1, 5))
    else:
        story.append(
            Paragraph(
                "Choose a career goal to receive a roadmap.",
                body_style,
            )
        )

    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "Generated by StudentCareerAI | Learn, practice, and grow.",
            subtitle_style,
        )
    )

    document.build(story)
    buffer.seek(0)

    return buffer.getvalue()


# ==================================================
# 8. LOGIN AND REGISTRATION
# ==================================================

def show_authentication():
    st.title("🎓 StudentCareerAI")

    st.markdown(
        "### Discover your career. Improve your skills. Build your future."
    )

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.subheader("Welcome Back")

        login_username = st.text_input(
            "Username",
            key="login_username",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button("Login", use_container_width=True):
            if not login_username.strip() or not login_password:
                st.error("Enter your username and password.")

            else:
                success = login_user(
                    login_username.strip(),
                    login_password,
                )

                if success:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = (
                        login_username.strip()
                    )
                    st.session_state["page"] = "Dashboard"

                    st.success("Login successful!")
                    st.rerun()

                else:
                    st.error(
                        "Login failed. Check your username and password."
                    )

    with register_tab:
        st.subheader("Create Your Account")

        new_username = st.text_input(
            "Choose a username",
            key="register_username",
        )

        new_password = st.text_input(
            "Create a password (minimum 8 characters)",
            type="password",
            key="register_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="confirm_password",
        )

        if st.button("Register", use_container_width=True):
            if not new_username.strip() or not new_password:
                st.error("Enter a username and password.")

            elif len(new_password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                success, message = register_user(
                    new_username.strip(),
                    new_password,
                )

                if success:
                    st.success(message)
                    st.info(
                        "Registration completed! Open the Login tab "
                        "and sign in with your new account."
                    )

                else:
                    st.error(message)


# ==================================================
# 9. SIDEBAR
# ==================================================

def show_sidebar():
    with st.sidebar:
        st.title("🎓 StudentCareerAI")
        st.caption("Your student career companion")

        st.success(
            f"Logged in as {st.session_state['username']}"
        )

        menu_items = [
            "Dashboard",
            "My Profile",
            "Career Recommendations",
            "Skill Gap Analysis",
            "Career Roadmap",
            "Career Report",
            "Student Records",
        ]

        current_page = st.session_state["page"]

        selected_index = (
            menu_items.index(current_page)
            if current_page in menu_items
            else 0
        )

        selected_page = st.radio(
            "Navigation",
            menu_items,
            index=selected_index,
            key="navigation_radio",
        )

        st.session_state["page"] = selected_page

        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["page"] = "Dashboard"

            st.rerun()


# ==================================================
# 10. DASHBOARD
# ==================================================

def show_dashboard():
    username = st.session_state["username"]

    st.title("🏠 Dashboard")
    st.write(f"Welcome back, **{username}**!")

    profile = get_profile(username)

    if profile:
        name, branch, year, skills, interests, career_goal = profile

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Branch", branch or "Not added")

        with col2:
            st.metric("Academic Year", year or "Not added")

        with col3:
            st.metric("Career Goal", career_goal or "Not selected")

        st.subheader("Your Profile Summary")

        st.write("**Name:**", name or "Not provided")
        st.write("**Skills:**", skills or "Not added")
        st.write("**Interests:**", interests or "Not added")

    else:
        st.info(
            "Your profile is empty. Open My Profile to enter your details."
        )

    st.divider()

    st.subheader("Explore StudentCareerAI")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎯 Career")
        st.write("Explore careers based on your skills and interests.")

    with col2:
        st.markdown("### 📚 Skills")
        st.write("Find skills you can learn for your chosen career.")

    with col3:
        st.markdown("### 📄 Report")
        st.write("Generate a downloadable PDF career report.")


# ==================================================
# 11. MY PROFILE
# ==================================================

def show_profile_page():
    st.title("👤 My Profile")

    username = st.session_state["username"]
    profile = get_profile(username)

    if profile:
        (
            old_name,
            old_branch,
            old_year,
            old_skills,
            old_interests,
            old_goal,
        ) = profile

    else:
        old_name = ""
        old_branch = "CSE"
        old_year = "3rd Year"
        old_skills = ""
        old_interests = ""
        old_goal = "Software Developer"

    branch_options = [
        "CSE",
        "ISE",
        "ECE",
        "EEE",
        "Mechanical",
        "Civil",
        "Other",
    ]

    year_options = [
        "1st Year",
        "2nd Year",
        "3rd Year",
        "4th Year",
    ]

    career_options = list(CAREERS.keys())

    with st.form("profile_form"):
        name = st.text_input(
            "Full Name",
            value=old_name or "",
        )

        current_branch = (
            old_branch
            if old_branch in branch_options
            else "CSE"
        )

        branch = st.selectbox(
            "Branch / Course",
            branch_options,
            index=branch_options.index(current_branch),
        )

        current_year = (
            old_year
            if old_year in year_options
            else "3rd Year"
        )

        year = st.selectbox(
            "Academic Year",
            year_options,
            index=year_options.index(current_year),
        )

        skills_text = st.text_input(
            "Your Skills",
            value=old_skills or "",
            help="Example: Python, C, Java",
        )

        interests_text = st.text_input(
            "Your Interests",
            value=old_interests or "",
            help="Example: Coding, Web Development",
        )

        current_goal = (
            old_goal
            if old_goal in career_options
            else "Software Developer"
        )

        career_goal = st.selectbox(
            "Career Goal",
            career_options,
            index=career_options.index(current_goal),
        )

        submitted = st.form_submit_button(
            "Save Profile",
            use_container_width=True,
        )

    if submitted:
        if not name.strip():
            st.error("Please enter your full name.")

        else:
            skills = [
                item.strip()
                for item in skills_text.split(",")
                if item.strip()
            ]

            interests = [
                item.strip()
                for item in interests_text.split(",")
                if item.strip()
            ]

            save_profile(
                username,
                name.strip(),
                branch,
                year,
                skills,
                interests,
                career_goal,
            )

            st.success("Your profile has been saved!")
            st.rerun()


# ==================================================
# 12. SMART CAREER RECOMMENDATIONS
# ==================================================

def show_career_recommendations():
    st.title("🤖 Smart Career Recommendations")

    username = st.session_state["username"]
    profile = get_profile(username)

    if not profile:
        st.warning("Please complete your profile first.")
        st.info("Open My Profile and save your details.")
        return

    name, branch, year, skills_text, interests_text, career_goal = profile

    st.write(f"Welcome, **{name}**!")
    st.write(
        "Explore career options based on your skills and interests."
    )

    student_skills = {
        item.strip().lower()
        for item in (skills_text or "").split(",")
        if item.strip()
    }

    student_interests = {
        item.strip().lower()
        for item in (interests_text or "").split(",")
        if item.strip()
    }

    results = []

    for career_name, information in CAREERS.items():
        required_skills = information["skills"]
        required_interests = information["interests"]

        matching_skills = [
            skill
            for skill in required_skills
            if skill.lower() in student_skills
        ]

        matching_interests = [
            interest
            for interest in required_interests
            if any(
                interest.lower() in student_interest
                or student_interest in interest.lower()
                for student_interest in student_interests
            )
        ]

        total_items = (
            len(required_skills) + len(required_interests)
        )

        matched_items = (
            len(matching_skills) + len(matching_interests)
        )

        score = round(
            matched_items / total_items * 100
        ) if total_items else 0

        results.append({
            "career": career_name,
            "score": score,
            "matching_skills": matching_skills,
            "matching_interests": matching_interests,
        })

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    st.divider()
    st.subheader("🎯 Your Career Matches")

    for result in results:
        with st.container(border=True):
            st.subheader(result["career"])

            st.progress(result["score"] / 100)

            st.write(
                f"**Profile match: {result['score']}%**"
            )

            if result["matching_skills"]:
                st.write(
                    "**Matching skills:** "
                    + ", ".join(result["matching_skills"])
                )

            if result["matching_interests"]:
                st.write(
                    "**Matching interests:** "
                    + ", ".join(result["matching_interests"])
                )

            if not result["matching_skills"] and not result["matching_interests"]:
                st.write(
                    "Add relevant skills or interests to explore this career."
                )

            if result["score"] > 0:
                st.success("Some of your profile details match this career.")

    st.caption(
        "These percentages are keyword-based profile matches. "
        "They are not generated by a trained AI model and do not "
        "guarantee career suitability."
    )


# ==================================================
# 13. SKILL GAP ANALYSIS
# ==================================================

def show_skill_gap():
    st.title("📚 Skill Gap Analysis")

    profile = get_profile(st.session_state["username"])

    if not profile:
        st.warning("Save your profile first.")
        return

    name, branch, year, skills_text, interests, career_goal = profile

    career = CAREERS.get(career_goal)

    if not career:
        st.info("Select a career goal in My Profile.")
        return

    current_skills = {
        item.strip().lower()
        for item in (skills_text or "").split(",")
        if item.strip()
    }

    required_skills = career["skills"]

    matched = [
        skill
        for skill in required_skills
        if skill.lower() in current_skills
    ]

    missing = [
        skill
        for skill in required_skills
        if skill.lower() not in current_skills
    ]

    percentage = round(
        len(matched) / len(required_skills) * 100
    ) if required_skills else 0

    st.subheader(f"Career Goal: {career_goal}")

    st.metric("Skill Match", f"{percentage}%")
    st.progress(percentage / 100)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Skills You Have")

        if matched:
            for skill in matched:
                st.write(f"• {skill}")
        else:
            st.write("Add your current skills in My Profile.")

    with col2:
        st.subheader("📌 Skills to Learn")

        if missing:
            for skill in missing:
                st.write(f"• {skill}")
        else:
            st.success("You listed all recommended skills!")

    st.caption(
        "This is a simple comparison of your listed skills "
        "against the selected career's recommended skills."
    )


# ==================================================
# 14. CAREER ROADMAP
# ==================================================

def show_career_roadmap():
    st.title("🛣️ Career Roadmap")

    profile = get_profile(st.session_state["username"])

    if not profile:
        st.warning("Save your profile first.")
        return

    name, branch, year, skills, interests, career_goal = profile

    career = CAREERS.get(career_goal)

    if not career:
        st.info("Choose a career goal in My Profile.")
        return

    st.subheader(career_goal)
    st.write("Follow these learning steps one by one.")

    for index, step in enumerate(career["roadmap"], start=1):
        st.checkbox(
            f"Step {index}: {step}",
            key=f"roadmap_{st.session_state['username']}_{index}",
        )


# ==================================================
# 15. CAREER REPORT
# ==================================================

def show_career_report():
    st.title("📄 Career Report")

    username = st.session_state["username"]
    profile = get_profile(username)

    if not profile:
        st.warning(
            "Complete and save your profile before generating a report."
        )
        return

    name, branch, year, skills, interests, career_goal = profile

    st.subheader("Report Preview")

    st.write("**Student Name:**", name or "Not provided")
    st.write("**Username:**", username)
    st.write("**Branch:**", branch or "Not provided")
    st.write("**Academic Year:**", year or "Not provided")
    st.write("**Career Goal:**", career_goal or "Not selected")
    st.write("**Skills:**", skills or "Not added")
    st.write("**Interests:**", interests or "Not added")

    pdf_data = create_pdf_report(profile, username)

    st.download_button(
        label="📥 Download Career Report (PDF)",
        data=pdf_data,
        file_name="StudentCareerAI_Career_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# ==================================================
# 16. STUDENT RECORDS
# ==================================================

def show_student_records():
    st.title("📋 Student Records")

    dataframe = get_all_students()

    if dataframe.empty:
        st.info("No student profiles have been saved yet.")
        return

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = dataframe.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Student Records (CSV)",
        data=csv_data,
        file_name="student_records.csv",
        mime="text/csv",
    )


# ==================================================
# 17. MAIN APPLICATION
# ==================================================

def main():
    if not st.session_state["logged_in"]:
        show_authentication()
        return

    show_sidebar()

    selected_page = st.session_state["page"]

    if selected_page == "Dashboard":
        show_dashboard()

    elif selected_page == "My Profile":
        show_profile_page()

    elif selected_page == "Career Recommendations":
        show_career_recommendations()

    elif selected_page == "Skill Gap Analysis":
        show_skill_gap()

    elif selected_page == "Career Roadmap":
        show_career_roadmap()

    elif selected_page == "Career Report":
        show_career_report()

    elif selected_page == "Student Records":
        show_student_records()


if __name__ == "__main__":
    main()