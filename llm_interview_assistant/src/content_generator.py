import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_learning_content(role, level, topic, goal):
    prompt = f"""
You are an adaptive AI learning coach.

Learner profile:
- Target role: {role}
- Level: {level}
- Topic: {topic}
- Goal: {goal}

Generate personalized educational content.

Return the answer in this structure:

1. Personalized Technical Summary
Explain the topic according to the learner's level.

2. Key Concepts to Understand
List the most important concepts.

3. Interview Questions
Create 5 interview questions adapted to the learner's level and target role.

4. Model Answers
Provide short model answers for each question.

5. Recommended Next Steps
Suggest what the learner should study next.
"""

    response = model.generate_content(prompt)
    return response.text


def evaluate_answer(role, level, topic, question, user_answer):
    prompt = f"""
You are an AI technical interviewer.

Learner profile:
- Target role: {role}
- Level: {level}
- Topic: {topic}

Question:
{question}

Learner answer:
{user_answer}

Evaluate the answer.

Return:
1. Score out of 10
2. What is correct
3. What is missing
4. Improved answer
5. Follow-up question
"""

    response = model.generate_content(prompt)
    return response.text