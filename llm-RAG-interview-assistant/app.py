import streamlit as st

from src.content_generator import (
    generate_learning_content,
    generate_diagnostic_questions
)
from src.feedback_engine import (
    evaluate_answer,
    diagnose_skill_gaps
)


st.set_page_config(
    page_title="Adaptive AI Learning Coach",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Adaptive AI Learning Coach")
st.write(
    "Adaptive learning MVP: the system can recommend topics, diagnose skill gaps, "
    "generate personalized content, and evaluate learner answers."
)

st.sidebar.header("Learner Profile")

technical_level = st.sidebar.selectbox(
    "Technical Level",
    ["Beginner", "Intermediate", "Advanced"]
)

career_goal = st.sidebar.text_input(
    "Career Goal",
    placeholder="Example: AI Engineer, Data Analyst, ML Engineer"
)

existing_skills = st.sidebar.text_area(
    "Existing Skills",
    placeholder="Example: Python, SQL, Machine Learning, Streamlit"
)

learning_goal = st.sidebar.text_area(
    "Learning Goal",
    placeholder="Example: I want to prepare for AI Engineer interviews."
)

weaknesses = st.sidebar.text_area(
    "Known Weaknesses / Gaps (Optional)",
    placeholder="Leave empty if unknown"
)

topic = st.sidebar.text_input(
    "Topic to Learn (Optional)",
    placeholder="Leave empty for AI recommendation"
)

st.sidebar.divider()
st.sidebar.subheader("Adaptive Workflow")
st.sidebar.code(
    """
Learner Profile
↓
AI Recommends / Diagnoses Topics
↓
Diagnostic Questions
↓
Skill Gap Detection
↓
Personalized Content
↓
Answer Feedback
↓
Profile Adaptation
"""
)

tab1, tab2, tab3 = st.tabs(
    [
        "🔍 Diagnose Skill Gaps",
        "📘 Generate Personalized Content",
        "🧪 Evaluate Learner Answer"
    ]
)


with tab1:
    st.header("🔍 Diagnostic Skill-Gap Analysis")

    st.write(
        "If the learner does not know their weaknesses or topic, "
        "the AI generates diagnostic questions based on career goal and skills."
    )

    if st.button("Generate Diagnostic Questions"):
        if not career_goal or not existing_skills or not learning_goal:
            st.warning("Please complete career goal, existing skills, and learning goal.")
        else:
            with st.spinner("Generating diagnostic questions..."):
                diagnostic_questions = generate_diagnostic_questions(
                    technical_level=technical_level,
                    career_goal=career_goal,
                    existing_skills=existing_skills,
                    learning_goal=learning_goal,
                    topic=topic
                )

                st.session_state["diagnostic_questions"] = diagnostic_questions
                st.session_state["technical_level"] = technical_level
                st.session_state["career_goal"] = career_goal
                st.session_state["existing_skills"] = existing_skills
                st.session_state["learning_goal"] = learning_goal
                st.session_state["topic"] = topic

            st.success("Diagnostic questions generated!")
            st.markdown(diagnostic_questions)

    if "diagnostic_questions" in st.session_state:
        st.subheader("Diagnostic Questions")
        st.markdown(st.session_state["diagnostic_questions"])

        learner_answers = st.text_area(
            "Learner Answers",
            placeholder="Answer the diagnostic questions here...",
            height=250
        )

        if st.button("Analyze Skill Gaps"):
            if not learner_answers:
                st.warning("Please enter learner answers first.")
            else:
                with st.spinner("Analyzing skill gaps..."):
                    skill_gap_report = diagnose_skill_gaps(
                        technical_level=st.session_state.get(
                            "technical_level", technical_level
                        ),
                        career_goal=st.session_state.get(
                            "career_goal", career_goal
                        ),
                        existing_skills=st.session_state.get(
                            "existing_skills", existing_skills
                        ),
                        learning_goal=st.session_state.get(
                            "learning_goal", learning_goal
                        ),
                        diagnostic_questions=st.session_state[
                            "diagnostic_questions"
                        ],
                        learner_answers=learner_answers,
                        topic=st.session_state.get("topic", topic)
                    )

                    st.session_state["skill_gap_report"] = skill_gap_report
                    st.session_state["detected_weaknesses"] = skill_gap_report

                st.success("Skill-gap analysis completed!")
                st.markdown(skill_gap_report)

    if "skill_gap_report" in st.session_state:
        st.divider()
        st.subheader("Latest Skill-Gap Report")
        st.markdown(st.session_state["skill_gap_report"])


with tab2:
    st.header("📘 Personalized Learning Content")

    st.write(
        "If no topic is entered, the AI recommends the most relevant focus topic "
        "based on the learner profile and detected gaps."
    )

    use_detected_gaps = st.checkbox(
        "Use detected skill gaps from diagnostic analysis",
        value=True
    )

    if st.button("Generate Learning Content"):
        if not career_goal or not existing_skills or not learning_goal:
            st.warning("Please complete career goal, existing skills, and learning goal.")
        else:
            final_weaknesses = weaknesses

            if use_detected_gaps and "detected_weaknesses" in st.session_state:
                final_weaknesses = st.session_state["detected_weaknesses"]

            with st.spinner("Generating adaptive learning content..."):
                content = generate_learning_content(
                    technical_level=technical_level,
                    career_goal=career_goal,
                    existing_skills=existing_skills,
                    learning_goal=learning_goal,
                    weaknesses=final_weaknesses,
                    topic=topic
                )

                st.session_state["generated_content"] = content
                st.session_state["technical_level"] = technical_level
                st.session_state["career_goal"] = career_goal
                st.session_state["learning_goal"] = learning_goal
                st.session_state["topic"] = topic

            st.success("Content generated successfully!")
            st.markdown(content)

    if "generated_content" in st.session_state:
        st.divider()
        st.subheader("Last Generated Content")
        st.markdown(st.session_state["generated_content"])


with tab3:
    st.header("🧪 Learner Answer Evaluation")

    question = st.text_area(
        "Interview Question",
        placeholder="Paste one generated interview question here."
    )

    learner_answer = st.text_area(
        "Learner Answer",
        placeholder="Type the learner's answer here..."
    )

    if st.button("Evaluate Answer"):
        if not question or not learner_answer:
            st.warning("Please enter both the interview question and learner answer.")
        else:
            saved_level = st.session_state.get("technical_level", technical_level)
            saved_goal = st.session_state.get("career_goal", career_goal)
            saved_learning_goal = st.session_state.get("learning_goal", learning_goal)
            saved_topic = st.session_state.get("topic", topic)

            with st.spinner("Evaluating learner answer..."):
                feedback = evaluate_answer(
                    technical_level=saved_level,
                    career_goal=saved_goal,
                    learning_goal=saved_learning_goal,
                    question=question,
                    learner_answer=learner_answer,
                    topic=saved_topic
                )

            st.session_state["latest_feedback"] = feedback

            st.success("Feedback generated successfully!")
            st.markdown(feedback)

    if "latest_feedback" in st.session_state:
        st.divider()
        st.subheader("Latest Answer Feedback")
        st.markdown(st.session_state["latest_feedback"])