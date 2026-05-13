import streamlit as st
from src.content_generator import generate_learning_content, evaluate_answer

st.set_page_config(
    page_title="Adaptive AI Learning Coach",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Adaptive AI Learning Coach")
st.write("Personalized technical summaries and interview practice based on learner level.")

tab1, tab2 = st.tabs(["Generate Learning Content", "Answer Evaluation"])

with tab1:
    st.header("Create Personalized Learning Content")

    role = st.selectbox(
        "Target Role",
        ["AI Engineer", "Machine Learning Engineer", "Data Engineer", "Software Engineer", "NLP Engineer"]
    )

    level = st.selectbox(
        "Learner Level",
        ["Beginner", "Intermediate", "Advanced"]
    )

    topic = st.text_input(
        "Topic",
        placeholder="Example: RAG, Python OOP, Vector Databases, Transformers"
    )

    goal = st.text_area(
        "Learning Goal",
        placeholder="Example: I want to prepare for an AI Engineer interview."
    )

    if st.button("Generate Content"):
        if not topic or not goal:
            st.warning("Please enter both topic and learning goal.")
        else:
            with st.spinner("Generating personalized content..."):
                content = generate_learning_content(role, level, topic, goal)
                st.session_state["generated_content"] = content
                st.session_state["role"] = role
                st.session_state["level"] = level
                st.session_state["topic"] = topic

            st.success("Content generated successfully!")
            st.markdown(content)

    if "generated_content" in st.session_state:
        st.divider()
        st.subheader("Generated Content")
        st.markdown(st.session_state["generated_content"])


with tab2:
    st.header("Evaluate Learner Answer")

    question = st.text_area(
        "Interview Question",
        placeholder="Paste one generated interview question here."
    )

    user_answer = st.text_area(
        "Your Answer",
        placeholder="Type your answer here."
    )

    if st.button("Evaluate Answer"):
        if not question or not user_answer:
            st.warning("Please enter both question and answer.")
        else:
            role = st.session_state.get("role", "AI Engineer")
            level = st.session_state.get("level", "Intermediate")
            topic = st.session_state.get("topic", "AI")

            with st.spinner("Evaluating your answer..."):
                feedback = evaluate_answer(role, level, topic, question, user_answer)

            st.success("Feedback generated!")
            st.markdown(feedback)