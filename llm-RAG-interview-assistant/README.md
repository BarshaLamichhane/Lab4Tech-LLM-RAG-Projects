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

```bash
touch llm-RAG-interview-assistant/src/__init__.py
```

This allows Python to recognize src as a package and fixes import-related issues.
---

