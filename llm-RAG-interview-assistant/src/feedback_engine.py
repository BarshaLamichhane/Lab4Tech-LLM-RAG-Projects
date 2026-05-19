import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))


def diagnose_skill_gaps(
    technical_level: str,
    career_goal: str,
    existing_skills: str,
    learning_goal: str,
    diagnostic_questions: str,
    learner_answers: str,
    topic: str = ""
) -> str:
    prompt = f"""
You are an adaptive learning analyst.

Analyze the learner's answers and identify real skill gaps.

Learner profile:
- Technical level: {technical_level}
- Career goal: {career_goal}
- Existing skills: {existing_skills}
- Learning goal: {learning_goal}
- Topic selected by learner: {topic if topic else "No topic selected"}

Diagnostic questions:
{diagnostic_questions}

Learner answers:
{learner_answers}

Return:

## 1. Strengths Detected
## 2. Weaknesses / Skill Gaps Detected
## 3. Recommended Focus Topic
Recommend the most important topic to study next.
## 4. Suggested Learning Path
Give a step-by-step learning path.
## 5. Updated Learner Profile
Write the updated learner profile clearly.
"""

    response = model.generate_content(prompt)
    return response.text


def evaluate_answer(
    technical_level: str,
    career_goal: str,
    learning_goal: str,
    question: str,
    learner_answer: str,
    topic: str = ""
) -> str:
    prompt = f"""
You are an AI technical interviewer and adaptive learning coach.

Learner profile:
- Technical level: {technical_level}
- Career goal: {career_goal}
- Learning goal: {learning_goal}
- Topic: {topic if topic else "Not specified"}

Interview question:
{question}

Learner answer:
{learner_answer}

Evaluate the learner's answer.

Return:

## 1. Score
Give a score out of 10.

## 2. Strengths
Mention what the learner answered correctly.

## 3. Missing Concepts
Identify missing technical points.

## 4. Improved Answer
Provide a better version of the answer.

## 5. Follow-up Question
Ask one adaptive follow-up question.

## 6. Profile Adjustment Suggestion
Suggest how the learner profile should be updated.
"""

    response = model.generate_content(prompt)
    return response.text