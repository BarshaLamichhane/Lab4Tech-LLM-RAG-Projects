# 🎓 Adaptive AI Learning Coach (MVP)

An AI-powered adaptive learning and interview preparation assistant built using Streamlit and Gemini API.

This project generates:
- Personalized technical summaries
- Adaptive interview questions
- Model answers
- AI feedback on learner responses
- Learning recommendations

The goal is to personalize technical learning according to:
- learner level
- target role
- topic
- career goals

---

# 🚀 Features

✅ Personalized technical summaries  
✅ AI-generated interview questions  
✅ Adaptive learning support  
✅ AI answer evaluation and feedback  
✅ Streamlit interactive UI  
✅ Gemini API integration  

---

# 🧠 Example Use Cases

- AI Engineer interview preparation
- Machine Learning learning assistant
- Personalized technical coaching
- Adaptive educational content generation
- Technical skill-gap analysis

---

# 🛠️ Tech Stack

- Python
- Streamlit
- Google Gemini API
- Generative AI
- Prompt Engineering

---

# 📁 Project Structure

```text
llm-RAG-interview-assistant/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
│
├── src/
│   └── content_generator.py
│
└── prompts/

# Installation

# Installation

## 1. Clone repository

```bash
git clone https://github.com/BarshaLamichhane/Lab4Tech-llm-rag-projects.git
cd lab4tech-cv-rag-assistant
```
# Future Improvements

Planned Features
RAG integration using FAISS
Knowledge base retrieval
Voice interview mode
Conversation memory
Skill-gap analytics
Adaptive difficulty progression
Learning roadmap generation
PDF export
User progress tracking

# Example Future Enhancement

User Profile
↓
Skill Analysis
↓
RAG Knowledge Retrieval
↓
LLM Prompt Generation
↓
Adaptive Content Generation
↓
Interview Feedback
↓
Learning Recommendation

## 2. Create virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python -m venv venv
source venv/bin/activate
```

---

# 📦 Install Dependencies

```bash
pip install -r llm-RAG-interview-assistant/requirements.txt
```

---

# Run Application

```bash
streamlit run llm-RAG-interview-assistant/app.py
```
## Common Issue

```md
## Fix for `ModuleNotFoundError`

If you encounter an error such as:

```bash
ModuleNotFoundError: No module named 'src.content_generator'
```

```md
Example:

project/
│
├── src/
│   ├── __init__.py
│   ├── content_generator.py
│   └── ...

create an empty __init__.py file inside the src/ directory:
```

```bash
touch llm-RAG-interview-assistant/src/__init__.py
```

This allows Python to recognize src as a package and fixes import-related issues.
---
Before pushing to git don't forget to check with this command to know whether commting account is same as your github account or not.

```bash
git log --format="%an <%ae>"
```
if found different do this:

```bash
git filter-branch -f --env-filter '

OLD_EMAIL="barshalamichhane@Barshas-MacBook-Air.local"
CORRECT_NAME="BarshaLamichhane"
CORRECT_EMAIL="barshalamichhane.bl@gmail.com"

if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi

if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags
```
