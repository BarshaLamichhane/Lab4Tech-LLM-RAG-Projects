import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))


def generate_diagnostic_questions(
    technical_level: str,
    career_goal: str,
    existing_skills: str,
    learning_goal: str,
    topic: str = ""
) -> str:
    prompt = f"""
You are an adaptive AI learning coach.

Learner profile:
- Technical level: {technical_level}
- Career goal: {career_goal}
- Existing skills: {existing_skills}
- Learning goal: {learning_goal}
- Topic selected by learner: {topic if topic else "No topic selected. Recommend relevant diagnostic areas automatically."}

Create 5 diagnostic questions to identify the learner's real skill gaps.

If no topic is provided, choose questions based on the learner's career goal and existing skills.

Return only a numbered list of questions.
"""

    response = model.generate_content(prompt)
    return response.text


def generate_learning_content(
    technical_level: str,
    career_goal: str,
    existing_skills: str,
    learning_goal: str,
    weaknesses: str = "",
    topic: str = ""
) -> str:
    prompt = f"""
You are an adaptive AI learning coach.

Learner profile:
- Technical level: {technical_level}
- Career goal: {career_goal}
- Existing skills: {existing_skills}
- Learning goal: {learning_goal}
- Known or detected weaknesses: {weaknesses if weaknesses else "Not provided"}
- Topic selected by learner: {topic if topic else "No topic selected. Determine the most relevant learning topic automatically."}

Analyze the learner profile and decide what the learner should study next.

Then generate customized educational content.

Return:

## 1. Recommended Focus Topic
Choose the most relevant topic to study now and explain why.

## 2. Personalized Technical Summary
Explain the topic according to the learner's level.

## 3. Key Concepts
List the most important concepts.

## 4. Personalized Interview Scenario
Create a realistic interview scenario for the learner's career goal.

## 5. Interview Questions
Generate 5 interview questions adapted to the learner's level.

##4. Model Answers
Provide short model answers for each question.

## 5. Recommended Next Steps
Suggest what the learner should study next.

## 6. Learning Support
Suggest topics/resources to study next.

## 7. Progression Advice
Give a short improvement plan.
"""

    response = model.generate_content(prompt)
    return response.text